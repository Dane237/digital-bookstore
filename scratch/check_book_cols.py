import sys, os
sys.path.append(os.getcwd())
from backend.main import get_db_connection
from psycopg2.extras import RealDictCursor

conn = get_db_connection()
cursor = conn.cursor(cursor_factory=RealDictCursor)

cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'admin_dashboard_book'
    ORDER BY ordinal_position;
""")
cols = cursor.fetchall()
print("=== admin_dashboard_book Columns ===")
for c in cols:
    print(f" - {c['column_name']} ({c['data_type']})")

cursor.execute("SELECT * FROM admin_dashboard_book LIMIT 1;")
sample_book = cursor.fetchone()
print("\n=== Sample Book Row ===")
if sample_book:
    for k, v in sample_book.items():
        print(f" {k}: {v}")

cursor.close()
conn.close()
