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
    question = state.get("clarification_question") or state["user_question"]
    schema = state.get("schema_context", "")
    
    prefs = memory_manager.get_preferences()
    
    full_context = f"SCHEMA:\n{schema}"
    if prefs:
        full_context += "\n\nCRITICAL USER PREFERENCES (You must follow these rules):\n" 
        for p in prefs:
            full_context += f"- {p}\n"
            
    variants = llm_provider.generate_sql(question, full_context)
    print(f"[Generated {len(variants)} variants]")
    
    state["sql_variants"] = variants
    return state

def validate_sql_node(state: AgentState) -> AgentState:
    print("--- VALIDATING SQL VARIANTS (AST Check) ---")
    variants = state.get("sql_variants", [])
    valid_variants = []
    errors = []
    
    for i, sql in enumerate(variants):
        error_msg = validate_sql(sql)
        if error_msg:
            errors.append(f"Variant {i+1} failed: {error_msg}")
        else:
            valid_variants.append(sql)
            
    state["valid_sql_variants"] = valid_variants
    
    if not valid_variants:
        combined_error = "All generated variants failed validation:\n" + "\n".join(errors)
        print(f"[Validation Failed] {combined_error}")
        
        history = state.get("correction_history", [])
        history.append({
            "stage": "validation",
            "error_message": combined_error,
            "recoverable": True
        })
        state["correction_history"] = history
        state["retry_count"] = state.get("retry_count", 0) + 1
    else:
        print(f"[{len(valid_variants)} variants passed validation]")
        
    return state

def correct_sql_node(state: AgentState) -> AgentState:
    print("--- CORRECTING SQL (Dedicated Recovery Node) ---")
    history = state.get("correction_history", [])
    if not history:
        return state
        
    question = state["user_question"]
    schema = state.get("schema_context", "")
    
    history_str = "\n\n".join([f"Attempt Failed at {h['stage']}:\nError: {h['error_message']}" for h in history])
    
    prompt = f"Fix the SQL for: '{question}'.\nSchema:\n{schema}\n\nPast errors you must avoid:\n{history_str}"
    
    # We ask the LLM to generate 3 new fixed variants based on the ENTIRE error history
    variants = llm_provider.generate_sql(prompt, "You are a SQL expert fixing broken queries. Do NOT repeat past mistakes.")
    print(f"[Generated {len(variants)} corrected variants]")
    
    state["sql_variants"] = variants
    return state

def select_best_sql_node(state: AgentState) -> AgentState:
    valid_variants = state.get("valid_sql_variants", [])
    if not valid_variants:
        return state
        
    print(f"--- SELECTING BEST SQL FROM {len(valid_variants)} VALID VARIANTS ---")
    best_sql = llm_provider.select_best_sql(state["user_question"], valid_variants)
    
    state["generated_sql"] = best_sql
    return state

def execute_sql_node(state: AgentState) -> AgentState:
    print("--- EXECUTING SQL ---")
    sql = state["generated_sql"]
    db = DatabaseExecutor()
    
    try:
        results = db.execute_query(sql)
        print(f"[Success] {len(results)} rows returned")
        state["execution_results"] = results
    except Exception as e:
        error_msg = str(e)
        print(f"[Execution Error] {error_msg}")
        
        # Error Classification: Identify unrecoverable infrastructure errors
        unrecoverable_patterns = ["timeout", "readonly", "query_only", "locked"]
        is_recoverable = not any(p in error_msg.lower() for p in unrecoverable_patterns)
        
        if not is_recoverable:
            print(f"⚠️ [Error Class: Unrecoverable] Aborting retry loop.")
            
        history = state.get("correction_history", [])
        history.append({
            "stage": "execution",
            "sql": sql,
            "error_message": error_msg,
            "recoverable": is_recoverable
        })
        state["correction_history"] = history
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
