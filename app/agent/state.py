from typing import TypedDict, Optional, List, Any

class AgentState(TypedDict):
    user_question: str
    schema_context: str
    generated_sql: Optional[str]
    execution_results: Optional[List[dict]]
    final_answer: Optional[str]
