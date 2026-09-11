import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from .base import LLMProvider

class GeminiProvider(LLMProvider):
    def __init__(self):
        # We assume GEMINI_API_KEY is loaded in the environment
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0,
            api_key=os.getenv("GEMINI_API_KEY")
        )

    def generate_sql(self, question: str, schema: str) -> str:
        system_prompt = f"""You are an expert SQL data analyst.
Your goal is to generate a PostgreSQL/SQLite compatible SQL query based on the user's question.
You must return your response as a valid JSON object with two keys: "sql" and "assumptions".
Do not return any markdown wrapping the JSON, just the raw JSON string.

Here is the database schema:
{schema}
"""
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=question)
        ]
        
        response = self.llm.invoke(messages)
        content = response.content.strip()
        
        # Clean up potential markdown formatting from the LLM
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
            
        try:
            data = json.loads(content)
            return data.get("sql", "")
        except json.JSONDecodeError:
            # Fallback if the model fails to return strictly JSON
            return content

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
        
        response = self.llm.invoke(messages)
        return response.content
