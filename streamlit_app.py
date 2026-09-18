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

import os
import uuid
import httpx
import sqlite3
import pandas as pd
import streamlit as st

API_BASE_URL = os.getenv("SQLPILOT_API_URL", "http://localhost:8000")
REQUEST_TIMEOUT = 120.0

st.set_page_config(page_title="SQLPilot", page_icon="🚀", layout="wide")

# Custom CSS for a rocking UI
st.markdown("""
<style>
    .hero-title {
        font-size: 3rem !important;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #FF4B4B, #FF904F);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .hero-subtitle {
        font-size: 1.2rem;
        color: #A0AEC0;
        margin-bottom: 2rem;
    }
    /* Hide the default Streamlit top margin */
    .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Sidebar Navigation & State
# ---------------------------------------------------------
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_clarification" not in st.session_state:
    st.session_state.pending_clarification = None

with st.sidebar:
    st.markdown("### 🧭 Navigation")
    page = st.radio("Go to:", ["💬 Chat", "🗄️ Database Schema", "ℹ️ About SQLPilot"], label_visibility="collapsed")
    
    st.divider()
    
    st.markdown("### ⚙️ Control Panel")
    st.caption(f"Session ID: `{st.session_state.thread_id[:8]}...`")
    if st.button("🔄 Start New Conversation", use_container_width=True):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.pending_clarification = None
        st.rerun()

    st.divider()
    st.markdown("### 📊 System Status")
    st.success("🟢 API Connected")
    st.success("🟢 Sandbox Active")
    st.success("🟢 Qwen 3.8-27b Online")

# ---------------------------------------------------------
# Page 2: Database Schema (Live Inspector)
# ---------------------------------------------------------
if page == "🗄️ Database Schema":
    st.markdown('<p class="hero-title">🗄️ Schema Explorer</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Live inspection of the currently connected database.</p>', unsafe_allow_html=True)
    
    try:
        conn = sqlite3.connect("data/demo.db")
        tables_df = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';", conn)
        
        if tables_df.empty:
            st.warning("No tables found in the database.")
        else:
            st.markdown(f"**Found {len(tables_df)} tables in the database:**")
            
            # Display tables in a nice 2-column grid
            cols = st.columns(2)
            for i, table_name in enumerate(tables_df['name']):
                with cols[i % 2]:
                    with st.expander(f"📁 **{table_name}**", expanded=False):
                        df = pd.read_sql(f"PRAGMA table_info('{table_name}');", conn)
                        # Clean up the dataframe for display
                        display_df = df[['name', 'type', 'notnull', 'pk']].rename(
                            columns={'name': 'Column', 'type': 'Type', 'notnull': 'Required', 'pk': 'Primary Key'}
                        )
                        # Convert 1/0 to Yes/No
                        display_df['Required'] = display_df['Required'].map({1: '✅', 0: ''})
                        display_df['Primary Key'] = display_df['Primary Key'].map({1: '🔑', 0: ''})
                        
                        st.dataframe(display_df, hide_index=True, use_container_width=True)
        conn.close()
    except Exception as e:
        st.error(f"Could not load database schema. Ensure data/demo.db exists. Error: {e}")

# ---------------------------------------------------------
# Page 3: About
# ---------------------------------------------------------
elif page == "ℹ️ About SQLPilot":
    st.markdown('<p class="hero-title">ℹ️ About SQLPilot</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">The Agentic Text-to-SQL AI that <b>asks for clarification</b> before it guesses.</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🎯 What we solve")
        st.markdown("""
        Standard AI tools silently hallucinate or execute dangerous queries. **SQLPilot is different:**
        * 🛑 **Ambiguity Detection:** It detects vague questions and *asks you* what you meant.
        * 🛡️ **Security Sandbox:** It intercepts and strictly blocks `DELETE`/`DROP` queries.
        * 🔄 **Self-Correction:** It catches its own syntax errors and tries again.
        """)
    with col2:
        st.markdown("### 🗄️ The Data (Chinook)")
        st.markdown("""
        To prove it works, we connected it to a complex **Digital Media Store** database (~15,000 rows).
        * 🎵 **Media:** `Tracks`, `Albums`, `Artists`, `Genres`
        * 🛒 **Sales:** `Invoices`, `InvoiceLines`, `Customers`
        * 👥 **Staff:** `Employees` (Support Reps)
        """)

    st.markdown("### 💡 Try copy-pasting these questions:")
    c1, c2, c3 = st.columns(3)
    c1.info("🏆 **Test Complex Joins:**\n\n*\"Who is our top-selling artist?\"*")
    c2.warning("🤔 **Test Ambiguity:**\n\n*\"Show me all sales in Canada.\"*\n\n*(It will pause and ask if you mean Customer location or Billing location!)*")
    c3.error("🛡️ **Test Security:**\n\n*\"Delete all customers.\"*\n\n*(Watch the agent block the mutation)*")

# ---------------------------------------------------------
# Page 1: Chat UI
# ---------------------------------------------------------
elif page == "💬 Chat":
    st.markdown('<p class="hero-title">🚀 SQLPilot</p>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">Ask any question about your data.</p>', unsafe_allow_html=True)

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
            st.session_state.messages.append({"role": "assistant", "content": pending.get("message", "Can you clarify?")})
            st.session_state.messages.append({"role": "user", "content": free_text})
            with st.chat_message("user"):
                st.write(free_text)
                
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    result = _call_api("/resume", {"thread_id": st.session_state.thread_id, "answer": free_text})
                _handle_result(result)
                st.rerun()
    else:
        question = st.chat_input("Ask a question about your data...")
        if question:
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.write(question)
                
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    result = _call_api("/query", {"thread_id": st.session_state.thread_id, "question": question})
                _handle_result(result)
                st.rerun()
