# SQLPilot 🚀

SQLPilot is a production-grade **Agentic RAG pipeline** that translates natural language questions into highly accurate, secure, and optimized SQL queries. It is designed to act as an autonomous Data Analyst, answering complex business questions by querying databases directly.

Built entirely in Python, SQLPilot uses a **LangGraph state machine** to orchestrate an advanced reasoning loop that includes Ambiguity Detection, AST Security Validation, Self-Consistency (Chain-of-Thought), and Human-in-the-Loop approvals.

## 🧠 Core Features

* **RAG Context Engine:** Uses `ChromaDB` and `sentence-transformers` to dynamically inject database schemas, business logic (markdown files), and "Golden SQL" examples into the LLM's prompt.
* **Human-in-the-Loop Clarification:** If a user's question is ambiguous or missing information, the AI pauses execution and asks the user for clarification before generating SQL.
* **AST Security Blocklist:** Uses `SQLGlot` to parse generated queries into an Abstract Syntax Tree (AST). It strictly blocks destructive queries (`DROP TABLE`) and pauses execution to ask for explicit human Y/N approval before allowing safe mutations (`UPDATE`, `INSERT`, `DELETE`).
* **Self-Consistency (Majority Voting):** Generates 3 entirely different SQL variants for every question, validates them all, and uses the LLM as a "Judge" to select the most optimized query.
* **Self-Correction Loops:** If a query fails syntax validation or throws a database runtime error (e.g., missing column), the graph automatically loops the error back to the LLM to fix it.
* **Telemetry & Tracing:** Integrated with `Langfuse` to visually trace every LLM prompt, token cost, and latency metric in a cloud dashboard.
* **Production API:** Wraps the entire stateful LangGraph agent in a stateless, asynchronous **FastAPI** web server.

## 🛠️ Tech Stack

* **Frameworks:** Python, LangGraph, LangChain, FastAPI, Uvicorn
* **AI & LLM:** Google Gemini 3.5 Flash
* **Retrieval (RAG):** ChromaDB, HuggingFace (`all-MiniLM-L6-v2`)
* **Security:** SQLGlot
* **Observability:** Langfuse

## 🚀 Quickstart

### 1. Installation

Clone the repository and install the dependencies in a virtual environment:

```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the root directory and add your API keys:

```env
# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# Langfuse Telemetry (Optional)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

### 3. Initialize the Database & RAG Index

Seed the dummy SQLite database and build the local ChromaDB vector index:

```bash
python scripts/seed_database.py
python scripts/index_rag.py
```

### 4. Run the Application

You can interact with SQLPilot either through the interactive terminal CLI or by starting the FastAPI production server.

**Option A: Interactive CLI**
```bash
python -m app.cli
```
*Tip: Try typing `/remember Always format dates as YYYY-MM-DD` in the CLI to test the persistent memory engine!*

**Option B: FastAPI Server**
```bash
python -m uvicorn app.api:app --reload
```
Open your browser and navigate to **http://localhost:8000/docs** to interact with the Swagger UI.

## 🏗️ Architecture

1. **User asks a question** -> API receives `POST /query`.
2. **RAG Node** searches ChromaDB for relevant tables, rules, and examples.
3. **Ambiguity Node** checks if the question makes sense. If not, it pauses and waits for user input via `POST /resume`.
4. **Generation Node** writes 3 SQL variants.
5. **Validation Node** parses the SQL into an AST, checking for syntax errors and mutations.
6. **Selection Node** judges the remaining valid variants and picks the best one.
7. **Mutation Node** checks if the query modifies data. If yes, it pauses and waits for 'Y/N' approval via `POST /resume`.
8. **Execution Node** runs the SQL against the database.
9. **Explanation Node** summarizes the data into plain English.
