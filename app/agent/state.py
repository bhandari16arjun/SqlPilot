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
    is_mutation: bool
    mutation_approved: bool
    error_message: Optional[str]
    retry_count: int
    execution_results: Optional[List[dict]]
    final_answer: Optional[str]
