import json
from pathlib import Path

from scanner.config import KNOWN_CONTRACTS_DIR
from scanner.models import BlacklistHit, RiskLevel
from scanner.data.blacklist_loader import BlacklistLoader
from scanner.data.tornado import TornadoCashData


class BlacklistEngine:
    def __init__(self):
        self.loader = BlacklistLoader()
        self.tornado = TornadoCashData()
        self._hacked_addresses: set[str] | None = None

    def _load_hacked_addresses(self) -> set[str]:
        if self._hacked_addresses is not None:
            return self._hacked_addresses

        filepath = KNOWN_CONTRACTS_DIR / "hacked_contracts.json"
        self._hacked_addresses = set()
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                addr = item.get("address", "")
                if addr:
                    self._hacked_addresses.add(addr.lower())
        return self._hacked_addresses

    def check(self, address: str) -> list[BlacklistHit]:
        address = address.lower()
        hits: list[BlacklistHit] = []

        ofac_addresses = self.loader.load_ofac_addresses()
        if address in ofac_addresses:
            hits.append(BlacklistHit(
                source="OFAC SDN",
                hit_type="Sanctioned",
                risk_level=RiskLevel.CRITICAL,
                description="Address is on the OFAC Specially Designated Nationals list",
            ))

        scamsniffer_addresses = self.loader.load_scamsniffer_addresses()
        if address in scamsniffer_addresses:
            hits.append(BlacklistHit(
                source="ScamSniffer",
                hit_type="Phishing",
                risk_level=RiskLevel.HIGH,
                description="Address flagged as phishing/scam in ScamSniffer database",
            ))

        if self.tornado.is_tornado_address(address):
            hits.append(BlacklistHit(
                source="Tornado Cash",
                hit_type="Mixer",
                risk_level=RiskLevel.HIGH,
                description="Address is a Tornado Cash pool contract",
            ))

        hacked_addresses = self._load_hacked_addresses()
        if address in hacked_addresses:
            hits.append(BlacklistHit(
                source="Known Hacks",
                hit_type="Hacked Contract",
                risk_level=RiskLevel.CRITICAL,
                description="Address is associated with a known hack/exploit",
            ))

        return hits
