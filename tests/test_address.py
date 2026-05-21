from scanner.utils.address import is_valid_eth_address, normalize_address, shorten_address


def test_valid_address():
    assert is_valid_eth_address("0x1234567890abcdef1234567890abcdef12345678") is True
    assert is_valid_eth_address("0xABCDEF1234567890ABCDEF1234567890ABCDEF12") is True


def test_invalid_address():
    assert is_valid_eth_address("0x123") is False
    assert is_valid_eth_address("1234567890abcdef1234567890abcdef12345678") is False
    assert is_valid_eth_address("0xGGGG567890abcdef1234567890abcdef12345678") is False
    assert is_valid_eth_address("") is False


def test_normalize():
    assert normalize_address("0xABCDEF1234567890ABCDEF1234567890ABCDEF12") == "0xabcdef1234567890abcdef1234567890abcdef12"
    assert normalize_address("  0xABCDEF1234567890ABCDEF1234567890ABCDEF12  ") == "0xabcdef1234567890abcdef1234567890abcdef12"


def test_shorten():
    addr = "0x1234567890abcdef1234567890abcdef12345678"
    result = shorten_address(addr)
    assert result.startswith("0x1234")
    assert "..." in result
    assert result.endswith("345678")

    result6 = shorten_address(addr, 4)
    assert result6.startswith("0x1234")
    assert result6.endswith("5678")
