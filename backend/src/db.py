import psycopg

def get_db_connection():
    conn = psycopg.connect(
        dbname="poker_db",
        user="user",
        password="password",
        host="db", 
        port=5432
    )

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