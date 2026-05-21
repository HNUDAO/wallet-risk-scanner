import json
from pathlib import Path

from scanner.config import KNOWN_CONTRACTS_DIR


class TornadoCashData:
    def __init__(self):
        self._pools: dict[str, str] | None = None
        self._pool_addresses: set[str] | None = None

    def load_pools(self) -> dict[str, str]:
        if self._pools is not None:
            return self._pools

        filepath = KNOWN_CONTRACTS_DIR / "tornado_cash.json"
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._pools = {}
            for chain_pools in data.values():
                if isinstance(chain_pools, dict):
                    self._pools.update(chain_pools)
        else:
            self._pools = {}

        return self._pools

    def get_pool_addresses(self) -> set[str]:
        if self._pool_addresses is not None:
            return self._pool_addresses

        pools = self.load_pools()
        self._pool_addresses = {addr.lower() for addr in pools.values()}
        return self._pool_addresses

    def is_tornado_address(self, address: str) -> bool:
        return address.lower() in self.get_pool_addresses()
