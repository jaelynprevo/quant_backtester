import psycopg2
import psycopg2.extras

def get_connection():
    try:
        conn = psycopg2.connect(
            database="postgres",
            user="jaelyn",
            password="password",
            host="127.0.0.1",
            port=5432,
        )
        return conn
    except Exception as e:
        # print out the actual exception for debugging
        print("❌ Could not connect to PostgreSQL:", e)
        return None

conn = get_connection()
if conn:
    print("✅ Connection to PostgreSQL established successfully.")
else:
    print("⚠️ Connection to PostgreSQL encountered an error.")
