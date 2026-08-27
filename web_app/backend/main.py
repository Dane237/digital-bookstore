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
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
# noinspection PyPackageRequirements
import stripe
from datetime import datetime, timedelta
import urllib.request

# Load configuration
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="PUC Bookstore API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Customer Web App static files & serve index.html at '/'
customer_web_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'customer'))
if not os.path.exists(customer_web_dir):
    customer_web_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'web_app', 'customer'))
if os.path.exists(customer_web_dir):
    for subfolder in ['css', 'js', 'assets']:
        folder_path = os.path.join(customer_web_dir, subfolder)
        if os.path.exists(folder_path):
            app.mount(f"/{subfolder}", StaticFiles(directory=folder_path), name=subfolder)

    @app.get("/")
    def read_root():
        index_file = os.path.join(customer_web_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"status": "PUC Bookstore API is running", "docs": "/docs"}

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
    try:
        smtp_port = int(os.getenv('SMTP_PORT', '465'))
    except (ValueError, TypeError):
        smtp_port = 465
        
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_APP_PASSWORD')

    if not sender_email or not sender_password:
        return False, "SENDER_EMAIL or SENDER_APP_PASSWORD is not set."

    sender_password = sender_password.replace(" ", "")

    msg = MIMEText(f"Your PUC Bookstore Password Reset Code is: {otp}\n\nThis code expires in 10 minutes.")
    msg['Subject'] = "PUC Bookstore Security Code"
    msg['From'] = f"PUC Bookstore <{sender_email}>"
    msg['To'] = target_email

    try:
        if smtp_port == 465:
            logging.info(f"Attempting to send email via {smtp_server}:{smtp_port} using SSL")
            with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10) as server:
                server.login(sender_email, sender_password)
                server.send_message(msg)
        else:
            logging.info(f"Attempting to send email via {smtp_server}:{smtp_port} using STARTTLS")
            with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
        logging.info(f"Email sent successfully to {target_email}")
        return True, "Success"
    except Exception as e:
        logging.error(f"SMTP Error: {e}")
        return False, str(e)

# — MODELS —

class UserRegister(BaseModel):
    username: str
    email: str
    password: str
    student_id: Optional[str] = None

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

# — DATABASE (PostgreSQL Connection Pooling) —

db_pool = None

class PooledConnectionWrapper:
    def __init__(self, conn, pool):
        self._conn = conn
        self._pool = pool

    def cursor(self, *args, **kwargs):
        return self._conn.cursor(*args, **kwargs)

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        if self._pool and self._conn:
            try:
                self._pool.putconn(self._conn)
            except Exception:
                pass

    def __getattr__(self, name):
        return getattr(self._conn, name)

def init_db_pool():
    global db_pool
    if db_pool is None or db_pool.closed:
        db_url = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL')
        if db_url:
            logging.info("⚡ Initializing High-Performance DB Connection Pool via DATABASE_URL")
            db_pool = ThreadedConnectionPool(minconn=2, maxconn=15, dsn=db_url)
        else:
            host = os.getenv('DB_HOST', 'localhost')
            db_name = os.getenv('DB_NAME', 'puc_bookstore')
            user = os.getenv('DB_USER', 'postgres')
            password = os.getenv('DB_PASSWORD', 'pass123')
            port = os.getenv('DB_PORT', '5432')
            logging.info(f"⚡ Initializing High-Performance DB Connection Pool at {host}:{port}/{db_name}")
            db_pool = ThreadedConnectionPool(
                minconn=2, maxconn=15,
                host=host, database=db_name, user=user, password=password, port=port
            )

def get_db_connection():
    global db_pool
    if db_pool is None or db_pool.closed:
        init_db_pool()
    try:
        raw_conn = db_pool.getconn()
        if raw_conn.closed != 0:
            db_pool.putconn(raw_conn, close=True)
            raw_conn = db_pool.getconn()
        return PooledConnectionWrapper(raw_conn, db_pool)
    except Exception as e:
        logging.warning(f"Connection pool fallback: {e}")
        db_url = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL')
        if db_url:
            return psycopg2.connect(db_url, connect_timeout=10)
        host = os.getenv('DB_HOST', 'localhost')
        db_name = os.getenv('DB_NAME', 'puc_bookstore')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD', 'pass123')
        port = os.getenv('DB_PORT', '5432')
        return psycopg2.connect(host=host, database=db_name, user=user, password=password, port=port, connect_timeout=10)

