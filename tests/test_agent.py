import asyncio
from app.agent.graph import agent_graph
from app.schemas.corporate_entity import VerificationStatus


async def run_entity_check(label: str, company_name: str, country_code: str, website_url: str | None):
    print(f"\n==================== {label} ====================")
    print(f"Target:       {company_name} ({country_code})")
    print(f"Website URL:  {website_url if website_url else 'None (Offline / No URL provided)'}")
    print("Running workflow...\n")

    test_input = {
        "company_name": company_name,
        "country_code": country_code,
        "registration_number": "",
        "website_url": website_url,
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

    final_state = await agent_graph.ainvoke(test_input)

    print("--- RESULTS ---")
    print(f"Status:           {final_state.get('status')}")
    print(f"Confidence Score: {final_state.get('confidence_score')}")
    print(f"Legal Name:       {final_state.get('identified_legal_name')}")
    print(f"Registration ID:  {final_state.get('identified_reg_id')}")

    print("\nKey Findings:")
    for finding in final_state.get("findings", []):
        print(f"  - {finding}")

    print("\nRisk Flags:")
    flags = final_state.get("risk_flags", [])
    if flags:
        for flag in flags:
            print(f"  [!] {flag}")
    else:
        print("  None detected.")
    print("==================================================")


async def main():
    # Case 1: Online entity (with URL)
    await run_entity_check(
        label="CASE 1: WITH WEBSITE",
        company_name="Infosys Limited",
        country_code="IN",
        website_url="https://www.infosys.com",
    )

    # Case 2: Offline entity (without URL)
    await run_entity_check(
        label="CASE 2: WITHOUT WEBSITE",
        company_name="V-Trans (India) Limited",
        country_code="IN",
        website_url=None,
    )


if __name__ == "__main__":
    asyncio.run(main())