from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .state import AgentState
from .nodes import (
    retrieve_context_node, 
    check_ambiguity_node, 
    clarify_node,
    generate_sql_node, 
    execute_sql_node, 
    explain_results_node
)

def route_ambiguity(state: AgentState):
    if state.get("is_ambiguous"):
        return "clarify"
    return "generate_sql"

def create_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("retrieve_context", retrieve_context_node)
    workflow.add_node("check_ambiguity", check_ambiguity_node)
    workflow.add_node("clarify", clarify_node)
    workflow.add_node("generate_sql", generate_sql_node)
    workflow.add_node("execute_sql", execute_sql_node)
    workflow.add_node("explain_results", explain_results_node)

    # RAG -> Ambiguity Check
    workflow.set_entry_point("retrieve_context")
    workflow.add_edge("retrieve_context", "check_ambiguity")
    
    # Branching: Ambiguous -> Clarify, Clear -> Generate SQL
    workflow.add_conditional_edges(
        "check_ambiguity",
        route_ambiguity,
        {
            "clarify": "clarify",
            "generate_sql": "generate_sql"
        }
    )
    
    # Loop back from Clarify to RAG to inject the new context
    workflow.add_edge("clarify", "retrieve_context")
    
    # Standard generation pipeline
    workflow.add_edge("generate_sql", "execute_sql")
    workflow.add_edge("execute_sql", "explain_results")
    workflow.add_edge("explain_results", END)

    memory = MemorySaver()
    # Interrupt execution BEFORE the clarify node runs
    return workflow.compile(checkpointer=memory, interrupt_before=["clarify"])
