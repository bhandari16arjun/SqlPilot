import pytest
from app.agent.validators import validate_sql

def test_plain_select_is_valid():
    assert validate_sql("SELECT id, name FROM customers LIMIT 10") is None

def test_cte_and_join_are_valid():
    sql = """
    WITH active AS (
        SELECT id FROM subscriptions WHERE active = 1
    )
    SELECT c.name FROM customers c JOIN active a ON a.id = c.id
    """
    assert validate_sql(sql) is None

def test_empty_sql_is_invalid():
    assert validate_sql("   ") == "No valid SQL statement found."

@pytest.mark.parametrize("sql", [
    "DROP TABLE customers",
    "DELETE FROM customers WHERE id = 1",
    "INSERT INTO customers (name) VALUES ('x')",
    "UPDATE customers SET name = 'x'",
    "ALTER TABLE customers ADD COLUMN x TEXT",
    "TRUNCATE TABLE customers",
    "GRANT ALL ON customers TO public",
])
def test_mutations_are_blocked(sql):
    error = validate_sql(sql)
    assert error is not None
    assert "UNSAFE" in error
    assert "Only SELECT" in error

def test_syntax_error():
    error = validate_sql("SELECT FROM WHERE customers")
    assert error is not None
    assert "SYNTAX ERROR" in error
