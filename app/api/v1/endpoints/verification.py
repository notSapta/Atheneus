import traceback
from fastapi import APIRouter, HTTPException, status
from app.schemas.corporate_entity import (
    BusinessVerificationRequest,
    BusinessVerificationResponse,
    VerificationStatus,
    EvidenceRecord,
)
from app.agent.graph import agent_graph

router = APIRouter()


@router.post(
    "/verify",
    response_model=BusinessVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Business Entity",
    description="Asynchronously queries corporate registries, scrapes websites (if provided), and assesses fraud risk using Groq reasoning.",
)
async def verify_business_entity(request: BusinessVerificationRequest):
    try:
        # Determine country code from structured address or default fallback
        country_code = "US"
        if request.address and request.address.country:
            country_code = request.address.country.upper()

        # Safely resolve full address string for agent grounding
        raw_addr = getattr(request, "raw_address", None)
        structured_city_country = f"{request.address.city}, {country_code}" if request.address else ""
        resolved_address = raw_addr or structured_city_country

        # Prepare initial state matching AgentState schema
        initial_state = {
            "company_name": request.name,
            "country_code": country_code,
            "address": resolved_address,
            "registration_number": request.registration_id or "",
            "website_url": request.official_url,
            "search_results": [],
            "website_markdown": "",
            "iteration_count": 0,
            "identified_legal_name": None,
            "identified_reg_id": None,
            "findings": [],
            "risk_flags": [],
            "confidence_score": 0.0,
            "status": VerificationStatus.UNVERIFIED,
        }

        # Run the LangGraph workflow
        final_state = await agent_graph.ainvoke(initial_state)

        # Convert search items into EvidenceRecord objects
        evidence_list = []
        for raw in final_state.get("search_results", []):
            evidence_list.append(
                EvidenceRecord(
                    source_url=raw.get("url", ""),
                    source_title=raw.get("title", ""),
                    snippet=raw.get("content", ""),
                    relevance_notes=f"Relevance Score: {raw.get('score', 0.0)}",
                )
            )

        status_result = final_state.get("status", VerificationStatus.UNVERIFIED)
        findings = final_state.get("findings", [])
        summary_text = " ".join(findings) if findings else "Verification completed."

        matched_addr = raw_addr or (request.address.city if request.address else None)

        return BusinessVerificationResponse(
            query=request,
            status=status_result,
            is_valid=(status_result == VerificationStatus.VERIFIED),
            confidence_score=final_state.get("confidence_score", 0.0),
            matched_legal_name=final_state.get("identified_legal_name"),
            matched_address=matched_addr,
            matched_domain=request.official_url,
            risk_signals=final_state.get("risk_flags", []),
            evidence=evidence_list,
            verification_summary=summary_text,
        )

    except Exception as e:
        print("\n" + "=" * 60)
        print("TRACEBACK CAUGHT IN /verify:")
        traceback.print_exc()
        print("=" * 60 + "\n")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification agent execution error: {str(e)}",
        )