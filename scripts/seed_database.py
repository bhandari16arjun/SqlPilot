import sqlite3
import os
import random
from datetime import datetime, timedelta

DB_PATH = "data/demo.db"

def setup_database():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create Tables
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            company TEXT,
            plan_type TEXT,
            signup_date DATE NOT NULL,
            country TEXT
        );

        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER REFERENCES customers(id),
            plan_name TEXT NOT NULL,
            monthly_fee DECIMAL(10,2),
            status TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE
        );

        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY,
            subscription_id INTEGER REFERENCES subscriptions(id),
            amount DECIMAL(10,2),
            tax DECIMAL(10,2),
            discount DECIMAL(10,2),
            payment_status TEXT,
            issued_date DATE NOT NULL,
            paid_date DATE
        );

        CREATE TABLE IF NOT EXISTS support_tickets (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER REFERENCES customers(id),
            subject TEXT NOT NULL,
            priority TEXT,
            status TEXT,
            created_at TIMESTAMP NOT NULL,
            resolved_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            base_price DECIMAL(10,2),
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS usage_events (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER REFERENCES customers(id),
            product_id INTEGER REFERENCES products(id),
            event_type TEXT,
            quantity INTEGER DEFAULT 1,
            timestamp TIMESTAMP NOT NULL
        );

        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT,
            role TEXT
        );
    """)

    # Dummy Data Insertion
    customers = [
        (1, 'Jack Smith', 'jack@acme.com', 'Acme Corp', 'pro', '2023-01-15', 'USA'),
        (2, 'Sarah Connor', 'sarah@skynet.com', 'Skynet', 'enterprise', '2023-03-20', 'UK'),
        (3, 'John Doe', 'john@doe.com', 'Doe LLC', 'free', '2024-01-10', 'CAN')
    ]
    cursor.executemany("INSERT OR IGNORE INTO customers VALUES (?, ?, ?, ?, ?, ?, ?)", customers)

    employees = [
        (1, 'Jack Smith', 'sales', 'manager'), # Intentional Ambiguity with customer name
        (2, 'Alice Johnson', 'engineering', 'engineer')
    ]
    cursor.executemany("INSERT OR IGNORE INTO employees VALUES (?, ?, ?, ?)", employees)
    
    subscriptions = [
        (1, 1, 'pro', 99.00, 'active', '2023-01-15', None),
        (2, 2, 'enterprise', 999.00, 'active', '2023-03-20', None),
        (3, 3, 'free', 0.00, 'active', '2024-01-10', None)
    ]
    cursor.executemany("INSERT OR IGNORE INTO subscriptions VALUES (?, ?, ?, ?, ?, ?, ?)", subscriptions)

    conn.commit()
    conn.close()
    print(f"Database seeded successfully at {DB_PATH}")

if __name__ == "__main__":
    setup_database()
