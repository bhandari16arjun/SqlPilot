from .state import AgentState
from app.llm.gemini import GeminiProvider
from app.db.sqlite import DatabaseExecutor
from app.rag.chroma import RAGController

llm_provider = GeminiProvider()
db_executor = DatabaseExecutor()
rag_controller = RAGController()

def retrieve_context_node(state: AgentState) -> AgentState:
    question = state["user_question"]
    history = state.get("conversation_history", [])
    
    # Combine question and history for better RAG retrieval
    full_query = question
    if history:
        full_query += " " + " ".join(history)
        
    print(f"--- RETRIEVING CONTEXT FOR: '{full_query}' ---")
    schema_context = rag_controller.retrieve_context(full_query)
    
    state["schema_context"] = schema_context
    return state

def check_ambiguity_node(state: AgentState) -> AgentState:
    print("--- DETECTING AMBIGUITY ---")
    question = state["user_question"]
    schema = state["schema_context"]
    history = state.get("conversation_history", [])
    
    result = llm_provider.detect_ambiguity(question, schema, history)
    
    state["is_ambiguous"] = result.get("is_ambiguous", False)
    state["clarification_question"] = result.get("clarification_question", "")
    return state

def clarify_node(state: AgentState) -> AgentState:
    # This node acts as an empty anchor point for LangGraph to interrupt before.
    # The actual user input logic happens in the CLI runner.
    return state

def generate_sql_node(state: AgentState) -> AgentState:
    print("--- GENERATING SQL ---")
    question = state["user_question"]
    schema_context = state["schema_context"]
    history = state.get("conversation_history", [])
    
    # Pass history to SQL generation so it knows the full context of what the user wants
    full_context = schema_context + "\n\nClarifications: " + str(history)
    sql = llm_provider.generate_sql(question, full_context)
    
    state["generated_sql"] = sql
    return state

def execute_sql_node(state: AgentState) -> AgentState:
    print("--- EXECUTING SQL ---")
    sql = state["generated_sql"]
    results = db_executor.execute_query(sql)
    state["execution_results"] = results
    return state

def explain_results_node(state: AgentState) -> AgentState:
    print("--- EXPLAINING RESULTS ---")
    question = state["user_question"]
    sql = state["generated_sql"]
    results = state["execution_results"]
    
    explanation = llm_provider.explain_results(question, sql, results)
    state["final_answer"] = explanation
    return state
