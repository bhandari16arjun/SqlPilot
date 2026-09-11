from .state import AgentState
from app.llm.gemini import GeminiProvider
from app.db.sqlite import DatabaseExecutor

llm_provider = GeminiProvider()
db_executor = DatabaseExecutor()

def generate_sql_node(state: AgentState) -> AgentState:
    print("--- GENERATING SQL ---")
    question = state["user_question"]
    
    # For Phase 1, just get the hardcoded schema (no RAG yet)
    schema = db_executor.get_schema()
    
    sql = llm_provider.generate_sql(question, schema)
    
    return {
        "user_question": question,
        "schema_context": schema,
        "generated_sql": sql,
        "execution_results": None,
        "final_answer": None
    }

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
