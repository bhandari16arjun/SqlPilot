from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
import os
from dotenv import load_dotenv

# Load env variables so Gemini API keys and Langfuse are available
load_dotenv()

from app.agent.graph import create_graph
try:
    from langfuse.langchain import CallbackHandler
    langfuse_handler = CallbackHandler()
    callbacks = [langfuse_handler]
except Exception:
    callbacks = []

app = FastAPI(
    title="SQLPilot API",
    description="An Agentic RAG API for Text-to-SQL and Text-to-DML",
    version="1.0.0"
)

graph = create_graph()

# --- Request Models ---
class QueryRequest(BaseModel):
    question: str
    thread_id: Optional[str] = None

class ResumeRequest(BaseModel):
    thread_id: str
    answer: str  # Text for clarification

# --- Endpoints ---
@app.post("/query")
def run_query(req: QueryRequest):
    thread_id = req.thread_id or str(uuid.uuid4())
    config = {
        "configurable": {"thread_id": thread_id},
        "callbacks": callbacks
    }
    
    initial_state = {
        "user_question": req.question,
        "schema_context": "",
        "is_ambiguous": False,
        "clarification_question": "",
        "conversation_history": [],
        "sql_variants": None,
        "valid_sql_variants": None,
        "generated_sql": None,
        "correction_history": [],
        "retry_count": 0,
        "execution_results": None,
        "final_answer": None
    }
    
    # Run the state machine
    for _ in graph.stream(initial_state, config):
        pass
        
    state = graph.get_state(config)
    
    # Check if the graph paused for Human-in-the-Loop interaction
    if state.next and state.next[0] == "clarify":
        return {
            "status": "needs_clarification",
            "thread_id": thread_id,
            "message": state.values.get("clarification_question")
        }
            
    return {
        "status": "success",
        "thread_id": thread_id,
        "sql": state.values.get("generated_sql"),
        "results": state.values.get("execution_results"),
        "explanation": state.values.get("final_answer")
    }

@app.post("/resume")
def resume_query(req: ResumeRequest):
    config = {
        "configurable": {"thread_id": req.thread_id},
        "callbacks": callbacks
    }
    state = graph.get_state(config)
    
    if not state.next:
        raise HTTPException(status_code=400, detail="No pending actions for this thread ID.")
        
    current_values = state.values
    
    # Handle Clarification Interrupt
    if state.next[0] == "clarify":
        history = current_values.get("conversation_history", [])
        q = current_values.get("clarification_question")
        history.append(f"AI: {q}\nUser: {req.answer}")
        graph.update_state(config, {"conversation_history": history, "is_ambiguous": False})
    else:
        raise HTTPException(status_code=400, detail="Action mismatch with current graph state.")
        
    # Resume the graph from where it paused
    for _ in graph.stream(None, config):
        pass
        
    new_state = graph.get_state(config)
    
    return {
        "status": "success",
        "thread_id": req.thread_id,
        "sql": new_state.values.get("generated_sql"),
        "results": new_state.values.get("execution_results"),
        "explanation": new_state.values.get("final_answer")
    }
