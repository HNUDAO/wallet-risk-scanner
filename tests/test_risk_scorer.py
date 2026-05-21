from scanner.engines.risk_scorer import RiskScorer
from scanner.models import BlacklistHit, ContractRisk, FundSourceRisk, RiskLevel


def test_empty_risks():
    scorer = RiskScorer()
    result = scorer.calculate([], [], [])
    assert result.score == 0
    assert result.level == RiskLevel.LOW


def test_ofac_hit():
    scorer = RiskScorer()
    hits = [BlacklistHit(source="OFAC SDN", hit_type="Sanctioned", risk_level=RiskLevel.CRITICAL, description="test")]
    result = scorer.calculate(hits, [], [])
    assert result.score == 40
    assert result.blacklist_score == 40


def test_scamsniffer_hit():
    scorer = RiskScorer()
    hits = [BlacklistHit(source="ScamSniffer", hit_type="Phishing", risk_level=RiskLevel.HIGH, description="test")]
    result = scorer.calculate(hits, [], [])
    assert result.score == 30
    assert result.blacklist_score == 30


def test_tornado_hit():
    scorer = RiskScorer()
    hits = [BlacklistHit(source="Tornado Cash", hit_type="Mixer", risk_level=RiskLevel.HIGH, description="test")]
    result = scorer.calculate(hits, [], [])
    assert result.score == 20
    assert result.blacklist_score == 20


def test_honeypot_contract():
    scorer = RiskScorer()
    risks = [ContractRisk(address="0x1234", risk_type="Honeypot", risk_level=RiskLevel.CRITICAL, source="GoPlus")]
    result = scorer.calculate([], risks, [])
    assert result.score == 15
    assert result.contract_score == 15


def test_stolen_funds():
    scorer = RiskScorer()
    risks = [FundSourceRisk(source_address="0x5678", risk_type="Stolen Funds", risk_level=RiskLevel.CRITICAL)]
    result = scorer.calculate([], [], risks)
    assert result.score == 25
    assert result.fund_source_score == 25


def test_combined_risks():
    scorer = RiskScorer()
    hits = [BlacklistHit(source="OFAC SDN", hit_type="Sanctioned", risk_level=RiskLevel.CRITICAL, description="test")]
    contracts = [ContractRisk(address="0x1234", risk_type="Honeypot", risk_level=RiskLevel.CRITICAL, source="GoPlus")]
    funds = [FundSourceRisk(source_address="0x5678", risk_type="Stolen Funds", risk_level=RiskLevel.CRITICAL)]
    result = scorer.calculate(hits, contracts, funds)
    assert result.score == 80
    assert result.level == RiskLevel.HIGH


def test_max_score_cap():
    scorer = RiskScorer()
    hits = [
        BlacklistHit(source="OFAC SDN", hit_type="Sanctioned", risk_level=RiskLevel.CRITICAL, description="test"),
        BlacklistHit(source="ScamSniffer", hit_type="Phishing", risk_level=RiskLevel.HIGH, description="test"),
    ]
    contracts = [
        ContractRisk(address="0x1", risk_type="Honeypot", risk_level=RiskLevel.CRITICAL, source="GoPlus"),
        ContractRisk(address="0x2", risk_type="Rug Pull", risk_level=RiskLevel.CRITICAL, source="GoPlus"),
        ContractRisk(address="0x3", risk_type="Unverified Contract", risk_level=RiskLevel.MEDIUM, source="Etherscan"),
    ]
    funds = [
        FundSourceRisk(source_address="0x4", risk_type="Stolen Funds", risk_level=RiskLevel.CRITICAL),
        FundSourceRisk(source_address="0x5", risk_type="Mixer (Tornado Cash)", risk_level=RiskLevel.HIGH),
    ]
    result = scorer.calculate(hits, contracts, funds)
    assert result.score <= 100


def test_risk_levels():
    scorer = RiskScorer()

    result_low = scorer.calculate([], [], [])
    assert result_low.level == RiskLevel.LOW

    result_medium = scorer.calculate(
        [BlacklistHit(source="ScamSniffer", hit_type="Phishing", risk_level=RiskLevel.HIGH, description="test")],
        [], []
    )
    assert result_medium.level == RiskLevel.MEDIUM
