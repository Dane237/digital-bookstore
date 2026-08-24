#!/usr/bin/env python3
"""
PUC Digital Bookstore - Completely Empty Production Database Initializer
Resets the SQLite / PostgreSQL database to a 100% EMPTY catalog state:
 - 0 Books (Staff/Admin will input books via the Admin Portal)
 - 0 Customer Accounts (Ready for real student registrations)
 - 0 Orders
 - 1 Official Staff Admin Account (admin@puc.edu.kh / pucadmin2026)
"""

import sqlite3
import hashlib
import secrets
import os

from db_adapter import get_db

def hash_password(password, salt=None):
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
    return hashed, salt

def reset_database():
    conn = get_db()
    cursor = conn.cursor()

    # 1. Create Tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        full_name TEXT NOT NULL,
        student_id TEXT,
        role TEXT NOT NULL DEFAULT 'customer',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_code TEXT UNIQUE NOT NULL,
        course_name TEXT NOT NULL,
        department TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id TEXT PRIMARY KEY,
        isbn TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        stock INTEGER NOT NULL DEFAULT 0,
        category TEXT NOT NULL,
        course_code TEXT NOT NULL,
        department TEXT NOT NULL,
        cover_img TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id TEXT PRIMARY KEY,
        user_id INTEGER,
        customer_name TEXT NOT NULL,
        customer_email TEXT NOT NULL,
        subtotal REAL NOT NULL,
        service_fee REAL NOT NULL DEFAULT 0.50,
        total_amount REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'Paid',
        pickup_pin TEXT NOT NULL,
        payment_method TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT NOT NULL,
        book_id TEXT NOT NULL,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        course_code TEXT NOT NULL,
        unit_price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        line_total REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        expires_at DATETIME NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """)

    # 2. Seed Official Admin/Staff Account Only
    admin_pass = "pucadmin2026"
    admin_hash, admin_salt = hash_password(admin_pass)
    cursor.execute("""
    INSERT INTO users (email, password_hash, salt, full_name, student_id, role)
    VALUES (?, ?, ?, ?, ?, ?);
    """, ('admin@puc.edu.kh', admin_hash, admin_salt, 'PUC Bookstore Staff Admin', 'STAFF-001', 'staff'))

    staff_hash, staff_salt = hash_password('staffpass123')
    cursor.execute("""
    INSERT INTO users (email, password_hash, salt, full_name, student_id, role)
    VALUES (?, ?, ?, ?, ?, ?);
    """, ('staff@puc.edu.kh', staff_hash, staff_salt, 'Bookstore Manager', 'STAFF-002', 'staff'))

    # NO BOOKS ARE SEEDED. CATALOG STARTS 100% EMPTY FOR STAFF ENTRY!

    conn.commit()
    conn.close()

    print("\n Clean Production Database Initialized (100% EMPTY Catalog)!")
    print(" ------------------------------------------------------------------")
    print(" Catalog State: EMPTY (0 books) -> Ready for Staff Admin input")
    print(" Staff Admin Account: admin@puc.edu.kh  /  pucadmin2026")
    print(" Staff Manager Account: staff@puc.edu.kh /  staffpass123")
    print(" Customer Accounts: 0 (Ready for real student registrations)")
    print(" ------------------------------------------------------------------\n")

if __name__ == '__main__':
    reset_database()