@app.get("/api/health/")
def health_check():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return {"status": "healthy", "database": "connected", "details": "System is operational"}
    except Exception as e:
        logging.error(f"Health Check Failed: {e}")
        return {"status": "unhealthy", "database": str(e)}

def init_db():
    """Ensure required tables exist."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_resets (
                email VARCHAR(100) PRIMARY KEY REFERENCES users(email) ON DELETE CASCADE,
                otp VARCHAR(10) NOT NULL,
                expires_at TIMESTAMP NOT NULL
            );
        """)
        conn.commit()
        cursor.close()
        conn.close()
        logging.info("Database initialized successfully.")
    except Exception as e:
        logging.error(f"Database initialization deferred or failed: {e}")

# Run DB init in a slightly safer way
@app.on_event("startup")
async def startup_event():
    init_db()

# — ENDPOINTS —

@app.get("/api/departments/")
def get_departments():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM admin_dashboard_department ORDER BY name ASC")
    # noinspection PyTypeChecker
    depts_list = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return depts_list

@app.get("/api/books/")
def get_books(department: str = "all", q: str = ""):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    query = """
        SELECT b.id AS book_id, b.isbn, b.title, b.author, b.price, b.stock_quantity, b.description, b.cover_img, b.created_at,
               STRING_AGG(d.name, ', ') as departments 
        FROM admin_dashboard_book b 
        LEFT JOIN admin_dashboard_book_departments bd ON b.id = bd.book_id 
        LEFT JOIN admin_dashboard_department d ON bd.department_id = d.id 
        WHERE 1=1
    """
    params = []
    if department and department != "all":
        query += " AND (d.name = %s OR d.name ILIKE %s)"
        params.extend([department, f"%{department}%"])
    if q:
        query += " AND (b.title ILIKE %s OR b.isbn ILIKE %s OR b.description ILIKE %s OR b.author ILIKE %s)"
        pattern = f"%{q}%"
        params.extend([pattern, pattern, pattern, pattern])
    query += " GROUP BY b.id, b.isbn, b.title, b.author, b.price, b.stock_quantity, b.description, b.cover_img, b.created_at ORDER BY b.created_at DESC"
    cursor.execute(query, params)
    books = cursor.fetchall()
    cursor.close()
    conn.close()
    for b in books:
        depts = b.get('departments')
        b['department'] = depts.split(',')[0].strip() if depts else 'General'
    return books

@app.post("/api/register/")
def register_user(user: UserRegister):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT id AS user_id FROM admin_dashboard_user WHERE email = %s", (user.email,))
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
    
    emp_id = user.student_id if user.student_id else ('PUC-ROOT-001' if role == 'Admin' else None)
    cursor.execute(
        "INSERT INTO admin_dashboard_user (username, email, password_hash, role, employee_id, created_at) VALUES (%s, %s, %s, %s, %s, NOW()) RETURNING id AS user_id", 
        (user.username, user.email, hashed, role, emp_id)
    )
    user_id = cursor.fetchone()['user_id']
    conn.commit()
    cursor.close()
    conn.close()
    
    return {
        "status": "success", 
        "user": {"user_id": user_id, "username": user.username, "email": user.email, "role": role, "employee_id": emp_id}
    }

