import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
import re
from typing import Any, Dict

from app.core.config import settings
from app.agent.state import AgentState
from app.agent.tools.search import TavilySearchClient
from app.agent.tools.reader import JinaReaderClient
from app.schemas.corporate_entity import VerificationStatus

# Initialize clients
llm = ChatGroq(
    groq_api_key=settings.GROQ_API_KEY,
    model_name="openai/gpt-oss-120b",
    temperature=0.0
)

tavily_client = TavilySearchClient()
jina_client = JinaReaderClient()


# Structured Output Schema for Groq Reasoning
class VerificationAnalysis(BaseModel):
    identified_legal_name: str = Field(description="Exact legal name found in records")
    identified_reg_id: str = Field(description="Official registration/tax ID like CIN, CRN, or EIN")
    findings: List[str] = Field(description="Key evidence points gathered from verification")
    risk_flags: List[str] = Field(description="Potential risks, e.g. domain mismatch, inactive status, virtual office")
    confidence_score: float = Field(description="Score between 0.0 and 1.0 reflecting certainty")
    status: VerificationStatus = Field(description="Final status: VERIFIED, REJECTED, SUSPICIOUS, or UNVERIFIED")


async def search_node(state: AgentState) -> Dict[str, Any]:
    """Queries corporate registries, GST/trade data, and local presence via Tavily."""
    company_name = state["company_name"]
    country_code = state.get("country_code", "IN")
    reg_id = state.get("registration_number") or ""
    address = state.get("address") or ""

    if reg_id:
        query = f'"{company_name}" "{reg_id}"'
    elif address:
        # Extract 6-digit Indian PIN code if present
        pin_match = re.search(r'\b\d{6}\b', address)
        pincode = pin_match.group(0) if pin_match else ""

        # Extract primary locality keywords (e.g. Kumaraswamy Layout, Kanakapura Road, Bangalore)
        # Avoid door numbers, slashes, and "Opposite/Near" directions that confuse Tavily
        clean_addr = address
        clean_addr = re.sub(r'No\s*[\d\/\-]+', '', clean_addr, flags=re.IGNORECASE)
        clean_addr = re.sub(r'(Opposite|Near|Behind|Beside|Metro Pillar)\s+[^,]+,?', '', clean_addr, flags=re.IGNORECASE)
        clean_addr = " ".join(clean_addr.split())  # normalize whitespace

        query = f'"{company_name}" {clean_addr} {pincode}'.strip()
    else:
        query = f'"{company_name}" {country_code} corporate registry'

    # Request up to 5 results to capture both directory listings and registry pages
    results = await tavily_client.search(query=query, max_results=5)
    serialized_results = [item.model_dump() for item in results]

    return {
        "search_results": serialized_results,
        "iteration_count": state.get("iteration_count", 0) + 1,
    }

async def scrape_node(state: AgentState) -> Dict[str, Any]:
    """Fetches clean markdown from the company's claimed website using Jina, handling failures gracefully."""
    website_url = state.get("website_url")
    if not website_url:
        return {"website_markdown": ""}

    try:
        scraped_doc = await jina_client.fetch_markdown(target_url=website_url, max_chars=4000)
        return {"website_markdown": scraped_doc.markdown_content}
    except Exception as exc:
        error_msg = f"Failed to retrieve claimed website ({website_url}): {str(exc)}"
        existing_flags = list(state.get("risk_flags") or [])
        existing_flags.append(f"Claimed domain could not be scraped or resolved: {str(exc)}")
        return {
            "website_markdown": f"SCRAPE_ERROR: {error_msg}",
            "risk_flags": existing_flags,
        }


async def reasoning_node(state: AgentState) -> Dict[str, Any]:
    """Analyzes search hits and scraped website to evaluate risk and emit structured verdict."""
    structured_llm = llm.with_structured_output(VerificationAnalysis)

    prompt = f"""You are ATHENEUS, an autonomous KYB (Know Your Business) intelligence agent.
Verify the target business against the gathered external evidence.

--- CLAIMED ENTITY ---
Company Name: {state['company_name']}
Country Code: {state['country_code']}
Claimed Address: {state.get('address') or 'None provided'}
Claimed Registration ID: {state.get('registration_number') or 'None provided'}
Claimed Website: {state.get('website_url') or 'None provided (Offline / Local entity)'}

--- EVIDENCE (REGISTRY & WEB SEARCH) ---
{json.dumps(state.get('search_results', []), indent=2)}

--- SCRAPED WEBSITE CONTENT ---
{state.get('website_markdown', 'No website content available')}

--- INSTRUCTIONS ---
1. Cross-reference the claimed company name, address, and country against official registry snippets and trusted 3rd-party commercial directories.
2. Identify the true legal entity name, operating address/city, and official registration number (CIN, GSTIN, Trade License, or equivalent).
3. URL HANDLING:
   - If a website URL is provided, check for domain alignment and legitimacy. If the scraped content indicates a SCRAPE_ERROR or unresolvable domain, treat this as a strong risk flag and evaluate whether it represents domain spoofing or an invalid storefront.
   - If NO website URL is provided, DO NOT penalize the entity or mark it suspicious simply for lacking a website, provided third-party registry or directory evidence confirms its active commercial status.
4. Calculate a strict confidence score (0.0 to 1.0) and assign a final status (MUST be one of: VERIFIED, SUSPICIOUS, REJECTED, UNVERIFIED, INSUFFICIENT_DATA):
   - VERIFIED (score >= 0.70): Clear registry/directory match, confirmed physical/operational presence, active status.
   - SUSPICIOUS (score 0.25 to 0.50): Conflicting addresses, shell company indicators, unverified claims, or spoofing flags.
   - UNVERIFIED / INSUFFICIENT_DATA (score <= 0.20): Little to no public data or registry hits found, or identity/active status cannot be substantiated.
   - REJECTED (score <= 0.10): Dissolved, struck off, or outright fraudulent/phishing entity.
5. Critical Verification Rules:
   - Exact Name Matching: Do NOT substitute the requested entity with a different company (e.g., if querying "Ramesh Electronics", do NOT match "R S Electronics Private Limited" or "Rameshwaram Electronics"). If the exact entity name does not appear, treat it as UNVERIFIED or INSUFFICIENT_DATA with a confidence score <= 0.15.
   - Address Corroboration: For local or sole proprietorship businesses, verify whether the locality, street, or PIN code in the evidence matches the input address. If the evidence points to a completely different address or city, set status to REJECTED or SUSPICIOUS with a low confidence score (< 0.30).
   - Local Physical Grounding: If search snippets show local directory presence (e.g., Justdial, IndiaMART, Google Maps, local GST filings) matching BOTH the business name and locality/PIN, mark status as VERIFIED with confidence score between 0.75 and 0.85, even if there is no central MCA/CIN registration.
   - Empty/Irrelevant Evidence: If the retrieved search results contain no relevant records or mentions of the claimed business, return status INSUFFICIENT_DATA with confidence_score 0.0 and add "No verifiable public or corporate record found" in findings.
"""

    analysis: VerificationAnalysis = await structured_llm.ainvoke(prompt)

    return {
        "identified_legal_name": analysis.identified_legal_name,
        "identified_reg_id": analysis.identified_reg_id,
        "findings": analysis.findings,
        "risk_flags": analysis.risk_flags,
        "confidence_score": analysis.confidence_score,
        "status": analysis.status
    }