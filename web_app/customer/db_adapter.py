#!/usr/bin/env python3
"""
PUC Digital Bookstore - Dual Database Adapter (SQLite3 + PostgreSQL)
Supports both local SQLite (puc_bookstore.db) and PostgreSQL (Render PostgreSQL / DATABASE_URL).
"""

import os
import sqlite3

try:
    from dotenv import load_dotenv
    load_dotenv()
    # Also load from backend/.env if available
    backend_env = os.path.join(os.path.dirname(__file__), '..', '..', 'backend', '.env')
    if os.path.exists(backend_env):
        load_dotenv(backend_env)
except Exception:
    pass

DB_PATH = ':memory:'

class DBConnectionWrapper:
    def __init__(self, conn, is_postgres=False):
        self.conn = conn
        self.is_postgres = is_postgres

    def cursor(self):
        cursor = self.conn.cursor()
        return DBCursorWrapper(cursor, self.is_postgres)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

class DBCursorWrapper:
    def __init__(self, cursor, is_postgres=False):
        self.cursor = cursor
        self.is_postgres = is_postgres
        self.last_query = ""

    def execute(self, query, params=None):
        if params is None:
            params = ()
        
        self.last_query = query

        # Convert ? placeholders to %s for PostgreSQL
        if self.is_postgres:
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

        try:
            self.cursor.execute(query, params)
        except Exception as err:
            if self.is_postgres:
                raise err
            if "RETURNING" in query and "syntax error" in str(err).lower():
                clean_query = query.split("RETURNING")[0].strip()
                self.cursor.execute(clean_query, params)
            else:
                raise err

        return self

    def executemany(self, query, params_list):
        if self.is_postgres and '?' in query:
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
    pg_url = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')
    
    if not pg_url and os.environ.get('DB_HOST') and os.environ.get('DB_NAME'):
        host = os.environ.get('DB_HOST')
        port = os.environ.get('DB_PORT', '5432')
        name = os.environ.get('DB_NAME')
        user = os.environ.get('DB_USER', 'postgres')
        password = os.environ.get('DB_PASSWORD', '')
        pg_url = f"postgresql://{user}:{password}@{host}:{port}/{name}"

    if pg_url:
        try:
            import psycopg2
            import psycopg2.extras
            conn = psycopg2.connect(pg_url)
            return DBConnectionWrapper(conn, is_postgres=True)
        except ImportError:
            print("[INFO] DATABASE_URL / PostgreSQL detected. Install psycopg2 via: pip install psycopg2-binary")
        except Exception as e:
            print(f"[WARN] PostgreSQL connection warning: {e}.")

    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    return DBConnectionWrapper(conn, is_postgres=False)
