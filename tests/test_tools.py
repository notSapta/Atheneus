import asyncio
from app.agent.tools.search import TavilySearchClient
from app.agent.tools.reader import JinaReaderClient


async def test_sensors():
    print("\n--- 1. Testing Tavily Search ---")
    search_client = TavilySearchClient()
    query = "Infosys Limited corporate registration MCA India"
    print(f"Searching for: '{query}'...")
    
    search_results = await search_client.search(query=query, max_results=2)
    for idx, res in enumerate(search_results, 1):
        print(f"[{idx}] {res.title}")
        print(f"    URL: {res.url}")
        print(f"    Snippet: {res.content[:120]}...\n")

    print("--- 2. Testing Jina Reader ---")
    reader_client = JinaReaderClient()
    target_site = "https://www.infosys.com/about.html"
    print(f"Fetching clean markdown from: {target_site}...")
    
    doc = await reader_client.fetch_markdown(target_site, max_chars=400)
    print(f"Status: {doc.status_code}")
    print(f"Markdown Excerpt:\n{doc.markdown_content}\n")
    print("--- Sensor Verification Complete! ATHENEUS has live web connectivity. ---")


if __name__ == "__main__":
    asyncio.run(test_sensors())