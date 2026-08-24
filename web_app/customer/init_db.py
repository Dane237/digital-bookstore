#!/usr/bin/env python3
"""
PUC Digital Bookstore - Database Initialization & Seed Script
Creates SQLite database schema aligned with mobile customer schema and seeds initial departments & course textbooks.
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
    return f"{salt}:{hashed}"

def verify_password(password, stored_pass):
    try:
        salt, stored_hash = stored_pass.split(":")
        computed_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
        return computed_hash == stored_hash
    except Exception:
        return False

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # 1. USERS Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role VARCHAR(20) NOT NULL DEFAULT 'Customer' CHECK (role IN ('Customer', 'Staff', 'Admin')),
        employee_id VARCHAR(50) DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. BOOKS Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        book_id INTEGER PRIMARY KEY AUTOINCREMENT,
        isbn VARCHAR(20) UNIQUE NOT NULL,
        title VARCHAR(255) NOT NULL,
        author VARCHAR(255),
        price DECIMAL(10, 2) NOT NULL,
        stock_quantity INT NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        description TEXT,
        cover_img VARCHAR(500)
    );
    """)

    # 3. DEPARTMENTS Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS departments (
        department_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) UNIQUE NOT NULL
    );
    """)

    # 4. BOOK_DEPARTMENTS Bridge Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS book_departments (
        book_id INT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
        department_id INT NOT NULL REFERENCES departments(department_id) ON DELETE CASCADE,
        PRIMARY KEY (book_id, department_id)
    );
    """)

    # 5. ORDERS Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INT NOT NULL REFERENCES users(user_id),
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status VARCHAR(20) NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending', 'Ready for Pickup', 'Picked Up', 'Cancelled')),
        total_amount DECIMAL(10, 2) NOT NULL,
        payment_method VARCHAR(50),
        stripe_payment_id VARCHAR(255),
        pickup_pin VARCHAR(10) NOT NULL,
        prepared_location VARCHAR(255),
        prepared_by_staff_id INT DEFAULT NULL REFERENCES users(user_id),
        released_by_staff_id INT DEFAULT NULL REFERENCES users(user_id),
        picked_up_at TIMESTAMP
    );
    """)

    # 6. ORDER_ITEMS Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
        book_id INT NOT NULL REFERENCES books(book_id),
        quantity INT NOT NULL,
        unit_price DECIMAL(10, 2) NOT NULL
    );
    """)

    # 7. CART_ITEMS Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cart_items (
        cart_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        book_id INT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
        quantity INT NOT NULL DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Seed Departments
    depts = [
        'Computer Science & Tech',
        'Business & Economics',
        'Law & Public Affairs',
        'Arts & Humanities',
        'Information Technology'
    ]
    for dname in depts:
        cursor.execute("INSERT OR IGNORE INTO departments (name) VALUES (?);", (dname,))

    # Seed Books & Link Departments
    books_data = [
        {
            "isbn": "978-0133943030",
            "title": "Software Engineering",
            "author": "Ian Sommerville",
            "price": 18.00,
            "stock_quantity": 15,
            "dept": "Computer Science & Tech",
            "cover": "https://images.unsplash.com/photo-1532012197267-da84d127e765?auto=format&fit=crop&w=400&q=80",
            "description": "Primary course textbook covering modern software methodologies, software planning, system architecture, agile development, testing, and project management practices at PUC."
        },
        {
            "isbn": "978-0078022159",
            "title": "Database System Concepts",
            "author": "Abraham Silberschatz, Henry F. Korth",
            "price": 22.50,
            "stock_quantity": 10,
            "dept": "Computer Science & Tech",
            "cover": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=400&q=80",
            "description": "Comprehensive introduction to database design, relational algebra, SQL optimization, transaction management, and database application architecture."
        },
        {
            "isbn": "978-1305971493",
            "title": "Principles of Microeconomics",
            "author": "N. Gregory Mankiw",
            "price": 19.99,
            "stock_quantity": 12,
            "dept": "Business & Economics",
            "cover": "https://images.unsplash.com/photo-1554415707-6e8cfc93fe23?auto=format&fit=crop&w=400&q=80",
            "description": "Fundamental principles of microeconomics, market supply and demand, competitive pricing models, trade policy, and consumer welfare."
        },
        {
            "isbn": "978-9995001234",
            "title": "Introduction to Cambodian Law",
            "author": "Khemra Hor & PUC Legal Faculty",
            "price": 15.00,
            "stock_quantity": 20,
            "dept": "Law & Public Affairs",
            "cover": "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?auto=format&fit=crop&w=400&q=80",
            "description": "Essential legal reference text covering the constitutional system, civil law code, judicial system structure, and administrative law in Cambodia."
        },
        {
            "isbn": "978-0472034758",
            "title": "Academic Writing & Research Methods",
            "author": "John M. Swales & Christine B. Feak",
            "price": 14.50,
            "stock_quantity": 18,
            "dept": "Arts & Humanities",
            "cover": "https://images.unsplash.com/photo-1455390582262-044cdead277a?auto=format&fit=crop&w=400&q=80",
            "description": "Comprehensive handbook on academic thesis writing, research question formulation, literature review synthesis, and APA citation standards."
        },
        {
            "isbn": "978-0133594140",
            "title": "Computer Networking: A Top-Down Approach",
            "author": "James Kurose & Keith Ross",
            "price": 24.00,
            "stock_quantity": 8,
            "dept": "Information Technology",
            "cover": "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?auto=format&fit=crop&w=400&q=80",
            "description": "In-depth exploration of network architecture layer by layer, covering HTTP/HTTPS protocols, TCP/UDP sockets, IP routing, wireless networks, and cybersecurity principles."
        }
    ]

    for b in books_data:
        cursor.execute("""
        INSERT INTO books (isbn, title, author, price, stock_quantity, description, cover_img)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(isbn) DO UPDATE SET
            title=excluded.title, author=excluded.author, price=excluded.price,
            stock_quantity=excluded.stock_quantity, description=excluded.description, cover_img=excluded.cover_img;
        """, (b["isbn"], b["title"], b["author"], b["price"], b["stock_quantity"], b["description"], b["cover"]))
        
        cursor.execute("SELECT book_id FROM books WHERE isbn = ?;", (b["isbn"],))
        brow = cursor.fetchone()
        bid = brow['book_id'] if isinstance(brow, dict) else (brow[0] if brow else 1)

        cursor.execute("SELECT department_id FROM departments WHERE name = ?;", (b["dept"],))
        dept_row = cursor.fetchone()
        if dept_row:
            did = dept_row['department_id'] if isinstance(dept_row, dict) else dept_row[0]
            cursor.execute("INSERT INTO book_departments (book_id, department_id) VALUES (?, ?) ON CONFLICT DO NOTHING;", (bid, did))

    # Seed Default Student Account
    dara_hash = hash_password("student123")
    cursor.execute("""
    INSERT INTO users (username, email, password_hash, role)
    VALUES (?, ?, ?, 'Customer')
    ON CONFLICT (email) DO NOTHING;
    """, ('Dara Sok', 'dara.sok@student.puc.edu.kh', dara_hash))

    conn.commit()
    conn.close()
    print("[OK] Customer Database initialized and seeded successfully!")

if __name__ == "__main__":
    init_db()
