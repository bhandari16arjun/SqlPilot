# 🚀 SQLPilot (v2.0)

A Text-to-SQL agent that **asks before it guesses**. Built with LangGraph, ChromaDB, SQLGlot, FastAPI, and Streamlit.

Ask a question in plain English, and SQLPilot retrieves the right schema, checks whether your question is actually answerable without guessing, generates dialect-aware SQL, validates and self-corrects it before it ever touches the database, runs it in a locked-down read-only sandbox, and explains the result back to you in plain English.

---

## Table of Contents
- [Why This Exists (The Challenges Solved)](#-why-this-exists-the-challenges-solved)
- [Architecture & State Graph](#-architecture--state-graph)
- [How a Request Flows Through the System](#-how-a-request-flows-through-the-system)
- [Validation & Self-Correction](#-validation--self-correction)
- [Security & Sandbox](#-security--sandbox)
- [Live Demo & Deployment](#-live-demo--deployment)
- [Local Development](#-local-development)

---

## 🛡️ Why This Exists (The Challenges Solved)

Building a text-to-SQL system that humans can actually trust is hard. Naive "prompt-in, query-out" scripts fail for predictable reasons. Here is how SQLPilot v2.0 solves them:

### 1. The Hallucination Problem (Invented Columns)
* **Challenge:** LLMs guess column names from training data (e.g. generating `first_name` when the table only has `full_name`).
* **Solution:** Before generation, the agent retrieves the *exact* schema chunks relevant to the question from a **ChromaDB** vector store using Gemini's lightning-fast `gemini-embedding-2` model.

### 2. The Domain Knowledge Gap (Ambiguity)
* **Challenge:** "What's our MRR?" or "show me revenue" mean nothing to an LLM without your business's specific definitions.
* **Solution:** An ambiguity-detection node classifies the question *before* any SQL is generated. If it is genuinely ambiguous, the pipeline halts and asks a clarifying question (Human-in-the-Loop) instead of silently picking an interpretation.

### 3. Syntax & Dialect Errors
* **Challenge:** LLMs mix up dialect-specific syntax and occasionally produce SQL that just doesn't parse.
* **Solution:** Generated SQL is parsed with **SQLGlot** before it ever reaches the database. A parse failure is fed back to the LLM along with the exact error and prior failed attempts (so it doesn't repeat mistakes), up to 2 retries.

### 4. Database Security Risks
* **Challenge:** Prompt injection or a model mistake could produce a `DROP TABLE` or similar.
* **Solution:** (1) The LLM is explicitly prompt-engineered to swap mutations for harmless `SELECT 1` queries. (2) An AST walk over the parsed SQLGlot tree catches mutation node types even if hidden in a subquery. (3) A Sliding-Window rate limiter protects the API.

---

## 🏗️ Architecture & State Graph

The core of the system is a **LangGraph state machine**. A single typed `AgentState` flows through a series of nodes with conditional routing — including two independent retry loops and an early-exit path for ambiguous questions.

```mermaid
graph TD
    Start([User question]) --> RL[rate_limit_guard]
    RL -- over limit --> ERR[explain_with_error]
    RL --> RC[retrieve_context<br/>ChromaDB: schema + business rules]
    RC --> AMB{check_ambiguity}
    AMB -- ambiguous --> CLARIFY[stop_for_clarification]
    CLARIFY -. caller collects answer,<br/>re-invokes graph .-> RC
    AMB -- clear --> GEN[generate_sql: LLM]
    GEN --> VAL[validate_sql<br/>SQLGlot parse + AST walk]
    VAL -- syntax error, retries < 2 --> FIX[correct_sql: Dedicated Recovery Node]
    FIX --> VAL
    VAL -- security violation --> ERR
    VAL -- valid --> EXEC[execute_query<br/>read-only SQLite, timeout, row cap]
    EXEC -- recoverable error, retries < 2 --> FIX
    EXEC -- unrecoverable / retries exhausted --> ERR
    EXEC -- success --> EXPLAIN[explain_results: LLM]
    EXPLAIN --> End([Answer + SQL + explanation])
    ERR --> End
```

### System Components

| Layer | Technology | Role |
|---|---|---|
| **Orchestrator** | LangGraph | Deterministic state machine with two retry loops and a clarification exit |
| **LLM** | Gemini 3.5 Flash | Fast, intelligent SQL generation and ambiguity detection |
| **Context engine (RAG)** | ChromaDB + LangChain | Retrieves schema chunks using a custom Gemini Embeddings wrapper |
| **Validation** | SQLGlot | Offline parse + AST mutation scan, dialect-aware |
| **Database sandbox** | SQLite | Read-only connection, 5s timeout, 100-row `fetchmany()` cap |
| **Security** | Custom | Sliding-window API rate limiter |
| **API** | FastAPI + Pydantic | Secure REST API hosting the graph logic |
| **Frontend** | Streamlit | Chat interface equipped to handle asynchronous graph interruptions |

---

## 🔄 How a Request Flows Through the System

1. **User asks a question** in the Streamlit UI.
2. Streamlit hits the FastAPI `/query` endpoint.
3. **LangGraph wakes up** and runs the Rate Limiter guard node.
4. **Context Retrieval:** Hits ChromaDB to grab the schema definitions matching the keywords in the question.
5. **Ambiguity Check:** The LLM decides if the question is safe to answer, or if it needs clarification. If it needs clarification, it immediately halts and returns a multiple-choice question to the UI.
6. **SQL Generation:** The LLM receives the schema + question and outputs 3 SQL variants.
7. **Validation & Execution:** The AST Validator selects the best variant, parses it, and executes it.
8. **Formatting:** The results are formatted back into a natural English explanation and pushed to the UI!

---

## 🛡️ Validation & Self-Correction

SQLPilot features a **Dedicated Recovery Node**. If an Execution Error occurs (e.g. `SQLite error: no such table: customers`), the LangGraph state machine catches the error, records it in the `correction_history` state array, and routes it to the `correct_sql` node. 

The LLM is prompted with the entire history of its failed attempts and the exact error messages so it can learn from its mistakes and generate a newly corrected variant. This loops up to 2 times before gracefully giving up.

---

## 🔒 Security & Sandbox

We take security seriously. SQLPilot deploys a defense-in-depth approach:
1. **Prompt Engineering Sandbox:** The LLM refuses to write DDL/DML.
2. **AST Walk:** We parse the raw string into a SQLGlot Abstract Syntax Tree and mathematically verify no `DROP`, `DELETE`, `INSERT`, `UPDATE`, `ALTER`, or `COMMAND` nodes exist.
3. **Execution Sandbox:** The SQLite connection is heavily restricted to a 5-second `threading.Timer` execution window and a 100-row `fetchmany()` limit to prevent Denial of Service via massive queries.

---

## 🌐 Live Demo & Deployment

**Check out the live deployment here:**  
🔗 **[https://sqlpilot-z317.onrender.com](https://sqlpilot-z317.onrender.com)** *(Streamlit UI)*

### Deploying to Render
This repository is heavily optimized for Render's Free Tier.
1. **Backend (`sqlpilot-api`):** Deploy a new Web Service using the Dockerfile default command. Set `GEMINI_API_KEY`.
2. **Frontend (`sqlpilot-ui`):** Deploy another Web Service using Docker command: `streamlit run streamlit_app.py --server.port 10000 --server.address 0.0.0.0`. Set `SQLPILOT_API_URL` to point to your backend.

---

## 💻 Local Development

```bash
git clone https://github.com/YOUR-USERNAME/SqlPilot.git
cd SqlPilot
python -m venv venv
source venv/bin/activate  # (On Windows: .\venv\Scripts\activate)
pip install -r requirements.txt
```

Create a `.env` file:
```env
GEMINI_API_KEY=your_google_ai_studio_api_key_here
SQLPILOT_API_URL=http://localhost:10000
```

Boot the entire microservice architecture locally:
```bash
docker-compose up --build
```
- **Streamlit UI:** `http://localhost:8501`
- **FastAPI Docs:** `http://localhost:10000/docs`
