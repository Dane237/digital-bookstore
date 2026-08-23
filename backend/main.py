import os
import logging
import hashlib
import secrets
import json
import smtplib
from email.mime.text import MIMEText
from typing import List, Optional
# noinspection PyPackageRequirements
from fastapi import FastAPI, HTTPException, Request
# noinspection PyPackageRequirements
from fastapi.middleware.cors import CORSMiddleware
# noinspection PyPackageRequirements
from pydantic import BaseModel
# noinspection PyPackageRequirements
import psycopg2
# noinspection PyPackageRequirements
from psycopg2.extras import RealDictCursor
# noinspection PyPackageRequirements
from dotenv import load_dotenv
# noinspection PyPackageRequirements
import stripe
from datetime import datetime, timedelta
import urllib.request

# Load configuration
load_dotenv()

app = FastAPI(title="PUC Bookstore API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_mockkey')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# — SECURITY —

def hash_password(password):
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
    return f"{salt}:{hashed}"

def verify_password(password, stored_pass):
    try:
        salt, stored_hash = stored_pass.split(":")
        computed_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
        return computed_hash == stored_hash
    except (ValueError, TypeError, Exception):
        return False

def send_otp_email(target_email, otp):
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_APP_PASSWORD')

    if not sender_email:
        logging.error("Email error: SENDER_EMAIL missing")
        return False
    if not sender_password:
        logging.error("Email error: SENDER_APP_PASSWORD missing")
        return False

    # Standardize password - remove spaces if they exist
    sender_password = sender_password.replace(" ", "")

    msg = MIMEText(f"Your PUC Bookstore Password Reset Code is: {otp}\n\nThis code expires in 10 minutes.")
    msg['Subject'] = "PUC Bookstore Security Code"
    msg['From'] = f"PUC Bookstore <{sender_email}>"
    msg['To'] = target_email

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except smtplib.SMTPException as e:
        logging.error(f"Email error: {e}")
        return False

# — MODELS —

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class StaffCreateRequest(BaseModel):
    username: str
    email: str
    password: str
    employee_id: str

class UserLogin(BaseModel):
    email: str
    password: str

class AdminPasswordReset(BaseModel):
    admin_id: int
    target_user_email: str
    new_password: str

class OTPRequest(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    email: str
    otp: str
    new_password: str

class OrderItemCreate(BaseModel):
    book_id: int
    quantity: int
    unit_price: float

class OrderCreate(BaseModel):
    user_id: int
    total_amount: float
    payment_method: str
    stripe_payment_id: Optional[str] = None
    items: List[OrderItemCreate]

class ManualBookAddRequest(BaseModel):
    isbn: str
    title: str
    author: Optional[str] = ""
    price: float
    stock_quantity: int
    department_name: str
    description: Optional[str] = ""
    cover_img: Optional[str] = ""

# — DATABASE (PostgreSQL) —

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'puc_bookstore'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'pass123'),
        port=os.getenv('DB_PORT', '5432')
    )

def init_db():
    """Ensure required tables exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_resets (
                email VARCHAR(100) PRIMARY KEY REFERENCES users(email) ON DELETE CASCADE,
                otp VARCHAR(10) NOT NULL,
                expires_at TIMESTAMP NOT NULL
            );
        """)
        conn.commit()
        logging.info("Database initialized successfully.")
    except Exception as e:
        logging.error(f"Database initialization error: {e}")
    finally:
        cursor.close()
        conn.close()

# Initialize DB on startup
init_db()

# — ENDPOINTS —

@app.get("/api/departments/")
async def get_departments():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM departments ORDER BY name ASC")
    # noinspection PyTypeChecker
    depts_list = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return depts_list

