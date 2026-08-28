import os
import psycopg2
import json
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime
from decimal import Decimal

load_dotenv('web_app/backend/.env')
db_url = os.getenv('DATABASE_URL')

def serialize_book(b):
    book_dict = dict(b)
    # This matches the new logic in main.py
    if book_dict.get('price'):
        book_dict['price'] = float(book_dict['price'])
    if book_dict.get('created_at') and isinstance(book_dict['created_at'], datetime):
        book_dict['created_at'] = book_dict['created_at'].isoformat()
    return book_dict

try:
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    query = "SELECT * FROM admin_dashboard_book LIMIT 1"
    cursor.execute(query)
    book = cursor.fetchone()
    
    print("Original book data:", book)
    
    # Simulate serialization
    serialized = serialize_book(book)
    print("\nSerialized book data:", serialized)
    
    # Test JSON dumps
    json_output = json.dumps(serialized)
    print("\nJSON successful:", json_output[:100], "...")
    
    cursor.close()
    conn.close()
    print("\nLogic verified!")
except Exception as e:
    print(f"Error: {e}")
