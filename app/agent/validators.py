import sqlglot
from sqlglot.errors import ParseError

def validate_sql(sql: str) -> tuple:
    """
    Parses SQL with SQLGlot.
    Returns (error_message, is_mutation).
    If error_message is None, the query is valid and safe.
    is_mutation is True if the query is an INSERT, UPDATE, or DELETE.
    """
    try:
        # Parse it as SQLite to catch syntax errors
        expressions = sqlglot.parse(sql, read="sqlite")
        
        if not expressions or not expressions[0]:
            return ("No valid SQL statement found.", False)
            
        is_mutation = False
        for expr in expressions:
            if expr is None:
                continue
            
            # Security Blocklist: Allow SELECT, INSERT, UPDATE, DELETE. Block DROP, ALTER, etc.
            if isinstance(expr, (sqlglot.exp.Insert, sqlglot.exp.Update, sqlglot.exp.Delete)):
                is_mutation = True
            elif not isinstance(expr, sqlglot.exp.Select):
                return (f"UNSAFE OR UNSUPPORTED QUERY TYPE. Found: {expr.key}. Only SELECT, INSERT, UPDATE, DELETE are allowed.", False)
                
        return (None, is_mutation)
        
    except ParseError as e:
        return (f"SYNTAX ERROR: {str(e)}", False)
    except Exception as e:
        return (f"VALIDATION ERROR: {str(e)}", False)
