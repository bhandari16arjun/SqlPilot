from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .state import AgentState
from .nodes import (
    retrieve_context_node, 
    check_ambiguity_node, 
    clarify_node,
    generate_sql_node, 
    validate_sql_node,
    correct_sql_node,
    select_best_sql_node,
    execute_sql_node, 
    explain_results_node
)

MAX_RETRIES = 2

def route_ambiguity(state: AgentState):
    if state.get("is_ambiguous"):
        return "clarify"
    return "generate_sql"

def route_after_validation(state: AgentState):
    if not state.get("valid_sql_variants"):
        if state.get("retry_count", 0) >= MAX_RETRIES:
            return "explain_results" # Give up
        return "correct_sql" # Route to explicit correction node
    return "select_best_sql"

def route_after_execution(state: AgentState):
    history = state.get("correction_history", [])
    if history and history[-1]["stage"] == "execution":
        # Check if error is unrecoverable (e.g. timeout)
        if not history[-1]["recoverable"] or state.get("retry_count", 0) >= MAX_RETRIES:
            return "explain_results" # Give up
        return "correct_sql" # Route to explicit correction node
    return "explain_results"

def create_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("retrieve_context", retrieve_context_node)
    workflow.add_node("check_ambiguity", check_ambiguity_node)
    workflow.add_node("clarify", clarify_node)
    workflow.add_node("generate_sql", generate_sql_node)
    workflow.add_node("validate_sql", validate_sql_node)
    workflow.add_node("correct_sql", correct_sql_node)
    workflow.add_node("select_best_sql", select_best_sql_node)
    workflow.add_node("execute_sql", execute_sql_node)
    workflow.add_node("explain_results", explain_results_node)

    workflow.set_entry_point("retrieve_context")
    workflow.add_edge("retrieve_context", "check_ambiguity")
    
    # Ambiguity Check
    workflow.add_conditional_edges(
        "check_ambiguity",
        route_ambiguity,
        {
            "clarify": "clarify",
            "generate_sql": "generate_sql"
        }
    )
    workflow.add_edge("clarify", "retrieve_context")
    
    # Generation -> Validation
    workflow.add_edge("generate_sql", "validate_sql")
    
    # Validation Loop
    workflow.add_conditional_edges(
        "validate_sql",
        route_after_validation,
        {
            "correct_sql": "correct_sql",
            "select_best_sql": "select_best_sql",
            "explain_results": "explain_results"
        }
    )
    
    # Correction ALWAYS goes back to validation
    workflow.add_edge("correct_sql", "validate_sql")
    
    # Select Best -> Execute
    workflow.add_edge("select_best_sql", "execute_sql")
    
    # Execution Loop
    workflow.add_conditional_edges(
        "execute_sql",
        route_after_execution,
        {
            "correct_sql": "correct_sql",
            "explain_results": "explain_results"
        }
    )
    
    workflow.add_edge("explain_results", END)

    memory = MemorySaver()
    return workflow.compile(checkpointer=memory, interrupt_before=["clarify"])
