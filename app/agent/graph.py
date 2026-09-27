from langgraph.graph import StateGraph, START, END
from app.agent.state import AgentState
from app.agent.nodes import search_node, scrape_node, reasoning_node

def create_verification_graph():
    workflow = StateGraph(AgentState)

    # Register graph nodes
    workflow.add_node("search", search_node)
    workflow.add_node("scrape", scrape_node)
    workflow.add_node("reasoning", reasoning_node)

    # Flow: START -> search -> scrape -> reasoning -> END
    workflow.add_edge(START, "search")
    workflow.add_edge("search", "scrape")
    workflow.add_edge("scrape", "reasoning")
    workflow.add_edge("reasoning", END)

    return workflow.compile()

# Global compiled agent ready for invocation
agent_graph = create_verification_graph()