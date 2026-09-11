from .state import AgentState
from app.llm.gemini import GeminiProvider
from app.db.sqlite import DatabaseExecutor
from app.rag.chroma import RAGController

llm_provider = GeminiProvider()
db_executor = DatabaseExecutor()
rag_controller = RAGController()

def generate_sql_node(state: AgentState) -> AgentState:
    print("--- GENERATING SQL ---")
    question = state["user_question"]
    
    # Retrieve exactly what we need from ChromaDB
    print(f"--- RETRIEVING CONTEXT FOR: '{question}' ---")
    schema_context = rag_controller.retrieve_context(question)
    
    sql = llm_provider.generate_sql(question, schema_context)
    
    return {
        "user_question": question,
        "schema_context": schema_context,
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
