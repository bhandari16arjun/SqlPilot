import sqlglot
from sqlglot.errors import ParseError

def validate_sql(sql: str) -> str:
    """
    Parses SQL with SQLGlot.
    Returns an error message if invalid or unsafe.
    Returns None if valid and safe.
    """
    try:
        # Parse it as SQLite to catch syntax errors
        expressions = sqlglot.parse(sql, read="sqlite")
        
        if not expressions or not expressions[0]:
            return "No valid SQL statement found."
            
        for expr in expressions:
            if expr is None:
                continue
            
            # Security Blocklist: STRICTLY ONLY allow SELECT statements.
            # Reject all mutations (INSERT, UPDATE, DELETE) and DDL (DROP, ALTER).
            if not isinstance(expr, sqlglot.exp.Select):
                return f"UNSAFE OR UNSUPPORTED QUERY TYPE. Only SELECT statements are allowed. Found: {expr.key}"
                
        return None
        
    except ParseError as e:
        return f"SYNTAX ERROR: {str(e)}"
    except Exception as e:
        return f"VALIDATION ERROR: {str(e)}"
