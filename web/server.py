from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from scanner.config import CHAINS, ETHERSCAN_API_KEY, BSCSCAN_API_KEY, CHAINABUSE_API_KEY, ETHERSCAN_V2_API_URL
from scanner.models import AddressRiskReport
from scanner.utils.address import is_valid_eth_address, normalize_address

STATIC_DIR = Path(__file__).resolve().parent / "static"
PROJECT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_DIR / ".env"

CONFIGURABLE_KEYS = {
    "ETHERSCAN_API_KEY": {
        "label": "Etherscan API Key",
        "description": "用于查询 Ethereum / Polygon / Arbitrum 等链的交易数据",
        "link": "https://etherscan.io/myapikey",
    },
    "BSCSCAN_API_KEY": {
        "label": "BscScan API Key",
        "description": "用于查询 BSC 链的交易数据",
        "link": "https://bscscan.com/myapikey",
    },
    "CHAINABUSE_API_KEY": {
        "label": "ChainAbuse API Key",
        "description": "用于查询 ChainAbuse 黑名单举报数据",
        "link": "https://chainabuse.com",
    },
}

app = FastAPI(title="Wallet Risk Scanner", version="1.0.0")

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class ScanRequest(BaseModel):
    address: str
    chain: str = "ethereum"


class ApiStatus(BaseModel):
    name: str
    key_configured: bool
    key_suffix: str
    working: bool


class CheckApiResponse(BaseModel):
    apis: list[ApiStatus]


class ChainInfo(BaseModel):
    key: str
    name: str
    chain_id: int
    v2_free: bool


class ConfigKeyInfo(BaseModel):
    env_name: str
    label: str
    description: str
    link: str
    configured: bool
    masked_value: str


class ConfigResponse(BaseModel):
    keys: list[ConfigKeyInfo]


class ConfigUpdateRequest(BaseModel):
    keys: dict[str, str]


class ConfigUpdateResponse(BaseModel):
    saved: list[str]
    removed: list[str]


def _mask_value(val: str) -> str:
    if not val:
        return ""
    if len(val) <= 8:
        return "****"
    return val[:4] + "****" + val[-4:]


def _read_env_file() -> dict[str, str]:
    result = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                result[k.strip()] = v.strip()
    return result


def _write_env_file(data: dict[str, str]) -> None:
    lines = []
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                lines.append(line)
                continue
            if "=" in stripped:
                k = stripped.split("=", 1)[0].strip()
                if k in data:
                    lines.append(f"{k}={data.pop(k)}")
                else:
                    lines.append(line)
            else:
                lines.append(line)

    for k, v in data.items():
        lines.append(f"{k}={v}")

    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


@app.get("/")
async def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.post("/api/scan")
async def scan(req: ScanRequest) -> dict:
    if not is_valid_eth_address(req.address):
        raise HTTPException(status_code=400, detail=f"Invalid address: {req.address}")

    if req.chain not in CHAINS:
        raise HTTPException(status_code=400, detail=f"Unsupported chain: {req.chain}")

    address = normalize_address(req.address)
    chain_info = CHAINS[req.chain]

    from scanner.apis.etherscan import EtherscanClient
    from scanner.engines.blacklist import BlacklistEngine
    from scanner.engines.contract_risk import ContractRiskEngine
    from scanner.engines.fund_tracing import FundTracingEngine
    from scanner.engines.risk_scorer import RiskScorer

    blacklist_engine = BlacklistEngine()
    shared_etherscan = EtherscanClient(req.chain)
    contract_engine = ContractRiskEngine(req.chain, etherscan=shared_etherscan)
    fund_engine = FundTracingEngine(req.chain, etherscan=shared_etherscan)
    scorer = RiskScorer()

    blacklist_hits = blacklist_engine.check(address)
    contract_risks = contract_engine.check(address)
    fund_risks = fund_engine.check(address)

    risk_score = scorer.calculate(
        blacklist_hits=blacklist_hits,
        contract_risks=contract_risks,
        fund_source_risks=fund_risks,
    )

    report = AddressRiskReport(
        address=address,
        chain=req.chain,
        chain_id=chain_info["chain_id"],
        blacklist_hits=blacklist_hits,
        contract_risks=contract_risks,
        fund_source_risks=fund_risks,
        risk_score=risk_score,
    )

    return report.model_dump()


