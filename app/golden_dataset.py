from dataclasses import dataclass


@dataclass
class GoldenExample:
    question: str
    golden_sql: str
    category: str
    is_answerable: bool = True


GOLDEN_DATASET: list[GoldenExample] = [
    # --- simple lookups ---
    GoldenExample(
        question="How many customers are there?",
        golden_sql="SELECT COUNT(*) FROM customers;",
        category="simple_lookup",
    ),
    GoldenExample(
        question="What is the price of the Standing Desk?",
        golden_sql="SELECT price FROM products WHERE name = 'Standing Desk';",
        category="simple_lookup",
    ),

    # --- multi-table joins ---
    GoldenExample(
        question="How many orders has each customer placed?",
        golden_sql=(
            "SELECT c.name, COUNT(o.id) AS order_count FROM customers c "
            "LEFT JOIN orders o ON o.customer_id = c.id GROUP BY c.name;"
        ),
        category="multi_table_join",
    ),
    GoldenExample(
        question="What products has Alice Chen ordered?",
        golden_sql=(
            "SELECT p.name FROM order_items oi "
            "JOIN orders o ON o.id = oi.order_id "
            "JOIN customers c ON c.id = o.customer_id "
            "JOIN products p ON p.id = oi.product_id "
            "WHERE c.name = 'Alice Chen';"
        ),
        category="multi_table_join",
    ),

    # --- aggregations with GROUP BY ---
    GoldenExample(
        question="What is the total quantity sold for each product?",
        golden_sql=(
            "SELECT p.name, SUM(oi.quantity) AS total_sold FROM order_items oi "
            "JOIN products p ON p.id = oi.product_id GROUP BY p.name;"
        ),
        category="aggregation",
    ),
    GoldenExample(
        question="What is the average price of products in each category?",
        golden_sql="SELECT category, AVG(price) AS avg_price FROM products GROUP BY category;",
        category="aggregation",
    ),

    # --- date range filters ---
    GoldenExample(
        question="How many orders were placed in April 2024?",
        golden_sql=(
            "SELECT COUNT(*) FROM orders WHERE order_date >= '2024-04-01' AND order_date < '2024-05-01';"
        ),
        category="date_range",
    ),

    # --- ambiguous phrasing (still answerable, but tests interpretation) ---
    GoldenExample(
        question="What are our best-selling products?",
        golden_sql=(
            "SELECT p.name, SUM(oi.quantity) AS total_sold FROM order_items oi "
            "JOIN products p ON p.id = oi.product_id GROUP BY p.name ORDER BY total_sold DESC;"
        ),
        category="ambiguous",
    ),

    # --- unanswerable given this schema ---
    GoldenExample(
        question="What is the average customer satisfaction rating?",
        golden_sql="",
        category="unanswerable",
        is_answerable=False,
    ),
    GoldenExample(
        question="Which customers have unsubscribed from our newsletter?",
        golden_sql="",
        category="unanswerable",
        is_answerable=False,
    ),
]