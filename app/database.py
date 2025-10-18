import os
import time
import psycopg2
import psycopg2.extras
import pandas as pd

from pathlib import Path
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
        con = psycopg2.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database,
            port=self.port,
        )

        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if parameters:
            cur.execute(sql, parameters)
        else:
            cur.execute(sql)

        # Fetch results only for SELECT queries
        if sql.strip().upper().startswith("SELECT"):
            results = cur.fetchall()
        else:
            results = []

        con.commit()
        cur.close()
        con.close()
        return results

    def create_tables(self):
        """Create a simple users table"""
        dir = Path(__file__).parent / "create_tables"
        for path in [
            "users.sql",
            "institutions.sql",
            "positions.sql",
            "experiences.sql",
            "skills.sql"
        ]:  # order matters
            with open(dir / path, "r") as query_file:
                q = "".join(query_file.readlines())
            self.query(q)

    def get_all_users(self):
        """Get all users from database"""
        return self.query("SELECT * FROM users ORDER BY id")


def insert_sample_data(db):
    """Insert some sample users"""
    dir = Path(__file__).parent / "data"
    for path in [
        "users.csv",
        "institutions.csv",
        "positions.csv",
        "experiences.csv",
        "skills.csv"
    ]:
        data = pd.read_csv(dir / path)
        for row in data.to_dict(orient="records"):
            try:
                stmt = f"""
                    INSERT INTO {path.split(".")[0]} 
                    ({", ".join(row.keys())})
                    VALUES
                    ({", ".join(["%s"] * len(row))})
                """
                db.query(stmt, list([v if not pd.isna(v) else None for v in row.values()]))
            except psycopg2.errors.UniqueViolation:
                pass


def wait_for_db(max_retries=6, delay=5):
    for _ in range(max_retries):
        try:
            db = Database()
            db.create_tables()
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
