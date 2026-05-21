from scanner.models import (
    BlacklistHit,
    ContractRisk,
    FundSourceRisk,
    RiskLevel,
    RiskScore,
)
from scanner.utils.constants import (
    BLACKLIST_SCORE_WEIGHTS,
    CONTRACT_SCORE_WEIGHTS,
    FUND_SOURCE_SCORE_WEIGHTS,
    MAX_SCORE,
    RISK_LEVEL_THRESHOLDS,
)


class RiskScorer:
    def calculate(
        self,
        blacklist_hits: list[BlacklistHit],
        contract_risks: list[ContractRisk],
        fund_source_risks: list[FundSourceRisk],
    ) -> RiskScore:
        blacklist_score = self._calc_blacklist_score(blacklist_hits)
        contract_score = self._calc_contract_score(contract_risks)
        fund_source_score = self._calc_fund_source_score(fund_source_risks)

        total = min(blacklist_score + contract_score + fund_source_score, MAX_SCORE)
        level = self._determine_level(total)

        breakdown_parts = []
        if blacklist_score > 0:
            breakdown_parts.append(f"Blacklist: +{blacklist_score}")
        if contract_score > 0:
            breakdown_parts.append(f"Contracts: +{contract_score}")
        if fund_source_score > 0:
            breakdown_parts.append(f"Fund Source: +{fund_source_score}")
        breakdown = " | ".join(breakdown_parts) if breakdown_parts else "No risks detected"

        return RiskScore(
            score=total,
            level=level,
            blacklist_score=blacklist_score,
            contract_score=contract_score,
            fund_source_score=fund_source_score,
            breakdown=breakdown,
        )

    def _calc_blacklist_score(self, hits: list[BlacklistHit]) -> int:
        score = 0
        for hit in hits:
            source = hit.source.lower()
            if "ofac" in source:
                score += BLACKLIST_SCORE_WEIGHTS["ofac"]
            elif "scamsniffer" in source:
                score += BLACKLIST_SCORE_WEIGHTS["scamsniffer"]
            elif "tornado" in source:
                score += BLACKLIST_SCORE_WEIGHTS["tornado"]
            elif "chainabuse" in source:
                score += BLACKLIST_SCORE_WEIGHTS["chainabuse"]
            elif "hack" in source:
                score += BLACKLIST_SCORE_WEIGHTS["ofac"]
            else:
                score += 15
        return min(score, 40)

    def _calc_contract_score(self, risks: list[ContractRisk]) -> int:
        score = 0
        for risk in risks:
            risk_type = risk.risk_type.lower()
            if "honeypot" in risk_type:
                score += CONTRACT_SCORE_WEIGHTS["honeypot"]
            elif "rug" in risk_type:
                score += CONTRACT_SCORE_WEIGHTS["rug_pull"]
            elif "unverified" in risk_type:
                score += CONTRACT_SCORE_WEIGHTS["unverified"]
            elif "phish" in risk_type:
                score += CONTRACT_SCORE_WEIGHTS["phish"]
            elif "exploit" in risk_type or "steal" in risk_type or "self" in risk_type:
                score += CONTRACT_SCORE_WEIGHTS["exploit"]
            elif "malicious" in risk_type or "blacklist" in risk_type:
                score += CONTRACT_SCORE_WEIGHTS["exploit"]
            elif "owner" in risk_type or "proxy" in risk_type or "hidden" in risk_type:
                score += 8
            elif "mint" in risk_type or "airdrop" in risk_type:
                score += 6
            else:
                score += 3
        return min(score, 30)

    def _calc_fund_source_score(self, risks: list[FundSourceRisk]) -> int:
        score = 0
        for risk in risks:
            risk_type = risk.risk_type.lower()
            if "stolen" in risk_type:
                score += FUND_SOURCE_SCORE_WEIGHTS["stolen_funds"]
            elif "mixer" in risk_type or "tornado" in risk_type:
                score += FUND_SOURCE_SCORE_WEIGHTS["mixer"]
            elif "indirect" in risk_type and "stolen" in risk_type:
                score += FUND_SOURCE_SCORE_WEIGHTS["indirect_stolen"]
            elif "indirect" in risk_type and "mixer" in risk_type:
                score += FUND_SOURCE_SCORE_WEIGHTS["indirect_mixer"]
            else:
                score += 10
        return min(score, 30)

    def _determine_level(self, score: int) -> RiskLevel:
        if score <= RISK_LEVEL_THRESHOLDS["LOW"][1]:
            return RiskLevel.LOW
        elif score <= RISK_LEVEL_THRESHOLDS["MEDIUM"][1]:
            return RiskLevel.MEDIUM
        elif score <= RISK_LEVEL_THRESHOLDS["HIGH"][1]:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
