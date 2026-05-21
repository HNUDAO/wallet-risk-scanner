from __future__ import annotations

from scanner.apis.goplus import GoPlusClient
from scanner.apis.etherscan import EtherscanClient
from scanner.config import CHAINS
from scanner.models import ContractRisk, RiskLevel


class ContractRiskEngine:
    def __init__(self, chain: str = "ethereum", etherscan: EtherscanClient | None = None):
        self.chain = chain
        self.chain_id = CHAINS.get(chain, CHAINS["ethereum"])["chain_id"]
        self.goplus = GoPlusClient()
        self.etherscan = etherscan or EtherscanClient(chain)

    def check(self, address: str) -> list[ContractRisk]:
        address = address.lower()
        risks: list[ContractRisk] = []

        address_risks = self.goplus.check_address_security(address, self.chain_id)
        risks.extend(address_risks)

        contracts = self.etherscan.get_interacted_contracts(address)
        max_contracts_to_check = min(len(contracts), 10)

        for contract in contracts[:max_contracts_to_check]:
            contract_risks = self.goplus.check_contract(contract, self.chain_id)
            risks.extend(contract_risks)

            etherscan_risks = self.etherscan.get_contract_risks(contract)
            risks.extend(etherscan_risks)

        seen: set[tuple[str, str]] = set()
        unique_risks: list[ContractRisk] = []
        for risk in risks:
            key = (risk.address.lower(), risk.risk_type)
            if key not in seen:
                seen.add(key)
                unique_risks.append(risk)

        return unique_risks
