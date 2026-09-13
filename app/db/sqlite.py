import sqlite3

class DatabaseExecutor:
    def __init__(self, db_path: str = "data/demo.db"):
        self.db_path = db_path

    def execute_query(self, sql: str) -> list:
        """Execute a query and return the results. Raises Exception on failure."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # SECURITY: Enforce read-only at the database engine level!
            cursor.execute("PRAGMA query_only = ON;")
            
            cursor.execute(sql)
            rows = cursor.fetchall()
            results = [dict(row) for row in rows]
            return results
        finally:
            conn.close()
