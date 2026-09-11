import sqlite3

class DatabaseExecutor:
    def __init__(self, db_path: str = "data/demo.db"):
        self.db_path = db_path

    def get_schema(self) -> str:
        """Returns a hardcoded schema string for Phase 1. 
        In Phase 2, this will be replaced by our RAG pipeline."""
        return """
        Table: customers
        Columns: id (INT), name (TEXT), email (TEXT), company (TEXT), plan_type (TEXT), signup_date (DATE), country (TEXT)
        
        Table: subscriptions
        Columns: id (INT), customer_id (INT), plan_name (TEXT), monthly_fee (DECIMAL), status (TEXT), start_date (DATE), end_date (DATE)
        
        Table: invoices
        Columns: id (INT), subscription_id (INT), amount (DECIMAL), tax (DECIMAL), discount (DECIMAL), payment_status (TEXT), issued_date (DATE), paid_date (DATE)
        """

    def execute_query(self, sql: str) -> list:
        """Execute a query and return the results as a list of dictionaries."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            results = [dict(row) for row in rows]
            conn.close()
            return results
        except Exception as e:
            # In Phase 1, we just return the error string. 
            # Phase 4 will introduce self-correction loops to fix this automatically.
            return [{"error": str(e)}]