@app.get("/api/check-api")
async def check_api() -> CheckApiResponse:
    import asyncio
    import httpx
    from scanner.config import BLACKLIST_DIR, BLACKLIST_CACHE_TTL_SECONDS

    TEST_ADDR = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    TIMEOUT = 8

    async def check_goplus(client: httpx.AsyncClient):
        try:
            resp = await client.get(
                "https://api.gopluslabs.io/api/v1/address_security/" + TEST_ADDR,
                params={"chain_id": "1"},
            )
            data = resp.json()
            ok = data.get("code") == 1
            return ApiStatus(name="GoPlus Security", key_configured=True, key_suffix="-", working=ok)
        except Exception:
            return ApiStatus(name="GoPlus Security", key_configured=True, key_suffix="-", working=False)

    async def check_etherscan(client: httpx.AsyncClient):
        if not ETHERSCAN_API_KEY:
            return ApiStatus(name="Etherscan V2", key_configured=False, key_suffix="-", working=False)
        try:
            resp = await client.get(
                ETHERSCAN_V2_API_URL,
                params={"chainid": 1, "module": "account", "action": "txlist",
                        "address": TEST_ADDR, "page": 1, "offset": 1, "apikey": ETHERSCAN_API_KEY},
            )
            ok = resp.json().get("status") == "1"
            return ApiStatus(name="Etherscan V2", key_configured=True,
                             key_suffix=f"***{ETHERSCAN_API_KEY[-4:]}", working=ok)
        except Exception:
            return ApiStatus(name="Etherscan V2", key_configured=True,
                             key_suffix=f"***{ETHERSCAN_API_KEY[-4:]}", working=False)

    async def check_bscscan(client: httpx.AsyncClient):
        if not BSCSCAN_API_KEY:
            return ApiStatus(name="BscScan (BSC)", key_configured=False, key_suffix="-", working=False)
        try:
            resp = await client.get(
                "https://api.bscscan.com/api",
                params={"module": "account", "action": "txlist",
                        "address": "0x28C6c06298d514Db089934071355E5743bf21d60",
                        "page": 1, "offset": 1, "apikey": BSCSCAN_API_KEY},
            )
            ok = resp.json().get("status") == "1"
            return ApiStatus(name="BscScan (BSC)", key_configured=True,
                             key_suffix=f"***{BSCSCAN_API_KEY[-4:]}", working=ok)
        except Exception:
            return ApiStatus(name="BscScan (BSC)", key_configured=True,
                             key_suffix=f"***{BSCSCAN_API_KEY[-4:]}", working=False)

    async def check_chainabuse(client: httpx.AsyncClient):
        if not CHAINABUSE_API_KEY:
            return ApiStatus(name="ChainAbuse", key_configured=False, key_suffix="-", working=False)
        try:
            resp = await client.get(
                "https://api.chainabuse.com/v1/reports",
                params={"address": TEST_ADDR},
                headers={"Authorization": f"Bearer {CHAINABUSE_API_KEY}"},
            )
            return ApiStatus(name="ChainAbuse", key_configured=True,
                             key_suffix=f"***{CHAINABUSE_API_KEY[-4:]}", working=resp.status_code == 200)
        except Exception:
            return ApiStatus(name="ChainAbuse", key_configured=True,
                             key_suffix=f"***{CHAINABUSE_API_KEY[-4:]}", working=False)

    async def check_scamsniffer():
        import time
        cache_file = BLACKLIST_DIR / "scamsniffer_address.json"
        if cache_file.exists():
            age = time.time() - cache_file.stat().st_mtime
            ok = age < BLACKLIST_CACHE_TTL_SECONDS
        else:
            ok = False
        return ApiStatus(name="ScamSniffer", key_configured=True, key_suffix="-", working=ok)

    async def check_ofac():
        import time
        cache_file = BLACKLIST_DIR / "ofac_addresses.json"
        if cache_file.exists():
            age = time.time() - cache_file.stat().st_mtime
            ok = age < BLACKLIST_CACHE_TTL_SECONDS
        else:
            ok = False
        return ApiStatus(name="OFAC SDN", key_configured=True, key_suffix="-", working=ok)

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        results = await asyncio.gather(
            check_goplus(client),
            check_etherscan(client),
            check_bscscan(client),
            check_chainabuse(client),
            check_scamsniffer(),
            check_ofac(),
        )

    return CheckApiResponse(apis=list(results))


@app.get("/api/chains")
async def get_chains() -> list[ChainInfo]:
    return [
        ChainInfo(key=k, name=v["name"], chain_id=v["chain_id"], v2_free=v.get("v2_free", True))
        for k, v in CHAINS.items()
    ]


@app.get("/api/config")
async def get_config() -> ConfigResponse:
    keys = []
    for env_name, meta in CONFIGURABLE_KEYS.items():
        val = os.getenv(env_name, "")
        keys.append(ConfigKeyInfo(
            env_name=env_name,
            label=meta["label"],
            description=meta["description"],
            link=meta["link"],
            configured=bool(val),
            masked_value=_mask_value(val) if val else "",
        ))
    return ConfigResponse(keys=keys)


@app.post("/api/config")
async def update_config(req: ConfigUpdateRequest) -> ConfigUpdateResponse:
    saved = []
    removed = []

    env_data = _read_env_file()

    for env_name, value in req.keys.items():
        if env_name not in CONFIGURABLE_KEYS:
            raise HTTPException(status_code=400, detail=f"Unknown key: {env_name}")

        cleaned = value.strip() if value else ""
        if cleaned:
            env_data[env_name] = cleaned
            os.environ[env_name] = cleaned
            saved.append(env_name)
        else:
            env_data.pop(env_name, None)
            os.environ.pop(env_name, None)
            removed.append(env_name)

    _write_env_file(env_data)

    import scanner.config as cfg
    cfg.ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "")
    cfg.BSCSCAN_API_KEY = os.getenv("BSCSCAN_API_KEY", "")
    cfg.CHAINABUSE_API_KEY = os.getenv("CHAINABUSE_API_KEY", "")

    return ConfigUpdateResponse(saved=saved, removed=removed)
