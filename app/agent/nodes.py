from .state import AgentState
from app.llm.gemini import GeminiProvider
from app.db.sqlite import DatabaseExecutor
from app.rag.chroma import RAGController
from app.agent.validators import validate_sql

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
    
    # Reset retry state whenever we start a fresh retrieval
    state["retry_count"] = 0
    state["error_message"] = None
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
    return state

def generate_sql_node(state: AgentState) -> AgentState:
    print("--- GENERATING SQL ---")
    question = state["user_question"]
    schema_context = state["schema_context"]
    history = state.get("conversation_history", [])
    error_msg = state.get("error_message")
    
    full_context = schema_context + "\n\nClarifications: " + str(history)
    
    # Self-Correction: If we hit an error earlier, feed it back to the LLM
    if error_msg:
        print(f"--- RETRYING AFTER ERROR: {error_msg} ---")
        full_context += f"\n\nYOUR PREVIOUS QUERY FAILED WITH ERROR:\n{error_msg}\nPLEASE FIX IT."
        
    sql = llm_provider.generate_sql(question, full_context)
    
    state["generated_sql"] = sql
    state["error_message"] = None # Reset error flag after generating
    return state

def validate_sql_node(state: AgentState) -> AgentState:
    print("--- VALIDATING SQL (AST Check) ---")
    sql = state.get("generated_sql", "")
    error_msg = validate_sql(sql)
    
    if error_msg:
        print(f"[Validation Failed] {error_msg}")
        state["error_message"] = error_msg
        state["retry_count"] = state.get("retry_count", 0) + 1
    return state

def execute_sql_node(state: AgentState) -> AgentState:
    print("--- EXECUTING SQL ---")
    sql = state["generated_sql"]
    
    try:
        results = db_executor.execute_query(sql)
        state["execution_results"] = results
    except Exception as e:
        error_msg = f"DATABASE RUNTIME ERROR: {str(e)}"
        print(f"[Execution Failed] {error_msg}")
        state["error_message"] = error_msg
        state["retry_count"] = state.get("retry_count", 0) + 1
        
    return state

def explain_results_node(state: AgentState) -> AgentState:
    # If we maxed out retries and failed, explain the failure
    if state.get("error_message"):
        print("--- GIVING UP (Max Retries Reached) ---")
        state["final_answer"] = f"I failed to generate a working SQL query after multiple attempts. Last error: {state['error_message']}"
        return state
        
    print("--- EXPLAINING RESULTS ---")
    question = state["user_question"]
    sql = state["generated_sql"]
    results = state["execution_results"]
    
    explanation = llm_provider.explain_results(question, sql, results)
    state["final_answer"] = explanation
    return state
