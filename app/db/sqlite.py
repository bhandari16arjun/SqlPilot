import sqlite3
import threading
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

class DatabaseExecutor:
    def __init__(self, db_path: str = "data/demo.db"):
        self.db_path = db_path
        self.db_url = os.getenv("DATABASE_URL")
        
        # If running in production with PostgreSQL
        if self.db_url and self.db_url.startswith("postgres"):
            # SQLAlchemy handles connection pooling automatically
            self.engine = create_engine(self.db_url, pool_timeout=5, pool_recycle=1800)
        else:
            self.engine = None

    def execute_query(self, sql: str) -> list:
        """Execute a query in a read-only, time-limited sandbox."""
        if self.engine:
            return self._execute_postgres(sql)
        else:
            return self._execute_sqlite(sql)
            
    def _execute_postgres(self, sql: str) -> list:
        try:
            with self.engine.connect() as conn:
                # Security: Force transaction to be read-only
                conn.execute(text("SET TRANSACTION READ ONLY;"))
                # Sandbox: Kill query if it runs > 5 seconds
                conn.execute(text("SET statement_timeout = 5000;"))
                
                result = conn.execute(text(sql))
                # Prevent OOM by capping results
                rows = result.fetchmany(100)
                
                # Convert to dict for JSON serialization
                return [dict(row._mapping) for row in rows]
        except SQLAlchemyError as e:
            error_msg = str(e).lower()
            if "statement timeout" in error_msg or "canceling statement" in error_msg:
                raise RuntimeError("Query timed out after 5 seconds.") from e
            if "read-only" in error_msg:
                raise RuntimeError("Query blocked: Database is strictly read-only.") from e
            raise RuntimeError(f"Database error: {e}") from e

    def _execute_sqlite(self, sql: str) -> list:
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
            error_msg = str(e).lower()
            if "interrupted" in error_msg:
                raise RuntimeError("Query timed out after 5 seconds.") from e
            if "readonly" in error_msg or "query_only" in error_msg:
                raise RuntimeError("Query blocked: Database is strictly read-only.") from e
            raise RuntimeError(f"SQLite error: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Database error: {e}") from e
        finally:
            conn.close()
