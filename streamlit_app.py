"""
Streamlit chat frontend for SQLPilot v2.

Run with:
    streamlit run streamlit_app.py

Talks to the FastAPI backend (app/api.py) over HTTP -- start it first:
    uvicorn app.api:app --reload
"""

import os
import uuid
import httpx
import streamlit as st

API_BASE_URL = os.getenv("SQLPILOT_API_URL", "http://localhost:8000")
REQUEST_TIMEOUT = 120.0

st.set_page_config(page_title="SQLPilot", page_icon="🚀", layout="wide")
st.title("🚀 SQLPilot")
st.caption("Text-to-SQL with clarification - asks before it guesses")

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_clarification" not in st.session_state:
    st.session_state.pending_clarification = None

with st.sidebar:
    st.subheader("Session")
    st.caption(f"`{st.session_state.thread_id}`")
    if st.button("New conversation"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.pending_clarification = None
        st.rerun()

    st.divider()
    st.subheader("Database")
    st.caption("The demo runs on a synthetic dataset.")

def _call_api(path: str, payload: dict) -> dict:
    try:
        resp = httpx.post(f"{API_BASE_URL}{path}", json=payload, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"status": "error", "error": str(e)}

def _render_result(result: dict) -> None:
    if result.get("sql"):
        st.code(result["sql"], language="sql")
    
    rows = result.get("results")
    if rows is not None:
        if rows:
            st.dataframe(rows, use_container_width=True)
        else:
            st.caption("(no rows returned)")
            
    if result.get("explanation"):
        st.write(result["explanation"])
        
    if result.get("error"):
        st.error(result["error"])

def _handle_result(result: dict) -> None:
    if result.get("status") == "needs_clarification":
        st.session_state.pending_clarification = result
    else:
        st.session_state.pending_clarification = None
        st.session_state.messages.append({"role": "assistant", "result": result})

# Replay conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if "content" in msg:
            st.write(msg["content"])
        if "result" in msg:
            _render_result(msg["result"])

pending = st.session_state.pending_clarification

if pending:
    with st.chat_message("assistant"):
        st.write(pending.get("message", "Can you clarify?"))
        
    free_text = st.chat_input("Type your answer here...")
    if free_text:
        st.session_state.messages.append({"role": "user", "content": free_text})
        with st.spinner("Thinking..."):
            result = _call_api(
                "/resume",
                {"thread_id": st.session_state.thread_id, "answer": free_text},
            )
        _handle_result(result)
        st.rerun()
else:
    question = st.chat_input("Ask a question about your data...")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.spinner("Thinking..."):
            result = _call_api(
                "/query",
                {"thread_id": st.session_state.thread_id, "question": question},
            )
        _handle_result(result)
        st.rerun()
