import sqlite3
import threading

class DatabaseExecutor:
    def __init__(self, db_path: str = "data/demo.db"):
        self.db_path = db_path

    def execute_query(self, sql: str) -> list:
        """Execute a query in a read-only, time-limited sandbox."""
        conn = sqlite3.connect(self.db_path, timeout=5)
        conn.row_factory = sqlite3.Row
        
        try:
            # SECURITY: Enforce read-only at the database engine level
            conn.execute("PRAGMA query_only = ON;")
            
            # Timeout sandbox: kill query if it runs > 5 seconds
            timer = threading.Timer(5.0, conn.interrupt)
            timer.start()
            
            try:
                cursor = conn.cursor()
                cursor.execute(sql)
                # Prevent OOM crashes by capping result size
                rows = cursor.fetchmany(100)
            finally:
                timer.cancel()
                
            results = [dict(row) for row in rows]
            return results
        except sqlite3.OperationalError as e:
            error_msg = str(e)
            if "interrupted" in error_msg.lower():
                raise RuntimeError("Query timed out after 5 seconds.") from e
            if "readonly" in error_msg.lower() or "query_only" in error_msg.lower():
                raise RuntimeError("Query blocked: Database is strictly read-only.") from e
            raise RuntimeError(f"SQLite error: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Database error: {e}") from e
        finally:
            conn.close()
