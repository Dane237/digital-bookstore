#!/usr/bin/env python3
"""
PUC Digital Bookstore - PostgreSQL Database Adapter
Exclusively connects to PostgreSQL (Render Cloud or Local PostgreSQL instance).
"""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
    # Also load from backend/.env if available
    backend_env = os.path.join(os.path.dirname(__file__), '..', '..', 'backend', '.env')
    if os.path.exists(backend_env):
        load_dotenv(backend_env)
except Exception:
    pass

class DBConnectionWrapper:
    def __init__(self, conn):
        self.conn = conn

    def cursor(self):
        cursor = self.conn.cursor()
        return DBCursorWrapper(cursor)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

class DBCursorWrapper:
    def __init__(self, cursor):
        self.cursor = cursor
        self.last_query = ""

    def execute(self, query, params=None):
        if params is None:
            params = ()
        
        self.last_query = query

        # Convert legacy placeholders and query syntax to PostgreSQL standard
        if '?' in query:
            query = query.replace('?', '%s')
        query = query.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        query = query.replace("INT PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        query = query.replace("AUTOINCREMENT", "")
        if "INSERT OR IGNORE INTO" in query:
            query = query.replace("INSERT OR IGNORE INTO", "INSERT INTO").rstrip(';').strip() + " ON CONFLICT DO NOTHING;"
        query = query.replace("datetime('now')", "NOW()")
        query = query.replace("GROUP_CONCAT(d.name, ', ')", "STRING_AGG(d.name, ', ')")
        query = query.replace("GROUP_CONCAT(d.name, ',')", "STRING_AGG(d.name, ',')")
        query = query.replace("GROUP_CONCAT", "STRING_AGG")

        self.cursor.execute(query, params)
        return self

    def executemany(self, query, params_list):
        if '?' in query:
            query = query.replace('?', '%s')
        self.cursor.executemany(query, params_list)
        return self

    def fetchone(self):
        try:
            row = self.cursor.fetchone()
        except Exception:
            row = None

        if row is None:
            return None
        if hasattr(row, 'keys'):
            return dict(row)
        if isinstance(row, dict):
            return row
        if self.cursor.description:
            colnames = [desc[0] for desc in self.cursor.description]
            return dict(zip(colnames, row))
        return {'id': getattr(self.cursor, 'lastrowid', 0)}

    def fetchall(self):
        try:
            rows = self.cursor.fetchall()
        except Exception:
            rows = []

        if not rows:
            return []
        if hasattr(rows[0], 'keys'):
            return [dict(r) for r in rows]
        if isinstance(rows[0], dict):
            return rows
        if self.cursor.description:
            colnames = [desc[0] for desc in self.cursor.description]
            return [dict(zip(colnames, r)) for r in rows]
        return []

    @property
    def lastrowid(self):
        return getattr(self.cursor, 'lastrowid', None)

def get_db():
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError:
        raise RuntimeError("PostgreSQL driver 'psycopg2' is missing. Install via: pip install psycopg2-binary")

    pg_url = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')
    
    if pg_url:
        try:
            conn = psycopg2.connect(pg_url)
            return DBConnectionWrapper(conn)
        except Exception as e:
            raise RuntimeError(f"Failed to connect to PostgreSQL at DATABASE_URL: {e}")

    # Fallback to individual DB params or local PostgreSQL defaults
    host = os.environ.get('DB_HOST', 'localhost')
    port = os.environ.get('DB_PORT', '5432')
    name = os.environ.get('DB_NAME', 'puc_bookstore')
    user = os.environ.get('DB_USER', 'postgres')
    password = os.environ.get('DB_PASSWORD', 'pass123')

    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=name,
            user=user,
            password=password,
            connect_timeout=10
        )
        return DBConnectionWrapper(conn)
    except Exception as e:
        raise RuntimeError(
            f"Could not connect to PostgreSQL database '{name}' on {host}:{port}. "
            f"Please verify PostgreSQL is running. Details: {e}"
        )

