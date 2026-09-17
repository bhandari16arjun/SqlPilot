# ?? SQLPilot (v2.0)

**An Enterprise-Grade, Agentic Text-to-SQL Microservice.**

SQLPilot is a natural language database querying tool powered by an intelligent **LangGraph** AI agent. It translates plain English questions into optimized, highly-secure SQL, executes them against your database, and returns the answers in a clean **Streamlit** interface. 

What makes SQLPilot different is its **Human-in-the-Loop** Clarification Engine. If your question is ambiguous (e.g., *"Who is the best customer?"*), SQLPilot refuses to guess. Instead, it pauses its state graph and asks you for clarification before touching the database.

---

## ? Key Features

- **?? LangGraph State Machine:** A multi-node agentic workflow that loops, self-corrects, and handles complex reasoning chains.
- **??? Ironclad Security (AST Validator):** A strict mathematical sqlglot Abstract Syntax Tree validator ensures absolutely zero DML/DDL (mutations, drops, deletes) can be executed.
- **?? State-of-the-Art AI:** Powered by Google's cutting edge gemini-3.5-flash for SQL generation and gemini-embedding-2 for blazing-fast RAG vectorization.
- **?? Rate Limiting:** A built-in sliding-window rate limiter protects your API limits from spam and bot attacks.
- **?? Cloud-Native & Containerized:** Fully orchestrated with Docker, optimized for Render.com's ephemeral free tier, and protected by CI/CD GitHub Actions.
- **?? Clean Chat Interface:** A bespoke Streamlit frontend tailored to handle long-running, interruptible LangGraph sessions asynchronously.

---

## ??? Architecture

1. **Frontend (sqlpilot-ui):** A Streamlit app that manages conversation history and handles LangGraph interrupts.
2. **Backend API (sqlpilot-api):** A robust FastAPI server that hosts the LangGraph AI Engine.
3. **RAG Engine (chroma_db):** Vectorizes your database schema and business rules using a custom LangChain Gemini Wrapper to eliminate memory bloat and OOM crashes.
4. **Execution Sandbox (SQLite):** An isolated database connection with a strict 5-second timeout and 100-row etchmany() cap to prevent DoS loops.

---

## ?? Live Demo

**Check out the live deployment here:**  
?? **[https://sqlpilot-z317.onrender.com](https://sqlpilot-z317.onrender.com)** *(Streamlit UI)*

*(Note: The backend API runs securely at https://sqlpilot-657o.onrender.com. Because it is an API, hitting it in a browser returns a 405 Method Not Allowed. Always interact via the Streamlit UI!)*

---

## ?? Local Development

### 1. Prerequisites
- Python 3.11+
- A Google Gemini API Key

### 2. Setup
\\ash
git clone https://github.com/YOUR-USERNAME/SqlPilot.git
cd SqlPilot
python -m venv venv
source venv/bin/activate  # (On Windows: .env\Scriptsctivate)
pip install -r requirements.txt
\
### 3. Environment Variables
Create a .env file in the root directory:
\\env
GEMINI_API_KEY=your_google_ai_studio_api_key_here
SQLPILOT_API_URL=http://localhost:10000
\
### 4. Run the Stack (Docker Compose)
The easiest way to boot the entire microservice architecture locally is via Docker:
\\ash
docker-compose up --build
\- **Streamlit UI:** http://localhost:8501
- **FastAPI Docs:** http://localhost:10000/docs

---

## ?? Testing

We built a strict Pytest suite to mathematically guarantee the security boundaries hold firm. 

\\ash
pytest tests/
\**Tests Include:**
- 	est_validation.py: Proves the AST Validator blocks DROP, DELETE, INSERT, UPDATE, and malicious PRAGMA queries.
- 	est_rate_limiter.py: Proves the sliding window algorithm correctly throttles request bursts.

---

## ?? Deploying to Render

This repository is optimized for deployment on Render's Free Tier.

1. **Deploy the Backend:** Create a New Web Service (name it sqlpilot-api), leave the Docker command empty, and add your GEMINI_API_KEY to the Environment Variables.
2. **Deploy the Frontend:** Create another New Web Service (name it sqlpilot-ui), set the Docker Command to streamlit run streamlit_app.py --server.port 10000 --server.address 0.0.0.0, and add the SQLPILOT_API_URL pointing to the backend.

Every time you git push to main, Render will automatically pull the new code and redeploy both servers!
