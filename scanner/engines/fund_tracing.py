from __future__ import annotations

import json
from pathlib import Path

from scanner.apis.etherscan import EtherscanClient
from scanner.config import KNOWN_CONTRACTS_DIR
from scanner.data.tornado import TornadoCashData
from scanner.models import FundSourceRisk, RiskLevel


class FundTracingEngine:
    def __init__(self, chain: str = "ethereum", etherscan: EtherscanClient | None = None):
        self.chain = chain
        self.etherscan = etherscan or EtherscanClient(chain)
        self.tornado = TornadoCashData()
        self._hacked_addresses: dict[str, str] | None = None

    def _load_hacked_addresses(self) -> dict[str, str]:
        if self._hacked_addresses is not None:
            return self._hacked_addresses

        filepath = KNOWN_CONTRACTS_DIR / "hacked_contracts.json"
        self._hacked_addresses = {}
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                addr = item.get("address", "").lower()
                name = item.get("name", "Unknown Hack")
                if addr:
                    self._hacked_addresses[addr] = name
        return self._hacked_addresses

    def check(self, address: str) -> list[FundSourceRisk]:
        address = address.lower()
        risks: list[FundSourceRisk] = []

        txs = self.etherscan.get_transaction_list(address)
        incoming_txs = [tx for tx in txs if tx.get("to", "").lower() == address]

        mixer_addresses = self.tornado.get_pool_addresses()
        hacked_addresses = self._load_hacked_addresses()

        for tx in incoming_txs:
            from_addr = tx.get("from", "").lower()
            tx_hash = tx.get("hash", "")
            value_wei = int(tx.get("value", "0"))
            value_eth = value_wei / 1e18 if value_wei else 0
            amount_str = f"{value_eth:.4f} ETH" if value_eth > 0 else "N/A"

            if from_addr in mixer_addresses:
                risks.append(FundSourceRisk(
                    source_address=from_addr,
                    risk_type="Mixer (Tornado Cash)",
                    risk_level=RiskLevel.HIGH,
                    amount=amount_str,
                    tx_hash=tx_hash,
                ))

            if from_addr in hacked_addresses:
                hack_name = hacked_addresses[from_addr]
                risks.append(FundSourceRisk(
                    source_address=from_addr,
                    risk_type=f"Stolen Funds ({hack_name})",
                    risk_level=RiskLevel.CRITICAL,
                    amount=amount_str,
                    tx_hash=tx_hash,
                ))

        risks = self._deduplicate(risks)
        return risks

    def _deduplicate(self, risks: list[FundSourceRisk]) -> list[FundSourceRisk]:
        seen: set[str] = set()
        unique: list[FundSourceRisk] = []
        for risk in risks:
            key = f"{risk.source_address}:{risk.risk_type}"
            if key not in seen:
                seen.add(key)
                unique.append(risk)
        return unique
