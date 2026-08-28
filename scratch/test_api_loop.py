import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv('web_app/backend/.env')
db_url = os.getenv('DATABASE_URL')

try:
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    query = """
        SELECT b.id AS book_id, b.isbn, b.title, b.author, b.price, b.stock_quantity, b.description, b.cover_img, b.created_at,
               STRING_AGG(d.name, ', ') as departments 
        FROM admin_dashboard_book b 
        LEFT JOIN admin_dashboard_book_departments bd ON b.id = bd.book_id 
        LEFT JOIN admin_dashboard_department d ON bd.department_id = d.id 
        WHERE 1=1
        GROUP BY b.id, b.isbn, b.title, b.author, b.price, b.stock_quantity, b.description, b.cover_img, b.created_at 
        ORDER BY b.created_at DESC
    """
    
    cursor.execute(query)
    books = cursor.fetchall()
    
    for b in books:
        depts = b.get('departments')
        print(f"Type of b: {type(b)}")
        # Try to set a new key
        b['department'] = depts.split(',')[0].strip() if depts else 'General'
        print(f"Set department for {b['title']}")
        
    print("Success!")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
