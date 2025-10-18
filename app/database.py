import os
import time
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()


class Database:
    def __init__(self):
        self.host       = os.getenv("DATABASE_HOST")
        self.user       = os.getenv("DATABASE_USER")
        self.port       = os.getenv("DATABASE_PORT")
        self.database   = os.getenv("DATABASE_NAME")
        self.password   = os.getenv("DATABASE_PASSWORD")

    def query(self, sql, parameters=None):
        """Execute a database query"""
        conn = psycopg2.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database,
            port=self.port,
        )

        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if parameters:
            cursor.execute(sql, parameters)
        else:
            cursor.execute(sql)

        # Fetch results only for SELECT queries
        if sql.strip().upper().startswith("SELECT"):
            results = cursor.fetchall()
        else:
            results = []

        conn.commit()
        cursor.close()
        conn.close()
        return results


    def create_tables(self):
        """Create a simple users table"""
        self.query(
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        print("✅ Table 'users' created successfully!")


    def get_all_users(self):
        """Get all users from database"""
        return self.query("SELECT * FROM users ORDER BY id")


def insert_sample_data(db):
    """Insert some sample users"""
    users = [
        ("Alice", "alice@email.com"),
        ("Bob", "bob@email.com"),
        ("Charlie", "charlie@email.com"),
    ]

    for name, email in users:
        try:
            db.query("INSERT INTO users (name, email) VALUES (%s, %s)", (name, email))
        except psycopg2.errors.UniqueViolation:
            # User already exists, skip
            pass

    print("✅ Sample data inserted!")


def wait_for_db(max_retries=6, delay=5):
    for _ in range(max_retries):
        try:
            db = Database()
            db.query("SELECT 1")
            return db
        except:
            time.sleep(delay)
    
    raise Exception("DB connection error. Max retries reached.")


def init_db():
    db = wait_for_db()
    insert_sample_data(db)


if __name__ == "__main__":
    print("Initializing DB with sample data...")
    init_db()
