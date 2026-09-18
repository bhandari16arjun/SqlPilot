import os
import json
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from .base import LLMProvider

class GeminiProvider(LLMProvider):
    def __init__(self):
        # Groq: free tier gives 14,400 requests/day (vs 20 with Gemini free tier)
        api_key = os.getenv("GROQ_API_KEY") or "missing_key"

        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            groq_api_key=api_key
        )

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=20),
        stop=stop_after_attempt(4),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def _call_model(self, messages) -> str:
        """Internal method to call the model with exponential backoff."""
        response = self.llm.invoke(messages)
        content = response.content
        if isinstance(content, list):
            text_blocks = [blk["text"] if isinstance(blk, dict) and "text" in blk else str(blk) for blk in content]
            content = "".join(text_blocks)
        return str(content)

    def generate_sql(self, question: str, schema: str) -> list:
        system_prompt = f"""You are an expert SQLite data analyst.
Your goal is to generate 3 different ways to write a valid SQLite SQL query for the user's question.
CRITICAL RULES:
- You MUST use ONLY standard SQLite syntax.
- NEVER use information_schema, pg_catalog, or any PostgreSQL-only syntax.
- NEVER hallucinate table or column names. ONLY use tables and columns that exist in the schema below.
- Use strftime('%Y', date_column) to filter by year in SQLite, NOT EXTRACT().
- Return your response as a valid JSON object with key "queries" containing exactly 3 SQL strings.
- Do NOT wrap the JSON in markdown. Return raw JSON only.

Database schema:
{schema}
"""
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=question)
        ]
        
        content = self._call_model(messages).strip()
        
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        elif content.startswith("```"):
            content = content.replace("```", "").strip()
            
        try:
            data = json.loads(content)
            queries = data.get("queries", [])
            if not queries and "sql" in data:
                queries = [data["sql"]]
            return queries
        except json.JSONDecodeError:
            return [content]

    def select_best_sql(self, question: str, variants: list) -> str:
        if not variants:
            return ""
        if len(variants) == 1:
            return variants[0]
            
        system_prompt = "You are a senior SQLite database administrator. Choose the most accurate and optimized SQLite SQL query from the list provided."
        user_message = f"""
Question: {question}

Valid SQL Variants:
{json.dumps(variants, indent=2)}

Return ONLY the raw SQL string of the best query. Do not wrap it in markdown or add explanations.
"""
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        
        content = self._call_model(messages)
        return content.replace("```sql", "").replace("```", "").strip()

    def explain_results(self, question: str, sql: str, results: list) -> str:
        system_prompt = "You are a helpful data analyst. Explain the results of a SQL query in plain, concise English."
        user_message = f"""
Original Question: {question}
SQL Executed: {sql}
Results from Database: {results}

Please provide a short answer to the original question based on these results.
"""
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        
        return self._call_model(messages).strip()

    def detect_ambiguity(self, question: str, schema: str, history: list) -> dict:
        system_prompt = f"""You are a strict data analyst. Check if the user's question is ambiguous given the schema.
RULES:
- Only flag as ambiguous if you genuinely cannot determine which table/column to use.
- If the schema clearly contains the answer, set is_ambiguous to false and let SQL generation proceed.
- Do NOT ask for clarification on things that are clearly inferrable from column names.
- You must return a JSON object with:
  "is_ambiguous": boolean
  "ambiguity_type": string (e.g. "Schema Ambiguity", "Clear")
  "clarification_question": string (A clear question for the user, or empty string if clear)

Schema:
{schema}

History of clarifications already provided:
{history}
"""
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=question)
        ]
        
        content = self._call_model(messages).strip()
        
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        elif content.startswith("```"):
            content = content.replace("```", "").strip()
            
        try:
            return json.loads(content)
        except:
            return {"is_ambiguous": False, "clarification_question": ""}
