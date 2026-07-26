FEW_SHOT_EXAMPLES = [
    {
        "question": "How many customers do we have?",
        "sql": "SELECT COUNT(*) FROM customers;",
    },
    {
        "question": "What are the 5 most expensive products?",
        "sql": "SELECT name, price FROM products ORDER BY price DESC LIMIT 5;",
    },
    {
        "question": "How many orders has each customer placed?",
        "sql": (
            "SELECT c.name, COUNT(o.id) AS order_count "
            "FROM customers c "
            "LEFT JOIN orders o ON o.customer_id = c.id "
            "GROUP BY c.name;"
        ),
    },
    {
        "question": "What is the total quantity of each product sold in completed orders?",
        "sql": (
            "SELECT p.name, SUM(oi.quantity) AS total_sold "
            "FROM order_items oi "
            "JOIN products p ON p.id = oi.product_id "
            "JOIN orders o ON o.id = oi.order_id "
            "WHERE o.status = 'completed' "
            "GROUP BY p.name;"
        ),
    },
]