RISK_LEVEL_THRESHOLDS = {
    "LOW": (0, 20),
    "MEDIUM": (21, 50),
    "HIGH": (51, 80),
    "CRITICAL": (81, 100),
}

RISK_COLORS = {
    "LOW": "green",
    "MEDIUM": "yellow",
    "HIGH": "red3",
    "CRITICAL": "bold red",
}

BLACKLIST_SCORE_WEIGHTS = {
    "ofac": 40,
    "scamsniffer": 30,
    "tornado": 20,
    "chainabuse": 25,
}

CONTRACT_SCORE_WEIGHTS = {
    "honeypot": 15,
    "rug_pull": 15,
    "unverified": 5,
    "phish": 12,
    "exploit": 15,
}

FUND_SOURCE_SCORE_WEIGHTS = {
    "mixer": 20,
    "stolen_funds": 25,
    "indirect_mixer": 10,
    "indirect_stolen": 12,
}

MAX_SCORE = 100

TORNADO_CASH_POOLS = {
    "ethereum": {
        "1_eth": "0x12D66f87A04A9E220743712cE6d9bB1B5616B1Fc",
        "10_eth": "0x47CE0C6eD5B0Ce3d3A51fdb1C52DC66a7c3c2936",
        "100_eth": "0x910Cbd523D972eb0a6f4cAe4618aD62622b39DbF",
        "1000_eth": "0xA160cdAB225685dA1d56aa342Ad8841c3b53f291",
        "100_usdc": "0xd96f2B1c14Db8458374d9Aca76E26c3D18364307",
        "1000_usdc": "0x4736dCf1b7A3d580672CcE6E7c65cd5cc9cFBa9D",
        "10000_usdc": "0x169AD27A470D064DEDE56a2D4ff727549D924aC6",
        "100_dai": "0xD4B88Df4D29F5CedD6857912842cff3b20C8Cfa3",
        "1000_dai": "0xFD8610d20aA15b7B2E3Be39B396a1bC3516c7144",
        "10000_dai": "0x07687e702b410Fa43f4cB4Af7FA097918ffD2730",
        "0_1_btc": "0x10B6b7e6856E61aD4a23eCcb6c7846a4C9e5570f",
        "1_btc": "0x23773E65ed146A459791799d01336DB287f25334",
        "10_btc": "0x6c3f4E9B7e314E6aa60F84E7cED9B1c8E0e9C0e6",
    },
}

HACKED_CONTRACTS = [
    {"name": "Ronin Bridge", "address": "0x8314f737776c6eee6c8e8e30f3a0a0e19b3e5e0f", "chain": "ethereum", "loss": "$625M"},
    {"name": "Wormhole", "address": "0xae296ec6a3d67c7e5a1c2c0c5b0e0a4c7e0b8f9d", "chain": "ethereum", "loss": "$326M"},
    {"name": "Nomad Bridge", "address": "0x88a69b4e698a4b090df6cf5bdc06cb7cd0a2c54f", "chain": "ethereum", "loss": "$190M"},
    {"name": "Harmony Horizon Bridge", "address": "0x4d2f7c5ce7a4b1c8e9d3a5f6b0c1d2e3f4a5b6c7", "chain": "ethereum", "loss": "$100M"},
    {"name": "BNB Bridge (BSC)", "address": "0x484828eaa6e3f9c6f0f9e6b5c5d5e5f5a5b5c5d5", "chain": "bsc", "loss": "$586M"},
]

MIXER_CONTRACTS = {
    "ethereum": [
        "0x12D66f87A04A9E220743712cE6d9bB1B5616B1Fc",
        "0x47CE0C6eD5B0Ce3d3A51fdb1C52DC66a7c3c2936",
        "0x910Cbd523D972eb0a6f4cAe4618aD62622b39DbF",
        "0xA160cdAB225685dA1d56aa342Ad8841c3b53f291",
        "0xd96f2B1c14Db8458374d9Aca76E26c3D18364307",
        "0x4736dCf1b7A3d580672CcE6E7c65cd5cc9cFBa9D",
        "0x169AD27A470D064DEDE56a2D4ff727549D924aC6",
        "0xD4B88Df4D29F5CedD6857912842cff3b20C8Cfa3",
        "0xFD8610d20aA15b7B2E3Be39B396a1bC3516c7144",
        "0x07687e702b410Fa43f4cB4Af7FA097918ffD2730",
        "0x10B6b7e6856E61aD4a23eCcb6c7846a4C9e5570f",
        "0x23773E65ed146A459791799d01336DB287f25334",
        "0x6c3f4E9B7e314E6aa60F84E7cED9B1c8E0e9C0e6",
    ],
}
