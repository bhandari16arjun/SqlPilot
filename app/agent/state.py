from typing import TypedDict, Optional, List

class AgentState(TypedDict):
    user_question: str
    schema_context: str
    is_ambiguous: Optional[bool]
    clarification_question: Optional[str]
    conversation_history: List[str]
    sql_variants: Optional[List[str]]
    valid_sql_variants: Optional[List[str]]
    generated_sql: Optional[str]
    correction_history: List[dict]
    retry_count: int
    execution_results: Optional[List[dict]]
    final_answer: Optional[str]
    error_message: Optional[str]
    thread_id: Optional[str]