@app.get("/api/books/")
async def get_books(department: str = "all", q: str = ""):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    query = """
        SELECT b.*, STRING_AGG(d.name, ',') as departments 
        FROM books b 
        LEFT JOIN book_departments bd ON b.book_id = bd.book_id 
        LEFT JOIN departments d ON bd.department_id = d.department_id 
        WHERE 1=1
    """
    params = []
    if department != "all":
        query += " AND d.name = %s"
        params.append(department)
    if q:
        query += " AND (b.title ILIKE %s OR b.isbn ILIKE %s OR b.description ILIKE %s OR b.author ILIKE %s)"
        pattern = f"%{q}%"
        params.extend([pattern, pattern, pattern, pattern])
    query += " GROUP BY b.book_id ORDER BY b.created_at DESC"
    cursor.execute(query, params)
    books = cursor.fetchall()
    cursor.close()
    conn.close()
    return books

@app.post("/api/register/")
def register_user(user: UserRegister):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT user_id FROM users WHERE email = %s", (user.email,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Email exists")
    
    # Logic: Force 'Admin' for the specific master email
    if user.email.lower() == 'vongchantha2001@gmail.com':
        role = 'Admin'
    else:
        role = 'Customer'
        
    hashed = hash_password(user.password)
    
    cursor.execute(
        "INSERT INTO users (username, email, password_hash, role, employee_id) VALUES (%s, %s, %s, %s, %s) RETURNING user_id", 
        (user.username, user.email, hashed, role, 'PUC-ROOT-001' if role == 'Admin' else None)
    )
    user_id = cursor.fetchone()['user_id']
    conn.commit()
    cursor.close()
    conn.close()
    
    return {
        "status": "success", 
        "user": {"user_id": user_id, "username": user.username, "email": user.email, "role": role}
    }

@app.post("/api/admin/staff/add/")
def admin_add_staff(req: StaffCreateRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (req.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Staff email already exists")
        
        hashed = hash_password(req.password)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role, employee_id) VALUES (%s, %s, %s, 'Staff', %s)", 
            (req.username, req.email, hashed, req.employee_id)
        )
        conn.commit()
        return {"status": "success", "message": f"Staff account {req.employee_id} created."}
    finally:
        cursor.close()
        conn.close()

@app.post("/api/login/")
def login_user(user: UserLogin):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE email = %s", (user.email,))
    db_user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if db_user and verify_password(user.password, db_user['password_hash']):
        return {"status": "success", "user": {
            "user_id": db_user['user_id'], 
            "username": db_user['username'], 
            "email": db_user['email'], 
            "role": db_user['role'], 
            "employee_id": db_user.get('employee_id')
        }}
    raise HTTPException(status_code=401, detail="Invalid login")

@app.post("/api/forgot-password/")
def forgot_password(req: OTPRequest):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT user_id, role FROM users WHERE email = %s", (req.email,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Check if SMTP config is present before proceeding
    if not os.getenv('SENDER_EMAIL') or not os.getenv('SENDER_APP_PASSWORD'):
        cursor.close()
        conn.close()
        raise HTTPException(status_code=500, detail="Server Email Configuration missing. Please set SENDER_EMAIL and SENDER_APP_PASSWORD in Render environment variables.")

    otp = str(secrets.randbelow(900000) + 100000)
    expires_at = datetime.now() + timedelta(minutes=10)
    
    # Store in database (UPSERT)
    cursor.execute("""
        INSERT INTO password_resets (email, otp, expires_at) 
        VALUES (%s, %s, %s)
        ON CONFLICT (email) DO UPDATE SET otp = EXCLUDED.otp, expires_at = EXCLUDED.expires_at
    """, (req.email, otp, expires_at))
    conn.commit()
    cursor.close()
    conn.close()
    
    if send_otp_email(req.email, otp):
        return {"status": "success", "message": "OTP sent to your email"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send email. Check SMTP config.")

@app.post("/api/reset-password-confirm/")
def reset_password_confirm(req: PasswordResetConfirm):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT otp, expires_at FROM password_resets WHERE email = %s", (req.email,))
    stored = cursor.fetchone()
    
    if not stored:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="No OTP requested for this email")
    
    if datetime.now() > stored["expires_at"]:
        cursor.execute("DELETE FROM password_resets WHERE email = %s", (req.email,))
        conn.commit()
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="OTP expired")
    
    if stored["otp"] != req.otp:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid code")

    new_hashed = hash_password(req.new_password)
    cursor.execute("UPDATE users SET password_hash = %s WHERE email = %s", (new_hashed, req.email))
    cursor.execute("DELETE FROM password_resets WHERE email = %s", (req.email,))
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"status": "success", "message": "Password updated"}

