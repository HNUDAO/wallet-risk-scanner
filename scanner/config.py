import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BLACKLIST_DIR = DATA_DIR / "blacklists"
KNOWN_CONTRACTS_DIR = DATA_DIR / "known_contracts"

BLACKLIST_DIR.mkdir(parents=True, exist_ok=True)
KNOWN_CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "")
BSCSCAN_API_KEY = os.getenv("BSCSCAN_API_KEY", "")
CHAINABUSE_API_KEY = os.getenv("CHAINABUSE_API_KEY", "")

ETHERSCAN_V2_API_URL = "https://api.etherscan.io/v2/api"

CHAINS = {
    "ethereum": {
        "chain_id": 1,
        "name": "Ethereum",
        "explorer_url": "https://etherscan.io",
        "v2_free": True,
        "fallback_api": None,
        "fallback_api_key_env": None,
    },
    "bsc": {
        "chain_id": 56,
        "name": "BSC",
        "explorer_url": "https://bscscan.com",
        "v2_free": False,
        "fallback_api": "https://api.bscscan.com/api",
        "fallback_api_key_env": "BSCSCAN_API_KEY",
    },
    "polygon": {
        "chain_id": 137,
        "name": "Polygon",
        "explorer_url": "https://polygonscan.com",
        "v2_free": True,
        "fallback_api": None,
        "fallback_api_key_env": None,
    },
    "arbitrum": {
        "chain_id": 42161,
        "name": "Arbitrum",
        "explorer_url": "https://arbiscan.io",
        "v2_free": True,
        "fallback_api": None,
        "fallback_api_key_env": None,
    },
    "optimism": {
        "chain_id": 10,
        "name": "Optimism",
        "explorer_url": "https://optimistic.etherscan.io",
        "v2_free": False,
        "fallback_api": "https://api-optimistic.etherscan.io/api",
        "fallback_api_key_env": "ETHERSCAN_API_KEY",
    },
    "base": {
        "chain_id": 8453,
        "name": "Base",
        "explorer_url": "https://basescan.org",
        "v2_free": False,
        "fallback_api": "https://api.basescan.org/api",
        "fallback_api_key_env": "ETHERSCAN_API_KEY",
    },
}

DEFAULT_CHAIN = "ethereum"

SCAMSNIFFER_ADDRESS_URL = "https://raw.githubusercontent.com/scamsniffer/scam-database/main/blacklist/address.json"
SCAMSNIFFER_DOMAINS_URL = "https://raw.githubusercontent.com/scamsniffer/scam-database/main/blacklist/domains.json"
OFAC_SDN_URL = "https://www.treasury.gov/ofac/downloads/sdn.csv"

BLACKLIST_CACHE_TTL_SECONDS = 86400

API_RATE_LIMIT_DELAY = 0.25
