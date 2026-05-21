import json
import time
from pathlib import Path

import requests

from scanner.config import (
    BLACKLIST_DIR,
    BLACKLIST_CACHE_TTL_SECONDS,
    SCAMSNIFFER_ADDRESS_URL,
    SCAMSNIFFER_DOMAINS_URL,
)


class BlacklistLoader:
    def __init__(self):
        self._scamsniffer_addresses: set[str] | None = None
        self._scamsniffer_domains: set[str] | None = None
        self._ofac_addresses: set[str] | None = None

    def _is_cache_valid(self, filepath: Path) -> bool:
        if not filepath.exists():
            return False
        mtime = filepath.stat().st_mtime
        return (time.time() - mtime) < BLACKLIST_CACHE_TTL_SECONDS

    def _download(self, url: str, filepath: Path) -> None:
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            filepath.write_bytes(resp.content)
        except requests.RequestException as e:
            if filepath.exists():
                pass
            else:
                raise RuntimeError(f"Failed to download {url}: {e}") from e

    def _load_json_set(self, filepath: Path) -> set[str]:
        if not filepath.exists():
            return set()
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return {str(item).lower() for item in data}
        if isinstance(data, dict):
            result = set()
            for v in data.values():
                if isinstance(v, str):
                    result.add(v.lower())
                elif isinstance(v, list):
                    for item in v:
                        result.add(str(item).lower())
            return result
        return set()

    def load_scamsniffer_addresses(self) -> set[str]:
        if self._scamsniffer_addresses is not None:
            return self._scamsniffer_addresses

        filepath = BLACKLIST_DIR / "scamsniffer_address.json"
        if not self._is_cache_valid(filepath):
            self._download(SCAMSNIFFER_ADDRESS_URL, filepath)

        self._scamsniffer_addresses = self._load_json_set(filepath)
        return self._scamsniffer_addresses

    def load_scamsniffer_domains(self) -> set[str]:
        if self._scamsniffer_domains is not None:
            return self._scamsniffer_domains

        filepath = BLACKLIST_DIR / "scamsniffer_domains.json"
        if not self._is_cache_valid(filepath):
            self._download(SCAMSNIFFER_DOMAINS_URL, filepath)

        self._scamsniffer_domains = self._load_json_set(filepath)
        return self._scamsniffer_domains

    def load_ofac_addresses(self) -> set[str]:
        if self._ofac_addresses is not None:
            return self._ofac_addresses

        filepath = BLACKLIST_DIR / "ofac_addresses.json"
        if not self._is_cache_valid(filepath):
            self._ofac_addresses = self._fetch_ofac_addresses()
            if self._ofac_addresses:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(sorted(self._ofac_addresses), f, indent=2)
            elif filepath.exists():
                self._ofac_addresses = self._load_json_set(filepath)
        else:
            self._ofac_addresses = self._load_json_set(filepath)

        return self._ofac_addresses

    def _fetch_ofac_addresses(self) -> set[str]:
        from scanner.config import OFAC_SDN_URL

        addresses: set[str] = set()
        try:
            resp = requests.get(OFAC_SDN_URL, timeout=30)
            resp.raise_for_status()
            for line in resp.text.splitlines():
                for part in line.split(","):
                    part = part.strip().strip('"').strip("'")
                    if part.startswith("0x") and len(part) == 42:
                        addresses.add(part.lower())
        except requests.RequestException:
            pass
        return addresses

    def update_all(self) -> None:
        self._scamsniffer_addresses = None
        self._scamsniffer_domains = None
        self._ofac_addresses = None

        self.load_scamsniffer_addresses()
        self.load_scamsniffer_domains()
        self.load_ofac_addresses()
