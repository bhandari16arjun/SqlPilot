from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import generate_sql_node, execute_sql_node, explain_results_node

def create_graph():
    workflow = StateGraph(AgentState)

    # Add the nodes
    workflow.add_node("generate_sql", generate_sql_node)
    workflow.add_node("execute_sql", execute_sql_node)
    workflow.add_node("explain_results", explain_results_node)

    # Define the simple, linear edge flow for Phase 1
    # (No self-correction loops or ambiguity checking yet)
    workflow.set_entry_point("generate_sql")
    workflow.add_edge("generate_sql", "execute_sql")
    workflow.add_edge("execute_sql", "explain_results")
    workflow.add_edge("explain_results", END)

    return workflow.compile()
