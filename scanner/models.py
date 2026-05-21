from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class BlacklistHit(BaseModel):
    source: str
    hit_type: str
    risk_level: RiskLevel
    description: str = ""


class ContractRisk(BaseModel):
    address: str
    risk_type: str
    risk_level: RiskLevel
    source: str = ""
    detail: str = ""


class FundSourceRisk(BaseModel):
    source_address: str
    risk_type: str
    risk_level: RiskLevel
    amount: str = ""
    tx_hash: str = ""


class RiskScore(BaseModel):
    score: int = Field(ge=0, le=100)
    level: RiskLevel
    blacklist_score: int = 0
    contract_score: int = 0
    fund_source_score: int = 0
    breakdown: str = ""


class AddressRiskReport(BaseModel):
    address: str
    chain: str
    chain_id: int
    blacklist_hits: list[BlacklistHit] = []
    contract_risks: list[ContractRisk] = []
    fund_source_risks: list[FundSourceRisk] = []
    risk_score: Optional[RiskScore] = None
