from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    SUSPICIOUS = "SUSPICIOUS"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    REJECTED = "REJECTED"


class AddressComponents(BaseModel):
    street_address: Optional[str] = Field(default=None, description="Street name, unit, building")
    city: str = Field(..., description="City or municipality")
    region_state: Optional[str] = Field(default=None, description="State, province, or region")
    country: str = Field(..., description="Country name or ISO code")
    postal_code: Optional[str] = Field(default=None, description="Postal/PIN/ZIP code")


class BusinessVerificationRequest(BaseModel):
    name: str = Field(..., min_length=2, description="Claimed business name to verify")
    official_url: Optional[str] = Field(default=None, description="Claimed website or domain")
    address: Optional[AddressComponents] = Field(default=None, description="Structured claimed address")
    raw_address: Optional[str] = Field(default=None, description="Unparsed free-text address")
    registration_id: Optional[str] = Field(default=None, description="Optional CIN, TIN, VAT, or local registry number")


class EvidenceRecord(BaseModel):
    source_url: str
    source_title: str
    snippet: str
    relevance_notes: str


class BusinessVerificationResponse(BaseModel):
    query: BusinessVerificationRequest
    status: VerificationStatus
    is_valid: bool
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    matched_legal_name: Optional[str] = None
    matched_address: Optional[str] = None
    matched_domain: Optional[str] = None
    risk_signals: List[str] = Field(default_factory=list, description="Flags like domain mismatch, unregistered entity, etc.")
    evidence: List[EvidenceRecord] = Field(default_factory=list)
    verification_summary: str = Field(..., description="Executive summary justifying the verdict")