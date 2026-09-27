from typing import TypedDict, List, Dict, Any, Optional
from app.schemas.corporate_entity import VerificationStatus

class AgentState(TypedDict):
    # --- Input data passed from the API request ---
    company_name: str
    country_code: str
    registration_number: Optional[str]
    address: Optional[str]
    website_url: Optional[str]

    # --- Sensory / Investigation Data ---
    search_results: List[Dict[str, Any]]
    website_markdown: Optional[str]
    iteration_count: int

    # --- Reasoning, Risk Flags & Conclusions ---
    identified_legal_name: Optional[str]
    identified_reg_id: Optional[str]
    findings: List[str]
    risk_flags: List[str]
    confidence_score: float
    status: VerificationStatus