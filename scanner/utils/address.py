import re


def is_valid_eth_address(address: str) -> bool:
    return bool(re.match(r"^0x[0-9a-fA-F]{40}$", address))


def normalize_address(address: str) -> str:
    return address.lower().strip()


def shorten_address(address: str, chars: int = 6) -> str:
    if not is_valid_eth_address(address):
        return address
    return f"{address[:chars+2]}...{address[-chars:]}"