@app.post("/api/admin/staff/add/")
def admin_add_staff(req: StaffCreateRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id AS user_id FROM admin_dashboard_user WHERE email = %s", (req.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Staff email already exists")
        
        hashed = hash_password(req.password)
        cursor.execute(
            "INSERT INTO admin_dashboard_user (username, email, password_hash, role, employee_id, created_at) VALUES (%s, %s, %s, 'Staff', %s, NOW())", 
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
    cursor.execute("SELECT id AS user_id, username, email, password_hash, role, employee_id FROM admin_dashboard_user WHERE email = %s", (user.email,))
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
    cursor.execute("SELECT id AS user_id, role FROM admin_dashboard_user WHERE email = %s", (req.email,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Log warning if SMTP config is missing, but don't crash yet
    if not os.getenv('SENDER_EMAIL') or not os.getenv('SENDER_APP_PASSWORD'):
        logging.warning("SENDER_EMAIL or SENDER_APP_PASSWORD is not set. Email will not be sent, but OTP is logged.")

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
    
    # FOR DEVELOPMENT: Print OTP to logs in case Render blocks SMTP
    logging.info(f"🔑 SECURITY CODE FOR {req.email}: {otp}")
    
    success, error_msg = send_otp_email(req.email, otp)
    if success:
        return {"status": "success", "message": "OTP sent to your email"}
    else:
        # We still return success if we logged it, so you can test the app!
        logging.warning(f"Email failed but OTP is logged: {error_msg}")
        return {
            "status": "success", 
            "message": "Security code generated. (Check Render logs if email doesn't arrive)",
            "dev_note": "SMTP is blocked by Render. Look at Render Dashboard Logs to find your code."
        }

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
    cursor.execute("UPDATE admin_dashboard_user SET password_hash = %s WHERE email = %s", (new_hashed, req.email))
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
        cursor.execute("SELECT role FROM admin_dashboard_user WHERE id = %s", (req.admin_id,))
        admin = cursor.fetchone()
        if not admin or admin['role'] != 'Admin':
            raise HTTPException(status_code=403, detail="Only Admins can perform this action")

        # Check if target user exists
        cursor.execute("SELECT id AS user_id FROM admin_dashboard_user WHERE email = %s", (req.target_user_email,))
        target = cursor.fetchone()
        if not target:
            raise HTTPException(status_code=404, detail="Target user not found")

        # Update password
        new_hashed = hash_password(req.new_password)
        cursor.execute("UPDATE admin_dashboard_user SET password_hash = %s WHERE email = %s", (new_hashed, req.target_user_email))
        conn.commit()
        return {"status": "success", "message": f"Password for {req.target_user_email} has been reset by Admin."}
    finally:
        cursor.close()
        conn.close()

@app.post("/api/admin/books/add/")
def admin_add_book(data: ManualBookAddRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO admin_dashboard_department (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (data.department_name,))
        cursor.execute("SELECT id AS department_id FROM admin_dashboard_department WHERE name = %s", (data.department_name,))
        dept_id = cursor.fetchone()[0]

        query = """
            INSERT INTO admin_dashboard_book (isbn, title, author, price, stock_quantity, description, cover_img)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (isbn) DO UPDATE SET 
                title=EXCLUDED.title, author=EXCLUDED.author, price=EXCLUDED.price, 
                stock_quantity=EXCLUDED.stock_quantity, description=EXCLUDED.description, cover_img=EXCLUDED.cover_img
            RETURNING book_id
        """
        cursor.execute(query, (data.isbn, data.title, data.author, data.price, data.stock_quantity, data.description, data.cover_img))
        book_id = cursor.fetchone()[0]

        cursor.execute("INSERT INTO admin_dashboard_book_departments (book_id, department_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (book_id, dept_id))
        conn.commit()
        return {"status": "success"}
    finally:
        cursor.close()
        conn.close()

@app.delete("/api/admin/books/{book_id}/")
def delete_book(book_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM admin_dashboard_book WHERE id = %s", (book_id,))
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
def create_order(order: OrderCreate):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        pin = str(secrets.randbelow(900000) + 100000)
        cursor.execute(
            "INSERT INTO admin_dashboard_order (user_id, order_date, status, total_amount, pickup_pin, payment_method, stripe_payment_id) VALUES (%s, NOW(), 'Pending', %s, %s, %s, %s) RETURNING id AS order_id", 
            (order.user_id, order.total_amount, pin, order.payment_method, order.stripe_payment_id)
        )
        oid = cursor.fetchone()['order_id']
        for item in order.items:
            cursor.execute("INSERT INTO admin_dashboard_orderitem (order_id, book_id, quantity, unit_price) VALUES (%s, %s, %s, %s)", (oid, item.book_id, item.quantity, item.unit_price))
            # Update stock only if sufficient quantity exists
            cursor.execute("UPDATE admin_dashboard_book SET stock_quantity = stock_quantity - %s WHERE id = %s AND stock_quantity >= %s", (item.quantity, item.book_id, item.quantity))
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
def user_orders(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    query = """
        SELECT o.id AS order_id, o.user_id, o.order_date, o.status, o.total_amount, 
               o.payment_method, o.stripe_payment_id, o.pickup_pin, o.prepared_location, 
               u_rel.username as released_by_name, u_rel.employee_id as released_by_staff_id
        FROM admin_dashboard_order o 
        LEFT JOIN admin_dashboard_user u_rel ON o.released_by_staff_id = u_rel.id
        WHERE o.user_id = %s 
        ORDER BY o.order_date DESC
    """
    cursor.execute(query, (user_id,))
    orders = cursor.fetchall()
    for o in orders:
        oid = o.get('order_id') or o.get('id')
        o['order_id'] = oid
        o['display_id'] = f"PUC-ORD-{oid+1000}"
        o['total_amount'] = float(o['total_amount']) if o.get('total_amount') is not None else 0.0
        if o.get('order_date'):
            o['created_at'] = o['order_date'].strftime('%Y-%m-%d %H:%M')

        # Automatically fetch complete items with cover images & authors for this order
        item_query = """
            SELECT oi.id AS order_item_id, oi.order_id, oi.book_id, oi.quantity, 
                   oi.unit_price, b.title, b.author, b.cover_img, b.isbn
            FROM admin_dashboard_orderitem oi
            JOIN admin_dashboard_book b ON oi.book_id = b.id
            WHERE oi.order_id = %s
        """
        cursor.execute(item_query, (oid,))
        items = cursor.fetchall()
        for item in items:
            item['unit_price'] = float(item['unit_price']) if item.get('unit_price') is not None else 0.0
            item['price'] = item['unit_price']
        o['items'] = items

    cursor.close()
    conn.close()
    return orders

@app.patch("/api/orders/{order_id}/cancel/")
def cancel_order(order_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT status FROM admin_dashboard_order WHERE id = %s", (order_id,))
        order = cursor.fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order['status'] in ['Picked Up', 'Cancelled']:
            raise HTTPException(status_code=400, detail=f"Cannot cancel order with status {order['status']}")

        cursor.execute("UPDATE admin_dashboard_order SET status = 'Cancelled' WHERE id = %s", (order_id,))
        cursor.execute("SELECT book_id, quantity FROM admin_dashboard_orderitem WHERE order_id = %s", (order_id,))
        items = cursor.fetchall()
        for item in items:
            cursor.execute("UPDATE admin_dashboard_book SET stock_quantity = stock_quantity + %s WHERE id = %s", (item['quantity'], item['book_id']))
        
        conn.commit()
        return {"status": "success", "message": "Order cancelled and stock restored."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/admin/orders/")
def get_admin_orders(status: str):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    query = """
        SELECT o.*, u.username as customer_name,
               STRING_AGG(CONCAT(b.title, ' (x', oi.quantity, ')'), ', ') as items_summary
        FROM admin_dashboard_order o 
        JOIN admin_dashboard_user u ON o.user_id = u.id 
        LEFT JOIN admin_dashboard_orderitem oi ON o.id = oi.order_id
        LEFT JOIN admin_dashboard_book b ON oi.book_id = b.id
        WHERE o.status = %s
        GROUP BY o.id, u.username
        ORDER BY o.order_date DESC
    """
    cursor.execute(query, (status,))
    orders = cursor.fetchall()
    for o in orders:
        oid = o.get('order_id') or o.get('id')
        o['order_id'] = oid
        o['display_id'] = f"PUC-ORD-{oid+1000}"
        o['total_amount'] = float(o['total_amount']) if o.get('total_amount') is not None else 0.0
        if o.get('order_date'):
            o['created_at'] = o['order_date'].strftime('%Y-%m-%d %H:%M')
    cursor.close()
    conn.close()
    return orders

@app.patch("/api/admin/orders/{order_id}/prepare/")
def admin_prepare(order_id: int, location: str, staff_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE admin_dashboard_order SET status = 'Ready for Pickup', prepared_location = %s, prepared_by_staff_id = %s WHERE id = %s", 
        (location, staff_id, order_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success"}

@app.get("/api/admin/orders/lookup/{pin}")
def lookup_pin(pin: str):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    query = """
        SELECT o.*, u.username as customer_name 
        FROM admin_dashboard_order o 
        JOIN admin_dashboard_user u ON o.user_id = u.id 
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
def fulfill_pickup(order_id: int, staff_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE admin_dashboard_order SET status = 'Picked Up', released_by_staff_id = %s, picked_up_at = NOW() WHERE id = %s", 
        (staff_id, order_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success"}

@app.get("/api/admin/isbn-lookup/{isbn}")
def isbn_lookup(isbn: str):
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
def order_details(order_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    query = """
        SELECT oi.id AS order_item_id, oi.order_id, oi.book_id, oi.quantity, 
               oi.unit_price, b.title, b.author, b.cover_img, b.isbn
        FROM admin_dashboard_orderitem oi 
        JOIN admin_dashboard_book b ON oi.book_id = b.id 
        WHERE oi.order_id = %s
    """
    cursor.execute(query, (order_id,))
    items = cursor.fetchall()
    for item in items:
        item['unit_price'] = float(item['unit_price']) if item.get('unit_price') is not None else 0.0
        item['price'] = item['unit_price']
    cursor.close()
    conn.close()
    return items

@app.get("/api/staff/analytics/")
def get_analytics():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT COUNT(*) as count, SUM(total_amount) as revenue FROM admin_dashboard_order WHERE status != 'Cancelled'")
        stats = cursor.fetchone()
        total_orders = stats['count'] if stats else 0
        total_revenue = float(stats['revenue'] or 0)
        
        # 2. Total Business Value (Cash Earned + Remaining Stock Value)
        # This number stays consistent as books turn into cash.
        cursor.execute("""
            SELECT (
                COALESCE((SELECT SUM(total_amount) FROM admin_dashboard_order WHERE status != 'Cancelled'), 0) + 
                COALESCE((SELECT SUM(price * stock_quantity) FROM admin_dashboard_book WHERE stock_quantity > 0), 0)
            ) as total_worth
        """)
        worth_result = cursor.fetchone()
        business_worth = float(worth_result['total_worth'] or 0) if worth_result else 0.0
        
        cursor.execute("""
            SELECT b.title, SUM(oi.quantity) as sold 
            FROM admin_dashboard_orderitem oi 
            JOIN books b ON oi.book_id = b.id 
            JOIN admin_dashboard_order o ON oi.order_id = o.id
            WHERE o.status != 'Cancelled'
            GROUP BY b.id, b.title 
            ORDER BY sold DESC LIMIT 3
        """)
        top_books = cursor.fetchall()
        
        cursor.execute("""
            SELECT d.name, SUM(oi.quantity * oi.unit_price) as revenue 
            FROM departments d 
            JOIN admin_dashboard_book_departments bd ON d.id = bd.id 
            JOIN order_items oi ON bd.book_id = oi.book_id 
            JOIN admin_dashboard_order o ON oi.order_id = o.id
            WHERE o.status != 'Cancelled'
            GROUP BY d.id, d.name
        """)
        sales_dept = cursor.fetchall()
        
        revenue_trend = []
        for i in range(6, -1, -1):
            target_date = (datetime.now() - timedelta(days=i)).date()
            cursor.execute("SELECT SUM(total_amount) as daily_total FROM admin_dashboard_order WHERE CAST(order_date AS DATE) = %s AND status != 'Cancelled'", (target_date,))
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
def seed_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            DELETE FROM admin_dashboard_department 
            WHERE name = 'Computer Science' 
               OR name = 'Technology'
        """)
        
        hashed = hash_password("password")
        cursor.execute("""
            INSERT INTO admin_dashboard_user (id, username, email, password_hash, role, employee_id) 
            VALUES (1, 'PUC Admin', 'vongchantha2001@gmail.com', %s, 'Admin', 'PUC-ROOT-001')
            ON CONFLICT (id) DO UPDATE SET 
                email='vongchantha2001@gmail.com',
                role='Admin',
                employee_id='PUC-ROOT-001'
        """, (hashed,))
        
        depts = ['Computer Science & Tech', 'Business & Economics', 'Law & Public Affairs', 'Arts & Humanities', 'Information Technology']
        for dname in depts:
            cursor.execute("INSERT INTO admin_dashboard_department (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (dname,))
        
        conn.commit()
        return {"status": "success", "message": "System database cleaned. Official departments and Staff account synced."}
    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()

@app.post("/api/admin/wipe-inventory/")
def wipe_inventory():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM admin_dashboard_book")
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
