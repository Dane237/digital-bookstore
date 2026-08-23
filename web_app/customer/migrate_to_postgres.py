#!/usr/bin/env python3
"""
PUC Digital Bookstore - SQLite to PostgreSQL Database Migration Tool
Reads data from local 'puc_bookstore.db' and populates a PostgreSQL target database.

Usage:
  python migrate_to_postgres.py "postgresql://user:password@localhost:5432/puc_bookstore"
"""

import sys
import os
import sqlite3

def migrate(pg_url):
    try:
        import psycopg2
    except ImportError:
        print("[ERROR] 'psycopg2' library is required for PostgreSQL migration.")
        print("Install it by running:  pip install psycopg2-binary")
        sys.exit(1)

    sqlite_db_path = 'puc_bookstore.db'
    if not os.path.exists(sqlite_db_path):
        print(f"[ERROR] SQLite database '{sqlite_db_path}' not found. Run 'python init_db.py' first.")
        sys.exit(1)

    print(f" Connecting to SQLite source ({sqlite_db_path})...")
    s_conn = sqlite3.connect(sqlite_db_path)
    s_conn.row_factory = sqlite3.Row
    s_cur = s_conn.cursor()

    print(f" Connecting to PostgreSQL target database...")
    pg_conn = psycopg2.connect(pg_url)
    pg_cur = pg_conn.cursor()

    # 1. Create PostgreSQL Schema
    print(" Creating PostgreSQL Tables Schema...")
    
    pg_cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        full_name TEXT NOT NULL,
        student_id TEXT,
        role VARCHAR(50) NOT NULL DEFAULT 'customer',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS courses (
        id SERIAL PRIMARY KEY,
        course_code VARCHAR(50) UNIQUE NOT NULL,
        course_name TEXT NOT NULL,
        department TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS books (
        id VARCHAR(100) PRIMARY KEY,
        isbn VARCHAR(50) UNIQUE NOT NULL,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        description TEXT,
        price NUMERIC(10,2) NOT NULL,
        stock INTEGER NOT NULL DEFAULT 0,
        category VARCHAR(100) NOT NULL,
        course_code VARCHAR(50) NOT NULL,
        department VARCHAR(100) NOT NULL,
        cover_img TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS orders (
        id VARCHAR(100) PRIMARY KEY,
        user_id INTEGER,
        customer_name TEXT NOT NULL,
        customer_email TEXT NOT NULL,
        subtotal NUMERIC(10,2) NOT NULL,
        service_fee NUMERIC(10,2) NOT NULL DEFAULT 0.50,
        total_amount NUMERIC(10,2) NOT NULL,
        status VARCHAR(50) NOT NULL DEFAULT 'Paid',
        pickup_pin VARCHAR(20) NOT NULL,
        payment_method TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS order_items (
        id SERIAL PRIMARY KEY,
        order_id VARCHAR(100) NOT NULL,
        book_id VARCHAR(100) NOT NULL,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        course_code VARCHAR(50) NOT NULL,
        unit_price NUMERIC(10,2) NOT NULL,
        quantity INTEGER NOT NULL,
        line_total NUMERIC(10,2) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS sessions (
        token VARCHAR(255) PRIMARY KEY,
        user_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL
    );
    """)

    pg_conn.commit()
    print(" PostgreSQL Schema Created Successfully!")

    # 2. Transfer Data from SQLite to PostgreSQL
    tables = ['users', 'courses', 'books', 'orders', 'order_items', 'sessions']
    
    for table in tables:
        s_cur.execute(f"SELECT * FROM {table};")
        rows = [dict(r) for r in s_cur.fetchall()]
        if not rows:
            print(f"  └ Table '{table}' is empty, skipping.")
            continue

        columns = list(rows[0].keys())
        cols_str = ", ".join(columns)
        vals_str = ", ".join(["%s"] * len(columns))

        query = f"INSERT INTO {table} ({cols_str}) VALUES ({vals_str}) ON CONFLICT DO NOTHING;"
        data_tuples = [tuple(r[c] for c in columns) for r in rows]

        pg_cur.executemany(query, data_tuples)
        pg_conn.commit()
        print(f"  └ Migrated {len(rows)} records into PostgreSQL table '{table}'")

    s_conn.close()
    pg_conn.close()

    print("\n MIGRATION COMPLETE! All SQLite data successfully exported to PostgreSQL database!")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    else:
        target_url = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')

    if not target_url:
        print("PUC Digital Bookstore - PostgreSQL Migration Utility")
        print("\nError: Please provide a target PostgreSQL URL.")
        print("Usage:")
        print("  python migrate_to_postgres.py \"postgresql://user:password@localhost:5432/puc_bookstore\"")
        print("  or set environment variable DATABASE_URL=\"postgresql://...\"")
        sys.exit(1)

    migrate(target_url)
