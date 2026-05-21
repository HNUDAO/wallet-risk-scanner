from __future__ import annotations

import time

import requests

from scanner.config import API_RATE_LIMIT_DELAY, CHAINABUSE_API_KEY
from scanner.models import BlacklistHit, RiskLevel
from scanner.utils.log import debug


class ChainAbuseClient:
    BASE_URL = "https://api.chainabuse.com/v1"

    def __init__(self):
        self.api_key = CHAINABUSE_API_KEY
        self._last_request_time = 0.0

    def _rate_limit(self) -> None:
        elapsed = time.time() - self._last_request_time
        if elapsed < API_RATE_LIMIT_DELAY:
            time.sleep(API_RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = time.time()

    def check_address(self, address: str) -> list[BlacklistHit]:
        if not self.api_key:
            debug("[ChainAbuse] Skipped: API key not configured")
            return []

        debug(f"[ChainAbuse] Checking address {address[:10]}... apikey=***{self.api_key[-4:]}")
        self._rate_limit()
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            resp = requests.get(
                f"{self.BASE_URL}/reports",
                params={"address": address},
                headers=headers,
                timeout=30,
            )
            debug(f"[ChainAbuse] Response: status={resp.status_code}")
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            debug(f"[ChainAbuse] Request failed: {e}")
            return []

        hits: list[BlacklistHit] = []
        reports = data if isinstance(data, list) else data.get("data", [])

        for report in reports[:10]:
            category = report.get("category", "unknown")
            hits.append(BlacklistHit(
                source="ChainAbuse",
                hit_type=category.replace("_", " ").title(),
                risk_level=RiskLevel.HIGH,
                description=f"ChainAbuse report: {category}",
            ))

        debug(f"[ChainAbuse] Found {len(hits)} reports for {address[:10]}...")
        return hits
