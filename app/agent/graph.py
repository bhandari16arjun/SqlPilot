from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .state import AgentState
from .nodes import (
    retrieve_context_node, 
    check_ambiguity_node, 
    clarify_node,
    generate_sql_node, 
    validate_sql_node,
    select_best_sql_node,
    require_approval_node,
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
        return "generate_sql" # Retry
    return "select_best_sql"

def route_mutation(state: AgentState):
    if state.get("is_mutation"):
        return "require_approval"
    return "execute_sql"

def route_approval(state: AgentState):
    if state.get("mutation_approved"):
        return "execute_sql"
    # If aborted by user, we skip execution and go to explanation
    state["execution_results"] = [{"status": "Aborted by user due to lack of approval"}]
    return "explain_results"

def route_after_execution(state: AgentState):
    if state.get("error_message"):
        if state.get("retry_count", 0) >= MAX_RETRIES:
            return "explain_results" # Give up
        return "generate_sql" # Retry
    return "explain_results"

def create_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("retrieve_context", retrieve_context_node)
    workflow.add_node("check_ambiguity", check_ambiguity_node)
    workflow.add_node("clarify", clarify_node)
    workflow.add_node("generate_sql", generate_sql_node)
    workflow.add_node("validate_sql", validate_sql_node)
    workflow.add_node("select_best_sql", select_best_sql_node)
    workflow.add_node("require_approval", require_approval_node)
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
            "generate_sql": "generate_sql",
            "select_best_sql": "select_best_sql",
            "explain_results": "explain_results"
        }
    )
    
    # Select Best -> (Mutation Check) -> Execute
    workflow.add_conditional_edges(
        "select_best_sql",
        route_mutation,
        {
            "require_approval": "require_approval",
            "execute_sql": "execute_sql"
        }
    )
    
    # Require Approval -> Execute
    workflow.add_conditional_edges(
        "require_approval",
        route_approval,
        {
            "execute_sql": "execute_sql",
            "explain_results": "explain_results"
        }
    )
    
    # Execution Loop
    workflow.add_conditional_edges(
        "execute_sql",
        route_after_execution,
        {
            "generate_sql": "generate_sql",
            "explain_results": "explain_results"
        }
    )
    
    workflow.add_edge("explain_results", END)

    memory = MemorySaver()
    return workflow.compile(checkpointer=memory, interrupt_before=["clarify", "require_approval"])
