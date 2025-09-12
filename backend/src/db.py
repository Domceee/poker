import psycopg
import os

def get_db_connection():
    database_url = os.getenv("DATABASE_URL")

    conn = psycopg.connect(database_url)
    return conn

def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS hands (
                id UUID PRIMARY KEY,
                stack TEXT NOT NULL,
                hands TEXT NOT NULL,
                actions TEXT NOT NULL,
                result TEXT NOT NULL
            )
            """)
        conn.commit()