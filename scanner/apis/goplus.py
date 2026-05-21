from __future__ import annotations

from scanner.models import ContractRisk, RiskLevel
from scanner.utils.log import debug


class GoPlusClient:
    def __init__(self):
        pass

    def check_address_security(self, address: str, chain_id: int = 1) -> list[ContractRisk]:
        from goplus.address import Address

        debug(f"[GoPlus/SDK] Address.security address={address} chain_id={chain_id}")
        risks: list[ContractRisk] = []

        try:
            res = Address().address_security(address=address, chain_id=str(chain_id))
            if res.code != 1:
                debug(f"[GoPlus/SDK] Address result code={res.code}")
                return risks
        except Exception as e:
            debug(f"[GoPlus/SDK] Address call failed: {e}")
            return risks

        data = res.result
        if not data:
            return risks

        risk_fields = {
            "is_malicious_address": ("Malicious Address", RiskLevel.HIGH),
            "is_phishing": ("Phishing", RiskLevel.HIGH),
            "is_stealing_attack": ("Stealing Attack", RiskLevel.CRITICAL),
            "is_blacklist": ("Blacklisted", RiskLevel.CRITICAL),
        }

        for field, (risk_type, risk_level) in risk_fields.items():
            val = getattr(data, field, "0")
            if str(val) == "1":
                risks.append(ContractRisk(
                    address=address,
                    risk_type=risk_type,
                    risk_level=risk_level,
                    source="GoPlus",
                    detail=f"GoPlus flagged: {field}",
                ))

        debug(f"[GoPlus/SDK] Address found {len(risks)} risks")
        return risks

    def check_token_security(self, token: str, chain_id: int = 1) -> list[ContractRisk]:
        from goplus.token import Token

        debug(f"[GoPlus/SDK] Token.security address={token} chain_id={chain_id}")
        risks: list[ContractRisk] = []

        try:
            res = Token().token_security(chain_id=str(chain_id), addresses=[token])
            if res.code != 1:
                debug(f"[GoPlus/SDK] Token result code={res.code}")
                return risks
        except Exception as e:
            debug(f"[GoPlus/SDK] Token call failed: {e}")
            return risks

        data = res.result
        if not data:
            return risks

        token_info = getattr(data, token.lower(), data) if hasattr(data, token.lower()) else data
        if not token_info:
            return risks

        risk_mappings = {
            "is_honeypot": ("Honeypot Token", RiskLevel.CRITICAL),
            "is_open_source": (None, None),
            "is_mintable": ("Mintable Token", RiskLevel.MEDIUM),
            "can_take_ownership": ("Ownership Takeover", RiskLevel.HIGH),
            "owner_change_balance": ("Owner Can Change Balance", RiskLevel.HIGH),
            "hidden_owner": ("Hidden Owner", RiskLevel.HIGH),
            "selfdestruct": ("Self-Destruct", RiskLevel.CRITICAL),
            "is_blacklisted": ("Blacklisted Token", RiskLevel.HIGH),
            "is_whitelisted": ("Whitelisted Token", RiskLevel.MEDIUM),
            "is_airdrop_scam": ("Airdrop Scam", RiskLevel.HIGH),
            "cannot_sell_all": ("Cannot Sell All", RiskLevel.CRITICAL),
            "slippage_modifiable": ("Slippage Modifiable", RiskLevel.MEDIUM),
            "trading_cooldown": ("Trading Cooldown", RiskLevel.MEDIUM),
        }

        for field, (risk_type, risk_level) in risk_mappings.items():
            if risk_type is None:
                continue
            val = getattr(token_info, field, "0")
            val_str = str(val) if val else "0"
            if val_str == "1" or (field == "is_open_source" and val_str == "0"):
                if field == "is_open_source" and val_str == "0":
                    risks.append(ContractRisk(
                        address=token,
                        risk_type="Unverified Token Contract",
                        risk_level=RiskLevel.MEDIUM,
                        source="GoPlus",
                        detail="Token contract source code is not verified",
                    ))
                else:
                    risks.append(ContractRisk(
                        address=token,
                        risk_type=risk_type,
                        risk_level=risk_level,
                        source="GoPlus",
                        detail=f"GoPlus flagged: {field}",
                    ))

        debug(f"[GoPlus/SDK] Token found {len(risks)} risks")
        return risks

    def check_rugpull_security(self, address: str, chain_id: int = 1) -> list[ContractRisk]:
        from goplus.rug_pull import RugPull

        debug(f"[GoPlus/SDK] RugPull.security address={address} chain_id={chain_id}")
        risks: list[ContractRisk] = []

        try:
            res = RugPull().rug_pull_security(chain_id=str(chain_id), address=address)
            if res.code != 1:
                debug(f"[GoPlus/SDK] RugPull result code={res.code}")
                return risks
        except Exception as e:
            debug(f"[GoPlus/SDK] RugPull call failed: {e}")
            return risks

        data = res.result
        if not data:
            return risks

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    risk_type = value.get("risk", "").strip()
                    if risk_type and risk_type != "safe":
                        risks.append(ContractRisk(
                            address=address,
                            risk_type=f"Rug Pull Risk: {risk_type}",
                            risk_level=RiskLevel.HIGH,
                            source="GoPlus RugPull",
                            detail=f"GoPlus rugpull detection: {key}={risk_type}",
                        ))
        elif hasattr(data, "__dict__"):
            for key, value in data.__dict__.items():
                if isinstance(value, (dict,)):
                    risk_type = value.get("risk", "").strip()
                    if risk_type and risk_type != "safe":
                        risks.append(ContractRisk(
                            address=address,
                            risk_type=f"Rug Pull Risk: {risk_type}",
                            risk_level=RiskLevel.HIGH,
                            source="GoPlus RugPull",
                            detail=f"GoPlus rugpull detection: {key}={risk_type}",
                        ))

        debug(f"[GoPlus/SDK] RugPull found {len(risks)} risks")
        return risks

    def check_contract(self, contract: str, chain_id: int = 1) -> list[ContractRisk]:
        risks: list[ContractRisk] = []

        token_risks = self.check_token_security(contract, chain_id)
        risks.extend(token_risks)

        rugpull_risks = self.check_rugpull_security(contract, chain_id)
        risks.extend(rugpull_risks)

        return risks
