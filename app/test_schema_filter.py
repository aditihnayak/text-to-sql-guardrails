from schema_filter import filter_relevant_tables
from schema_introspection import TableInfo

fake_tables = [
    TableInfo(name="customers"),
    TableInfo(name="products"),
    TableInfo(name="orders"),
    TableInfo(name="order_items"),
]


def test_customer_question():
    results = filter_relevant_tables(
        "Who are our newest customers?",
        fake_tables,
        top_k=4,
        min_score=0.0,
    )

    assert results[0].table.name == "customers"


def test_product_question():
    results = filter_relevant_tables(
        "What is the most expensive product?",
        fake_tables,
        top_k=4,
        min_score=0.0,
    )

    assert results[0].table.name == "products"