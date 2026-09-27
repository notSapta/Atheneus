ATHENEUS: Autonomous KYB Verification Agent
ATHENEUS is an autonomous business verification engine designed for modern Know Your Business (KYB) workflows. Built on FastAPI and orchestrated with LangGraph, it autonomously cross-references company registration claims, resolves official registry records, scrapes digital footprints, and detects corporate identity spoofing and fraud signals in real time.

Key Capabilities
Autonomous Corporate Intelligence: Uses search grounding and dynamic scraping to resolve official entity records (e.g., CIN, GSTIN, LEI) across international and domestic jurisdictions.

Dual-Mode Verification: Handles both online digital-first entities and local/offline establishments (brick-and-mortar SMBs) without penalizing businesses lacking an online domain.

Fraud & Spoofing Detection: Flags mismatched company numbers, suspect domains (e.g., phishing .xyz portals), geography discrepancies, and scraping errors.

Deterministic Structured Output: Delivers strict JSON payloads through Pydantic schemas, reporting confidence scores, verification status (VERIFIED, SUSPICIOUS, REJECTED, UNVERIFIED), and grounded evidence citations.

Architecture & Tech Stack
Plaintext
[ Client / Swagger UI ]
          │ (HTTP POST)
          ▼
   [ FastAPI Router ]
          │ (BusinessVerificationRequest)
          ▼
 [ LangGraph State Agent ]
   ├── Search Node (Tavily Search API)
   ├── Scrape Node (Jina Reader API - Markdown Extraction)
   └── Reasoning Node (Groq / gpt-oss-120b - Structured Analysis)
          │
          ▼
[ BusinessVerificationResponse ] ──► (JSON 200 OK)

Framework: FastAPI (Python 3.10+)

Orchestration: LangGraph / LangChain

LLM Inference: Groq Cloud (openai/gpt-oss-120b)

Web Search Grounding: Tavily Search API

Web Scraping: Jina Reader API

Data Validation: Pydantic v2

Project Structure
Plaintext
Atheneus/
├── app/
│   ├── main.py                  # FastAPI application entrypoint & middleware
│   ├── core/
│   │   └── config.py            # Pydantic BaseSettings & env management
│   ├── schemas/
│   │   └── corporate_entity.py  # Request & Response Pydantic contracts
│   ├── agent/
│   │   ├── state.py             # LangGraph TypedDict state definition
│   │   ├── nodes.py             # Search, Scrape, and LLM Reasoning nodes
│   │   ├── graph.py             # Compiled StateGraph workflow
│   │   └── tools/
│   │       ├── search.py        # Tavily search client wrapper
│   │       └── reader.py        # Jina Reader markdown scraper wrapper
│   └── api/
│       └── v1/
│           ├── api.py           # v1 API router aggregation
│           └── endpoints/
│               └── verification.py # /corporate/verify endpoint handler
├── tests/                       # Unit and integration test scripts
├── .env.example                 # Environment variable templates
├── .gitignore                   # Git exclusion rules
├── requirements.txt             # Frozen dependencies
└── README.md                    # Project documentation

Getting Started
1. Prerequisites
Python 3.10+

Valid API keys for Groq, Tavily, and Jina

2. Installation & Setup
Clone the repository and set up a virtual environment:

Bash
git clone https://github.com/<your-username>/atheneus.git
cd atheneus

python -m venv venv
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
3. Environment Variables
Create a .env file in the root directory:

Code snippet
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
JINA_API_KEY=your_jina_api_key
4. Run the API Server
Bash
uvicorn app.main:app --reload --port 8000
Access the interactive API documentation at:
[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Verified Test Cases
1. Enterprise Online Entity (VERIFIED)
Query: Infosys Limited | Official URL: [https://www.infosys.com](https://www.infosys.com) | Bengaluru, IN

Result: Status VERIFIED, Confidence 0.96

Findings: Successfully corroborated Ministry of Corporate Affairs (MCA) records, CIN L85110KA1981PLC013115, and LEI identifier 335800TYLGG93MM7PR89.

2. Impersonation / Fake Portal (REJECTED)
Query: Tata Consultancy Services Limited | Official URL: [https://tata-consultancy-free-jobs-portal-login.xyz](https://tata-consultancy-free-jobs-portal-login.xyz) | Registration ID: FAKE-CIN-99999999-XYZ | Lagos, NG

Result: Status REJECTED, Confidence 0.96 (High certainty of fraud)

Risk Signals:

Country mismatch (claimed Nigeria vs. verified India records).

Unresolvable .xyz domain.

Fabricated corporate registration ID.

Phishing / job scam impersonation detected.

3. Brick-and-Mortar / Offline Business (VERIFIED)
Query: Vidyarthi Bhavan | Official URL: null | Bengaluru, IN

Result: Status VERIFIED, Confidence 0.93

Findings: Successfully located GST registry records (GSTIN: 29AAFFV6137J1ZP, PAN: AAFFV6137J), matched the street address, and verified operational partnership without penalizing the entity for lacking an official domain.

License
MIT