@app.post("/api/admin/users/reset-password/")
def admin_reset_password(req: AdminPasswordReset):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Verify the requester is actually an admin
        cursor.execute("SELECT role FROM users WHERE user_id = %s", (req.admin_id,))
        admin = cursor.fetchone()
        if not admin or admin['role'] != 'Admin':
            raise HTTPException(status_code=403, detail="Only Admins can perform this action")

        # Check if target user exists
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (req.target_user_email,))
        target = cursor.fetchone()
        if not target:
            raise HTTPException(status_code=404, detail="Target user not found")

        # Update password
        new_hashed = hash_password(req.new_password)
        cursor.execute("UPDATE users SET password_hash = %s WHERE email = %s", (new_hashed, req.target_user_email))
        conn.commit()
        return {"status": "success", "message": f"Password for {req.target_user_email} has been reset by Admin."}
    finally:
        cursor.close()
        conn.close()

@app.post("/api/admin/books/add/")
async def admin_add_book(data: ManualBookAddRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO departments (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (data.department_name,))
        cursor.execute("SELECT department_id FROM departments WHERE name = %s", (data.department_name,))
        dept_id = cursor.fetchone()[0]

        query = """
            INSERT INTO books (isbn, title, author, price, stock_quantity, description, cover_img)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (isbn) DO UPDATE SET 
                title=EXCLUDED.title, author=EXCLUDED.author, price=EXCLUDED.price, 
                stock_quantity=EXCLUDED.stock_quantity, description=EXCLUDED.description, cover_img=EXCLUDED.cover_img
            RETURNING book_id
        """
        cursor.execute(query, (data.isbn, data.title, data.author, data.price, data.stock_quantity, data.description, data.cover_img))
        book_id = cursor.fetchone()[0]

        cursor.execute("INSERT INTO book_departments (book_id, department_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (book_id, dept_id))
        conn.commit()
        return {"status": "success"}
    finally:
        cursor.close()
        conn.close()

@app.delete("/api/admin/books/{book_id}/")
async def delete_book(book_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM books WHERE book_id = %s", (book_id,))
        conn.commit()
        return {"status": "success"}
    except psycopg2.Error as err:
        if err.pgcode == '23503': # Foreign key violation
            raise HTTPException(status_code=400, detail="Cannot delete book because it is part of existing orders. Try setting stock to 0 instead.")
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        cursor.close()
        conn.close()

@app.post("/api/orders/")
async def create_order(order: OrderCreate):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        pin = str(secrets.randbelow(900000) + 100000)
        cursor.execute(
            "INSERT INTO orders (user_id, total_amount, pickup_pin, payment_method, stripe_payment_id) VALUES (%s, %s, %s, %s, %s) RETURNING order_id", 
            (order.user_id, order.total_amount, pin, order.payment_method, order.stripe_payment_id)
        )
        oid = cursor.fetchone()['order_id']
        for item in order.items:
            cursor.execute("INSERT INTO order_items (order_id, book_id, quantity, unit_price) VALUES (%s, %s, %s, %s)", (oid, item.book_id, item.quantity, item.unit_price))
            # Update stock only if sufficient quantity exists
            cursor.execute("UPDATE books SET stock_quantity = stock_quantity - %s WHERE book_id = %s AND stock_quantity >= %s", (item.quantity, item.book_id, item.quantity))
            if cursor.rowcount == 0:
                raise Exception(f"Insufficient stock for book ID {item.book_id}")
        conn.commit()
        return {"status": "success", "order_id": oid, "pickup_pin": pin}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/orders/{user_id}")
async def user_orders(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    query = """
        SELECT o.*, COUNT(oi.order_item_id) as item_count,
               u_rel.username as released_by_name,
               u_rel.employee_id as released_by_staff_id
        FROM orders o 
        LEFT JOIN order_items oi ON o.order_id = oi.order_id 
        LEFT JOIN users u_rel ON o.released_by_staff_id = u_rel.user_id
        WHERE o.user_id = %s 
        GROUP BY o.order_id, u_rel.username, u_rel.employee_id
        ORDER BY o.order_date DESC
    """
    cursor.execute(query, (user_id,))
    orders = cursor.fetchall()
    for o in orders:
        o['display_id'] = f"PUC-ORD-{o['order_id']+1000}"
        o['created_at'] = o['order_date'].strftime('%Y-%m-%d %H:%M')
    cursor.close()
    conn.close()
    return orders

@app.patch("/api/orders/{order_id}/cancel/")
async def cancel_order(order_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT status FROM orders WHERE order_id = %s", (order_id,))
        order = cursor.fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order['status'] in ['Picked Up', 'Cancelled']:
            raise HTTPException(status_code=400, detail=f"Cannot cancel order with status {order['status']}")

        cursor.execute("UPDATE orders SET status = 'Cancelled' WHERE order_id = %s", (order_id,))
        cursor.execute("SELECT book_id, quantity FROM order_items WHERE order_id = %s", (order_id,))
        items = cursor.fetchall()
        for item in items:
            cursor.execute("UPDATE books SET stock_quantity = stock_quantity + %s WHERE book_id = %s", (item['quantity'], item['book_id']))
        
        conn.commit()
        return {"status": "success", "message": "Order cancelled and stock restored."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/admin/orders/")
async def get_admin_orders(status: str):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    query = """
        SELECT o.*, u.username as customer_name,
               STRING_AGG(CONCAT(b.title, ' (x', oi.quantity, ')'), ', ') as items_summary
        FROM orders o 
        JOIN users u ON o.user_id = u.user_id 
        LEFT JOIN order_items oi ON o.order_id = oi.order_id
        LEFT JOIN books b ON oi.book_id = b.book_id
        WHERE o.status = %s
        GROUP BY o.order_id, u.username
        ORDER BY o.order_date DESC
    """
    cursor.execute(query, (status,))
    orders = cursor.fetchall()
    for o in orders:
        o['display_id'] = f"PUC-ORD-{o['order_id']+1000}"
        o['created_at'] = o['order_date'].strftime('%Y-%m-%d %H:%M')
    cursor.close()
    conn.close()
    return orders

@app.patch("/api/admin/orders/{order_id}/prepare/")
async def admin_prepare(order_id: int, location: str, staff_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE orders SET status = 'Ready for Pickup', prepared_location = %s, prepared_by_staff_id = %s WHERE order_id = %s", 
        (location, staff_id, order_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success"}

@app.get("/api/admin/orders/lookup/{pin}")
async def lookup_pin(pin: str):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    query = """
        SELECT o.*, u.username as customer_name 
        FROM orders o 
        JOIN users u ON o.user_id = u.user_id 
        WHERE o.pickup_pin = %s
    """
    cursor.execute(query, (pin,))
    order = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not order:
        raise HTTPException(status_code=404, detail="Invalid PIN")
    if order['status'] == 'Pending':
        raise HTTPException(status_code=400, detail="Order not prepared. Please mark as Ready first.")
    if order['status'] == 'Picked Up':
        raise HTTPException(status_code=400, detail="Order already fulfilled.")
    return order

@app.patch("/api/admin/orders/{order_id}/pickup/")
async def fulfill_pickup(order_id: int, staff_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE orders SET status = 'Picked Up', released_by_staff_id = %s, picked_up_at = NOW() WHERE order_id = %s", 
        (staff_id, order_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success"}

@app.get("/api/admin/isbn-lookup/{isbn}")
async def isbn_lookup(isbn: str):
    try:
        url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            if data.get("totalItems", 0) > 0:
                item = data["items"][0]["volumeInfo"]
                return {
                    "title": item.get("title", ""),
                    "author": ", ".join(item.get("authors", [])),
                    "description": item.get("description", ""),
                    "cover_img": item.get("imageLinks", {}).get("thumbnail", ""),
                }
            return {"error": "Not found"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/orders/detail/{order_id}")
async def order_details(order_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    query = """
        SELECT oi.*, b.title 
        FROM order_items oi 
        JOIN books b ON oi.book_id = b.book_id 
        WHERE oi.order_id = %s
    """
    cursor.execute(query, (order_id,))
    items = cursor.fetchall()
    cursor.close()
    conn.close()
    return items

@app.get("/api/staff/analytics/")
async def get_analytics():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT COUNT(*) as count, SUM(total_amount) as revenue FROM orders WHERE status != 'Cancelled'")
        stats = cursor.fetchone()
        total_orders = stats['count'] if stats else 0
        total_revenue = float(stats['revenue'] or 0)
        
        # 2. Total Business Value (Cash Earned + Remaining Stock Value)
        # This number stays consistent as books turn into cash.
        cursor.execute("""
            SELECT (
                COALESCE((SELECT SUM(total_amount) FROM orders WHERE status != 'Cancelled'), 0) + 
                COALESCE((SELECT SUM(price * stock_quantity) FROM books WHERE stock_quantity > 0), 0)
            ) as total_worth
        """)
        worth_result = cursor.fetchone()
        business_worth = float(worth_result['total_worth'] or 0) if worth_result else 0.0
        
        cursor.execute("""
            SELECT b.title, SUM(oi.quantity) as sold 
            FROM order_items oi 
            JOIN books b ON oi.book_id = b.book_id 
            JOIN orders o ON oi.order_id = o.order_id
            WHERE o.status != 'Cancelled'
            GROUP BY b.book_id, b.title 
            ORDER BY sold DESC LIMIT 3
        """)
        top_books = cursor.fetchall()
        
        cursor.execute("""
            SELECT d.name, SUM(oi.quantity * oi.unit_price) as revenue 
            FROM departments d 
            JOIN book_departments bd ON d.department_id = bd.department_id 
            JOIN order_items oi ON bd.book_id = oi.book_id 
            JOIN orders o ON oi.order_id = o.order_id
            WHERE o.status != 'Cancelled'
            GROUP BY d.department_id, d.name
        """)
        sales_dept = cursor.fetchall()
        
        revenue_trend = []
        for i in range(6, -1, -1):
            target_date = (datetime.now() - timedelta(days=i)).date()
            cursor.execute("SELECT SUM(total_amount) as daily_total FROM orders WHERE CAST(order_date AS DATE) = %s AND status != 'Cancelled'", (target_date,))
            day_result = cursor.fetchone()
            daily_sum = float(day_result['daily_total'] or 0) if day_result else 0.0
            revenue_trend.append({
                "date": target_date.strftime('%Y-%m-%d'),
                "revenue": daily_sum
            })
            
        return {
            "total_orders": total_orders, 
            "total_revenue": total_revenue, 
            "business_value": business_worth,
            "top_selling": top_books,
            "sales_by_department": sales_dept,
            "revenue_trend": revenue_trend
        }
    except Exception as e:
        logging.error(f"Analytics Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

# — PROJECT RESET & SETUP SEEDER —
@app.post("/api/admin/seed/")
async def seed_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            DELETE FROM departments 
            WHERE name = 'Computer Science' 
               OR name = 'Technology'
        """)
        
        hashed = hash_password("password")
        cursor.execute("""
            INSERT INTO users (user_id, username, email, password_hash, role, employee_id) 
            VALUES (1, 'PUC Admin', 'vongchantha2001@gmail.com', %s, 'Admin', 'PUC-ROOT-001')
            ON CONFLICT (user_id) DO UPDATE SET 
                email='vongchantha2001@gmail.com',
                role='Admin',
                employee_id='PUC-ROOT-001'
        """, (hashed,))
        
        depts = ['Computer Science & Tech', 'Business & Economics', 'Law & Public Affairs', 'Arts & Humanities', 'Information Technology']
        for dname in depts:
            cursor.execute("INSERT INTO departments (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (dname,))
        
        conn.commit()
        return {"status": "success", "message": "System database cleaned. Official departments and Staff account synced."}
    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()

@app.post("/api/admin/wipe-inventory/")
async def wipe_inventory():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM books")
        conn.commit()
        return {"status": "success", "message": "Inventory wiped."}
    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
