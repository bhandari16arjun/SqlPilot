import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from .base import LLMProvider

class GeminiProvider(LLMProvider):
    def __init__(self):
        # Fallback to dummy key to prevent crash on boot if environment variable is missing
        api_key = os.getenv("GEMINI_API_KEY") or "missing_key"
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash",
            temperature=0,
            google_api_key=api_key
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
        system_prompt = f"""You are an expert SQL data analyst.
Your goal is to generate 3 different ways to write a PostgreSQL/SQLite compatible SQL query for the user's question.
This helps us ensure we find the most optimized and accurate query.
You must return your response as a valid JSON object with a key "queries" that contains a list of exactly 3 SQL strings.
Do not return any markdown wrapping the JSON, just the raw JSON string.

Here is the database schema and context:
{schema}
"""
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=question)
        ]
        
        content = self._call_model(messages).strip()
        
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
            
        try:
            data = json.loads(content)
            # If the LLM didn't return a list, try to force it
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
            
        system_prompt = "You are a senior database administrator. Choose the most accurate and optimized SQL query from the list provided."
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
An ambiguous question is one where you aren't 100% sure which table/column to use, or what a term means.
You must return a JSON object with:
"is_ambiguous": boolean
"ambiguity_type": string (e.g. "Missing Time Bound", "Schema Ambiguity", "Clear")
"clarification_question": string (A multiple choice question for the user to clarify, or empty if clear)

Schema & Rules:
{schema}

History of clarifications:
{history}
"""
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=question)
        ]
        
        content = self._call_model(messages).strip()
        
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
            
        try:
            return json.loads(content)
        except:
            return {"is_ambiguous": False, "clarification_question": ""}
