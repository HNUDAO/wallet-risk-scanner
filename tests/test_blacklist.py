from scanner.data.tornado import TornadoCashData


def test_tornado_data_load():
    data = TornadoCashData()
    pools = data.load_pools()
    assert isinstance(pools, dict)
    assert len(pools) > 0


def test_tornado_address_check():
    data = TornadoCashData()
    assert data.is_tornado_address("0x12D66f87A04A9E220743712cE6d9bB1B5616B1Fc") is True
    assert data.is_tornado_address("0x12d66f87a04a9e220743712ce6d9bb1b5616b1fc") is True
    assert data.is_tornado_address("0x0000000000000000000000000000000000000000") is False
