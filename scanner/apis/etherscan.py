from __future__ import annotations

import os
import time
from typing import Any

import requests

from scanner.config import (
    API_RATE_LIMIT_DELAY,
    CHAINS,
    ETHERSCAN_API_KEY,
    ETHERSCAN_V2_API_URL,
)
from scanner.models import ContractRisk, RiskLevel
from scanner.utils.log import debug


class EtherscanClient:
    def __init__(self, chain: str = "ethereum"):
        self.chain = chain
        chain_info = CHAINS.get(chain, CHAINS["ethereum"])
        self.chain_id = chain_info["chain_id"]
        self._chain_info = chain_info
        self._last_request_time = 0.0

        self.api_url, self.api_key = self._resolve_api()

    def _resolve_api(self) -> tuple[str, str]:
        if self._chain_info.get("v2_free", False):
            debug(f"[Etherscan] Chain {self.chain} (id={self.chain_id}) uses V2 API (free tier)")
            return ETHERSCAN_V2_API_URL, ETHERSCAN_API_KEY

        fallback_url = self._chain_info.get("fallback_api")
        fallback_key_env = self._chain_info.get("fallback_api_key_env")

        if fallback_url and fallback_key_env:
            fallback_key = os.getenv(fallback_key_env, "")
            if fallback_key:
                debug(f"[Etherscan] Chain {self.chain} (id={self.chain_id}) uses fallback API: {fallback_url}")
                return fallback_url, fallback_key

        debug(f"[Etherscan] Chain {self.chain} (id={self.chain_id}) falls back to V2 API (may require paid plan)")
        return ETHERSCAN_V2_API_URL, ETHERSCAN_API_KEY

    def _rate_limit(self) -> None:
        elapsed = time.time() - self._last_request_time
        if elapsed < API_RATE_LIMIT_DELAY:
            time.sleep(API_RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = time.time()

    def _get(self, params: dict[str, Any]) -> dict[str, Any]:
        self._rate_limit()
        has_key = bool(self.api_key)
        if has_key:
            params["apikey"] = self.api_key

        is_v2 = "v2" in self.api_url
        if is_v2:
            params["chainid"] = self.chain_id

        api_label = "V2" if is_v2 else "V1"
        debug(f"[Etherscan/{api_label} chainid={self.chain_id}] GET module={params.get('module')} action={params.get('action')} apikey={'***' + self.api_key[-4:] if has_key else 'NOT SET'}")
        try:
            resp = requests.get(self.api_url, params=params, timeout=30)
            debug(f"[Etherscan/{api_label} chainid={self.chain_id}] Response: status={resp.status_code}")
            resp.raise_for_status()
            data = resp.json()
            debug(f"[Etherscan/{api_label} chainid={self.chain_id}] Result: status={data.get('status')} message={data.get('message', '')}")

            if is_v2 and data.get("status") == "0":
                result_val = data.get("result", "")
                result_str = str(result_val) if not isinstance(result_val, str) else result_val
                if "deprecated" in result_str.lower():
                    debug(f"[Etherscan/V2 chainid={self.chain_id}] V2 endpoint returned deprecation, trying fallback...")
                    fallback_result = self._try_fallback(params)
                    if fallback_result:
                        return fallback_result

            return data
        except requests.RequestException as e:
            debug(f"[Etherscan/{api_label} chainid={self.chain_id}] Request failed: {e}")
            return {}

    def _try_fallback(self, params: dict[str, Any]) -> dict[str, Any] | None:
        fallback_url = self._chain_info.get("fallback_api")
        fallback_key_env = self._chain_info.get("fallback_api_key_env")
        if not fallback_url:
            return None

        fallback_key = os.getenv(fallback_key_env, "") if fallback_key_env else ""
        fallback_params = {k: v for k, v in params.items() if k not in ("chainid",)}
        if fallback_key:
            fallback_params["apikey"] = fallback_key

        debug(f"[Etherscan/Fallback] GET {fallback_url} module={fallback_params.get('module')}")
        try:
            resp = requests.get(fallback_url, params=fallback_params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            debug(f"[Etherscan/Fallback] Result: status={data.get('status')} message={data.get('message', '')}")
            return data
        except requests.RequestException as e:
            debug(f"[Etherscan/Fallback] Request failed: {e}")
            return None

    def get_transaction_list(self, address: str, start_block: int = 0, end_block: int = 99999999) -> list[dict]:
        params = {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": start_block,
            "endblock": end_block,
            "sort": "desc",
            "page": 1,
            "offset": 100,
        }
        result = self._get(params)
        if result.get("status") == "1":
            txs = result.get("result", [])
            debug(f"[Etherscan] Got {len(txs)} transactions for {address[:10]}...")
            return txs
        return []

    def get_internal_transactions(self, address: str, start_block: int = 0, end_block: int = 99999999) -> list[dict]:
        params = {
            "module": "account",
            "action": "txlistinternal",
            "address": address,
            "startblock": start_block,
            "endblock": end_block,
            "sort": "desc",
            "page": 1,
            "offset": 50,
        }
        result = self._get(params)
        if result.get("status") == "1":
            return result.get("result", [])
        return []

    def get_contract_info(self, contract: str) -> dict[str, Any]:
        params = {
            "module": "contract",
            "action": "getabi",
            "address": contract,
        }
        result = self._get(params)
        info: dict[str, Any] = {"address": contract, "is_verified": False}
        if result.get("status") == "1" and result.get("result") != "Contract source code not verified":
            info["is_verified"] = True
        return info

    def get_contract_risks(self, contract: str) -> list[ContractRisk]:
        info = self.get_contract_info(contract)
        risks: list[ContractRisk] = []

        if not info.get("is_verified", True):
            risks.append(ContractRisk(
                address=contract,
                risk_type="Unverified Contract",
                risk_level=RiskLevel.MEDIUM,
                source="Etherscan",
                detail="Contract source code is not verified on block explorer",
            ))

        return risks

    def get_interacted_contracts(self, address: str) -> list[str]:
        txs = self.get_transaction_list(address)
        contracts: set[str] = set()

        for tx in txs:
            to_addr = tx.get("to", "")
            if to_addr and to_addr.lower() != address.lower():
                contracts.add(to_addr.lower())

        debug(f"[Etherscan] Found {len(contracts)} interacted contracts for {address[:10]}...")
        return list(contracts)
