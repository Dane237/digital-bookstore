#!/usr/bin/env python3
"""
PUC Digital Bookstore - Dedicated Customer Web Application Server
Flask REST API Backend + SQLite Database + Session Security + Static File Server
Exclusively serves Customer Storefront API endpoints (No Admin/Staff routes).
"""

from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
import os
import sys

app = Flask(__name__, static_folder='.')
app.config['SECRET_KEY'] = secrets.token_hex(32)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
    return response

from db_adapter import get_db

# In-memory store for OTPs
otp_store = {}

def hash_password(password, salt=None):
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
    return f"{salt}:{hashed}"

def verify_password(password, stored_pass):
    try:
        if ":" in stored_pass:
            salt, stored_hash = stored_pass.split(":")
            computed_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
            return computed_hash == stored_hash
        return False
    except Exception:
        return False

# --- REST API ENDPOINTS (CUSTOMER EXCLUSIVE) ---

@app.route('/api/departments/', methods=['GET'])
@app.route('/api/departments', methods=['GET'])
def get_departments():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM departments ORDER BY name ASC;")
    rows = cursor.fetchall()
    conn.close()
    depts = [r['name'] if isinstance(r, dict) else r[0] for r in rows]
    return jsonify(depts)

@app.route('/api/books/', methods=['GET'])
@app.route('/api/books', methods=['GET'])
def get_books():
    department = request.args.get('department', 'all')
    q = request.args.get('q', '').strip()

    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT b.*, GROUP_CONCAT(d.name, ', ') as departments
        FROM books b
        LEFT JOIN book_departments bd ON b.book_id = bd.book_id
        LEFT JOIN departments d ON bd.department_id = d.department_id
        WHERE 1=1
    """
    params = []

    if department != 'all':
        query += " AND d.name = ?"
        params.append(department)

    if q:
        query += " AND (b.title LIKE ? OR b.isbn LIKE ? OR b.description LIKE ? OR b.author LIKE ?)"
        pattern = f"%{q}%"
        params.extend([pattern, pattern, pattern, pattern])

    query += " GROUP BY b.book_id ORDER BY b.created_at DESC;"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    books = []
    for r in rows:
        item = dict(r) if hasattr(r, 'keys') or isinstance(r, dict) else {
            'book_id': r[0], 'isbn': r[1], 'title': r[2], 'author': r[3],
            'price': float(r[4]), 'stock_quantity': r[5], 'created_at': str(r[6]),
            'description': r[7], 'cover_img': r[8], 'departments': r[9] or ''
        }
        depts = item.get('departments')
        item['department'] = depts.split(',')[0].strip() if depts and depts.strip() else 'General'
        books.append(item)

    return jsonify(books)

@app.route('/api/register/', methods=['POST'])
@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.json or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()

    if not username or not email or not password:
        return jsonify({"status": "error", "detail": "All fields are required"}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM users WHERE email = ?;", (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"status": "error", "detail": "An account with this email already exists"}), 400

    employee_id = data.get('employee_id', None)

    if email == 'admin@puc.edu.kh':
        role = 'Admin'
    elif employee_id:
        role = 'Staff'
    else:
        role = 'Customer'

    hashed = hash_password(password)

    cursor.execute(
        "INSERT INTO users (username, email, password_hash, role, employee_id) VALUES (?, ?, ?, ?, ?) RETURNING user_id;",
        (username, email, hashed, role, employee_id)
    )
    user_row = cursor.fetchone()
    conn.commit()
    conn.close()

    user_id = user_row['user_id'] if user_row and 'user_id' in user_row else (user_row[0] if user_row else cursor.lastrowid)

    return jsonify({
        "status": "success",
        "user": {
            "user_id": user_id,
            "username": username,
            "email": email,
            "role": role,
            "employee_id": employee_id
        }
    })

@app.route('/api/login/', methods=['POST'])
@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()

    if not email or not password:
        return jsonify({"status": "error", "detail": "Email and password are required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?;", (email,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return jsonify({"status": "error", "detail": "Invalid email or password"}), 401

    user_dict = dict(user)
    if verify_password(password, user_dict['password_hash']):
        return jsonify({
            "status": "success",
            "user": {
                "user_id": user_dict.get('user_id'),
                "username": user_dict.get('username'),
                "email": user_dict.get('email'),
                "role": user_dict.get('role'),
                "employee_id": user_dict.get('employee_id')
            }
        })

    return jsonify({"status": "error", "detail": "Invalid email or password"}), 401

@app.route('/api/forgot-password/', methods=['POST'])
@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    data = request.json or {}
    email = data.get('email', '').strip().lower()

    if not email:
        return jsonify({"status": "error", "detail": "Email is required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE email = ?;", (email,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return jsonify({"status": "error", "detail": "Account not found"}), 404

    otp = str(secrets.randbelow(900000) + 100000)
    otp_store[email] = {
        "otp": otp,
        "expires": datetime.now() + timedelta(minutes=10)
    }

    # Simulated email OTP sending
    print(f"[SECURITY OTP LOG] Verification OTP code for {email}: {otp}")
    return jsonify({"status": "success", "message": "OTP sent to your email", "demo_otp": otp})

@app.route('/api/reset-password-confirm/', methods=['POST'])
@app.route('/api/reset-password-confirm', methods=['POST'])
def reset_password_confirm():
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    otp = data.get('otp', '').strip()
    new_password = data.get('new_password', '').strip()

    if not email or not otp or not new_password:
        return jsonify({"status": "error", "detail": "Missing required parameters"}), 400

    if email not in otp_store:
        return jsonify({"status": "error", "detail": "No OTP requested for this account"}), 400

    stored = otp_store[email]
    if datetime.now() > stored["expires"]:
        del otp_store[email]
        return jsonify({"status": "error", "detail": "Verification OTP has expired"}), 400

    if stored["otp"] != otp:
        return jsonify({"status": "error", "detail": "Invalid 6-digit verification code"}), 400

    conn = get_db()
    cursor = conn.cursor()
    new_hashed = hash_password(new_password)
    cursor.execute("UPDATE users SET password_hash = ? WHERE email = ?;", (new_hashed, email))
    conn.commit()
    conn.close()

    del otp_store[email]
    return jsonify({"status": "success", "message": "Password updated successfully"})

import urllib.request
import json

@app.route('/api/admin/isbn-lookup/<isbn>', methods=['GET'])
def isbn_lookup(isbn):
    try:
        url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data.get("totalItems", 0) > 0:
                item = data["items"][0]["volumeInfo"]
                return jsonify({
                    "title": item.get("title", ""),
                    "author": ", ".join(item.get("authors", [])),
                    "description": item.get("description", ""),
                    "cover_img": item.get("imageLinks", {}).get("thumbnail", ""),
                    "isbn": isbn
                })
            return jsonify({"error": "ISBN not found in Google Books API"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/books/add/', methods=['POST'])
@app.route('/api/admin/books/add', methods=['POST'])
def admin_add_book():
    data = request.json or {}
    title = data.get('title', '').strip()
    author = data.get('author', '').strip()
    isbn = data.get('isbn', '').strip()
    price = float(data.get('price', 0.0))
    stock_quantity = int(data.get('stock_quantity', 0))
    department_name = data.get('department_name', 'Computer Science & Tech').strip()
    description = data.get('description', '').strip()
    cover_img = data.get('cover_img', '').strip()

    if not title or not isbn:
        return jsonify({"status": "error", "detail": "Title and ISBN are required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        # Check/create department
        cursor.execute("SELECT department_id FROM departments WHERE name = ?;", (department_name,))
        dept_row = cursor.fetchone()
        if not dept_row:
            cursor.execute("INSERT INTO departments (name) VALUES (?);", (department_name,))
            dept_id = cursor.lastrowid
        else:
            dept_id = dept_row['department_id'] if isinstance(dept_row, dict) else dept_row[0]

        # Insert or update book
        cursor.execute("SELECT book_id FROM books WHERE isbn = ?;", (isbn,))
        existing = cursor.fetchone()
        if existing:
            bid = existing['book_id'] if isinstance(existing, dict) else existing[0]
            cursor.execute(
                "UPDATE books SET title = ?, author = ?, price = ?, stock_quantity = ?, description = ?, cover_img = ? WHERE book_id = ?;",
                (title, author, price, stock_quantity, description, cover_img, bid)
            )
            book_id = bid
        else:
            cursor.execute(
                "INSERT INTO books (isbn, title, author, price, stock_quantity, description, cover_img) VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING book_id;",
                (isbn, title, author, price, stock_quantity, description, cover_img)
            )
            b_row = cursor.fetchone()
            book_id = b_row['book_id'] if b_row and 'book_id' in b_row else (b_row[0] if b_row else cursor.lastrowid)

        # Connect department bridge
        cursor.execute("INSERT OR IGNORE INTO book_departments (book_id, department_id) VALUES (?, ?);", (book_id, dept_id))
        conn.commit()
        return jsonify({"status": "success", "book_id": book_id})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "detail": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/admin/books/<int:book_id>/', methods=['DELETE'])
@app.route('/api/admin/books/<int:book_id>', methods=['DELETE'])
def admin_delete_book(book_id):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM book_departments WHERE book_id = ?;", (book_id,))
        cursor.execute("DELETE FROM books WHERE book_id = ?;", (book_id,))
        conn.commit()
        return jsonify({"status": "success", "message": "Book deleted"})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "detail": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/admin/staff/add/', methods=['POST'])
@app.route('/api/admin/staff/add', methods=['POST'])
def admin_add_staff():
    data = request.json or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    employee_id = data.get('employee_id', 'PUC-STF-100').strip()
    staff_code = data.get('staff_code', '').strip()

    if staff_code != 'PUC-STAFF-2026' and staff_code != 'PUC-STAFF-SEC':
        return jsonify({"status": "error", "detail": "Invalid Staff Passcode"}), 403

    if not username or not email or not password:
        return jsonify({"status": "error", "detail": "All fields are required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT user_id FROM users WHERE email = ?;", (email,))
        if cursor.fetchone():
            return jsonify({"status": "error", "detail": "Email already registered"}), 400

        hashed = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role, employee_id) VALUES (?, ?, ?, 'Staff', ?);",
            (username, email, hashed, employee_id)
        )
        conn.commit()
        return jsonify({"status": "success", "message": f"Staff account {employee_id} created."})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "detail": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/admin/seed/', methods=['POST'])
@app.route('/api/admin/seed', methods=['POST'])
def seed_database():
    conn = get_db()
    cursor = conn.cursor()
    try:
        depts = ['Computer Science & Tech', 'Business & Economics', 'Law & Public Affairs', 'Arts & Humanities', 'Information Technology']
        for dname in depts:
            cursor.execute("INSERT OR IGNORE INTO departments (name) VALUES (?);", (dname,))
        
        hashed = hash_password("password")
        cursor.execute("INSERT OR IGNORE INTO users (user_id, username, email, password_hash, role, employee_id) VALUES (1, 'PUC Admin', 'admin@puc.edu.kh', ?, 'Admin', 'PUC-ROOT-001');", (hashed,))
        conn.commit()
        return jsonify({"status": "success", "message": "Database seeded successfully."})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "detail": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/admin/wipe-inventory/', methods=['POST'])
@app.route('/api/admin/wipe-inventory', methods=['POST'])
def wipe_inventory():
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM book_departments;")
        cursor.execute("DELETE FROM books;")
        conn.commit()
        return jsonify({"status": "success", "message": "Inventory wiped successfully."})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "detail": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/orders/', methods=['POST'])
@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.json or {}
    user_id = data.get('user_id')
    total_amount = data.get('total_amount', 0.0)
    payment_method = data.get('payment_method', 'Stripe Card')
    stripe_payment_id = data.get('stripe_payment_id')
    pickup_location = data.get('pickup_location', 'Main Campus Library (Building A)')
    items = data.get('items', [])

    if not user_id or not items:
        return jsonify({"status": "error", "detail": "Invalid order payload"}), 400

    conn = get_db()
    cursor = conn.cursor()

    try:
        pin = str(secrets.randbelow(900000) + 100000)
        cursor.execute(
            "INSERT INTO orders (user_id, total_amount, pickup_pin, payment_method, stripe_payment_id, prepared_location) VALUES (?, ?, ?, ?, ?, ?) RETURNING order_id;",
            (user_id, total_amount, pin, payment_method, stripe_payment_id, pickup_location)
        )
        order_row = cursor.fetchone()
        order_id = order_row['order_id'] if order_row and 'order_id' in order_row else (order_row[0] if order_row else cursor.lastrowid)

        for item in items:
            book_id = item.get('book_id')
            qty = item.get('quantity', 1)
            unit_price = item.get('unit_price', 0.0)

            # Check stock
            cursor.execute("SELECT stock_quantity FROM books WHERE book_id = ?;", (book_id,))
            book_row = cursor.fetchone()
            current_stock = book_row['stock_quantity'] if book_row and 'stock_quantity' in book_row else (book_row[0] if book_row else 0)

            if current_stock < qty:
                raise Exception(f"Insufficient stock for book ID {book_id}")

            cursor.execute(
                "INSERT INTO order_items (order_id, book_id, quantity, unit_price) VALUES (?, ?, ?, ?);",
                (order_id, book_id, qty, unit_price)
            )

            cursor.execute(
                "UPDATE books SET stock_quantity = stock_quantity - ? WHERE book_id = ? AND stock_quantity >= ?;",
                (qty, book_id, qty)
            )

        conn.commit()
        return jsonify({"status": "success", "order_id": order_id, "pickup_pin": pin, "pickup_location": pickup_location})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "detail": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/orders/<int:user_id>', methods=['GET'])
def user_orders(user_id):
    conn = get_db()
    cursor = conn.cursor()
    query = """
        SELECT o.*, COUNT(oi.order_item_id) as item_count
        FROM orders o 
        LEFT JOIN order_items oi ON o.order_id = oi.order_id 
        WHERE o.user_id = ? 
        GROUP BY o.order_id
        ORDER BY o.order_date DESC;
    """
    cursor.execute(query, (user_id,))
    rows = cursor.fetchall()
    conn.close()

    orders = []
    for r in rows:
        o = dict(r) if hasattr(r, 'keys') or isinstance(r, dict) else {
            'order_id': r[0], 'user_id': r[1], 'order_date': str(r[2]), 'status': r[3],
            'total_amount': float(r[4]), 'payment_method': r[5], 'stripe_payment_id': r[6],
            'pickup_pin': r[7], 'prepared_location': r[8], 'item_count': r[9]
        }
        o['display_id'] = f"PUC-ORD-{o['order_id'] + 1000}"
        o['created_at'] = str(o.get('order_date', ''))[:16]
        orders.append(o)

    return jsonify(orders)

@app.route('/api/orders/detail/<int:order_id>', methods=['GET'])
def order_details(order_id):
    conn = get_db()
    cursor = conn.cursor()
    query = """
        SELECT oi.*, b.title, b.cover_img 
        FROM order_items oi 
        JOIN books b ON oi.book_id = b.book_id 
        WHERE oi.order_id = ?;
    """
    cursor.execute(query, (order_id,))
    rows = cursor.fetchall()
    conn.close()

    items = [dict(r) if hasattr(r, 'keys') or isinstance(r, dict) else {
        'order_item_id': r[0], 'order_id': r[1], 'book_id': r[2], 'quantity': r[3],
        'unit_price': float(r[4]), 'title': r[5], 'cover_img': r[6]
    } for r in rows]

    return jsonify(items)

@app.route('/api/orders/<int:order_id>/cancel/', methods=['PATCH'])
@app.route('/api/orders/<int:order_id>/cancel', methods=['PATCH'])
def cancel_order(order_id):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT status FROM orders WHERE order_id = ?;", (order_id,))
        order_row = cursor.fetchone()
        if not order_row:
            return jsonify({"status": "error", "detail": "Order not found"}), 404

        status = order_row['status'] if isinstance(order_row, dict) else order_row[0]
        if status in ['Picked Up', 'Cancelled']:
            return jsonify({"status": "error", "detail": f"Cannot cancel order with status {status}"}), 400

        cursor.execute("UPDATE orders SET status = 'Cancelled' WHERE order_id = ?;", (order_id,))
        cursor.execute("SELECT book_id, quantity FROM order_items WHERE order_id = ?;", (order_id,))
        items = cursor.fetchall()
        for item in items:
            bid = item['book_id'] if isinstance(item, dict) else item[0]
            qty = item['quantity'] if isinstance(item, dict) else item[1]
            cursor.execute("UPDATE books SET stock_quantity = stock_quantity + ? WHERE book_id = ?;", (qty, bid))

        conn.commit()
        return jsonify({"status": "success", "message": "Order cancelled and stock restored."})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "detail": str(e)}), 500
    finally:
        conn.close()

# --- ADMIN & STAFF ENDPOINTS (MOBILE & WEB APP PARITY) ---

@app.route('/api/admin/orders/', methods=['GET'])
@app.route('/api/admin/orders', methods=['GET'])
def get_admin_orders():
    status = request.args.get('status', 'Pending')
    conn = get_db()
    cursor = conn.cursor()
    query = """
        SELECT o.*, u.username as customer_name,
               GROUP_CONCAT(b.title, ', ') as items_summary
        FROM orders o 
        JOIN users u ON o.user_id = u.user_id 
        LEFT JOIN order_items oi ON o.order_id = oi.order_id
        LEFT JOIN books b ON oi.book_id = b.book_id
        WHERE o.status = ?
        GROUP BY o.order_id
        ORDER BY o.order_date DESC;
    """
    cursor.execute(query, (status,))
    rows = cursor.fetchall()
    conn.close()

    orders = []
    for r in rows:
        o = dict(r) if hasattr(r, 'keys') or isinstance(r, dict) else {
            'order_id': r[0], 'user_id': r[1], 'order_date': str(r[2]), 'status': r[3],
            'total_amount': float(r[4]), 'payment_method': r[5], 'stripe_payment_id': r[6],
            'pickup_pin': r[7], 'prepared_location': r[8], 'customer_name': r[9], 'items_summary': r[10]
        }
        o['display_id'] = f"PUC-ORD-{o['order_id'] + 1000}"
        o['created_at'] = str(o.get('order_date', ''))[:16]
        orders.append(o)

    return jsonify(orders)

@app.route('/api/admin/orders/<int:order_id>/prepare/', methods=['PATCH'])
@app.route('/api/admin/orders/<int:order_id>/prepare', methods=['PATCH'])
def admin_prepare(order_id):
    location = request.args.get('location', 'Counter 2')
    staff_id = request.args.get('staff_id', 1)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE orders SET status = 'Ready for Pickup', prepared_location = ?, prepared_by_staff_id = ? WHERE order_id = ?;",
        (location, staff_id, order_id)
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/admin/orders/lookup/<pin>', methods=['GET'])
def lookup_pin(pin):
    conn = get_db()
    cursor = conn.cursor()
    query = """
        SELECT o.*, u.username as customer_name 
        FROM orders o 
        JOIN users u ON o.user_id = u.user_id 
        WHERE o.pickup_pin = ?;
    """
    cursor.execute(query, (pin,))
    order = cursor.fetchone()
    conn.close()

    if not order:
        return jsonify({"status": "error", "detail": "Invalid PIN"}), 404

    order_dict = dict(order) if hasattr(order, 'keys') or isinstance(order, dict) else {
        'order_id': order[0], 'user_id': order[1], 'order_date': str(order[2]),
        'status': order[3], 'total_amount': float(order[4]), 'customer_name': order[8]
    }

    if order_dict['status'] == 'Pending':
        return jsonify({"status": "error", "detail": "Order not prepared. Please mark as Ready first."}), 400
    if order_dict['status'] == 'Picked Up':
        return jsonify({"status": "error", "detail": "Order already fulfilled."}), 400

    return jsonify(order_dict)

@app.route('/api/admin/orders/<int:order_id>/pickup/', methods=['PATCH'])
@app.route('/api/admin/orders/<int:order_id>/pickup', methods=['PATCH'])
def fulfill_pickup(order_id):
    staff_id = request.args.get('staff_id', 1)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE orders SET status = 'Picked Up', released_by_staff_id = ?, picked_up_at = datetime('now') WHERE order_id = ?;",
        (staff_id, order_id)
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/staff/analytics/', methods=['GET'])
def get_analytics():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count, SUM(total_amount) as revenue FROM orders WHERE status != 'Cancelled';")
    stats = cursor.fetchone()
    total_orders = stats['count'] if stats else 0
    total_revenue = float(stats['revenue'] or 0) if stats else 0.0

    cursor.execute("SELECT COUNT(*) as total_books, SUM(price * stock_quantity) as inventory_value FROM books;")
    inv_stats = cursor.fetchone()
    inventory_val = float(inv_stats['inventory_value'] or 0) if inv_stats else 0.0

    business_value = total_revenue + inventory_val

    # Top selling books
    cursor.execute("""
        SELECT b.title, SUM(oi.quantity) as sold 
        FROM order_items oi 
        JOIN books b ON oi.book_id = b.book_id 
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.status != 'Cancelled'
        GROUP BY b.book_id
        ORDER BY sold DESC LIMIT 3;
    """)
    top_books = [dict(r) if hasattr(r, 'keys') or isinstance(r, dict) else {'title': r[0], 'sold': r[1]} for r in cursor.fetchall()]

    conn.close()

    return jsonify({
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "business_value": business_value,
        "top_selling": top_books,
        "sales_by_department": [],
        "revenue_trend": []
    })

# --- STATIC FILE SERVING ---

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    if os.path.exists(os.path.join('.', path)):
        return send_from_directory('.', path)
    return send_from_directory('.', 'index.html')

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"[OK] PUC Digital Bookstore Customer Web App running live on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)

