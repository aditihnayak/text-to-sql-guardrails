-- db/init/01_schema.sql

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    signup_date DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    category VARCHAR(50) NOT NULL,
    price NUMERIC(10, 2) NOT NULL
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    order_date DATE NOT NULL DEFAULT CURRENT_DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0)
);

-- Sample data
INSERT INTO customers (name, email, signup_date) VALUES
    ('Alice Chen', 'alice@example.com', '2024-01-15'),
    ('Bob Martinez', 'bob@example.com', '2024-02-20'),
    ('Priya Rao', 'priya@example.com', '2024-03-01');

INSERT INTO products (name, category, price) VALUES
    ('Wireless Mouse', 'Electronics', 24.99),
    ('Standing Desk', 'Furniture', 349.00),
    ('Notebook Pack', 'Office Supplies', 8.50);

INSERT INTO orders (customer_id, order_date, status) VALUES
    (1, '2024-04-01', 'completed'),
    (2, '2024-04-03', 'completed'),
    (1, '2024-04-10', 'pending');

INSERT INTO order_items (order_id, product_id, quantity) VALUES
    (1, 1, 2),
    (1, 3, 1),
    (2, 2, 1),
    (3, 1, 1);