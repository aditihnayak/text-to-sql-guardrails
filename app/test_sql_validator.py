import pytest
from sql_validator import validate_sql


@pytest.mark.parametrize("sql,expected_valid", [
    ("SELECT * FROM customers;", True),
    ("DROP TABLE customers;", False),
    ("DELETE FROM customers WHERE id=1;", False),
    ("SELECT * FROM customers; DROP TABLE customers;", False),
    ("SELECT * FROM customers WHERE id = 1 OR 1=1;", True),
    ("INSERT INTO customers (name) VALUES ('x'); SELECT 1;", False),
    ("SELECT * FROM (SELECT * FROM (SELECT * FROM (SELECT * FROM (SELECT * FROM customers))));", False),
    ("  ; SELECT * FROM customers;", True),
    ("SELECT * FROM customers;  ;  ", True),
    ("", False),
    ("   ", False),
])
def test_validate_sql(sql, expected_valid):
    result = validate_sql(sql)
    assert result.is_valid == expected_valid, f"reason={result.reason}"