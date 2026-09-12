from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def generate_sql(self, question: str, schema: str) -> list:
        """Generate multiple SQL variants from a user question and schema."""
        pass

    @abstractmethod
    def select_best_sql(self, question: str, variants: list) -> str:
        """Act as a judge to pick the best SQL from valid variants."""
        pass
        
    @abstractmethod
    def explain_results(self, question: str, sql: str, results: list) -> str:
        """Explain the SQL results in plain English."""
        pass

    @abstractmethod
    def detect_ambiguity(self, question: str, schema: str, history: list) -> dict:
        """Detect if the user question is ambiguous."""
        pass
