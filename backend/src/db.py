import psycopg
import os
from psycopg import sql

def get_db_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg.connect(database_url)

def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS hands (
                id TEXT PRIMARY KEY,
                stack TEXT NOT NULL,
                hands TEXT NOT NULL,
                actions TEXT NOT NULL,
                result TEXT NOT NULL
            )
            """)
        conn.commit()