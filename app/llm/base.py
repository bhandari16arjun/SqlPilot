from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def generate_sql(self, question: str, schema: str) -> str:
        """Generate SQL from a user question and schema."""
        pass
        
    @abstractmethod
    def explain_results(self, question: str, sql: str, results: list) -> str:
        """Explain the SQL results in plain English."""
        pass
