import os
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()  # Load .env variables into environment

DB_HOST = os.getenv("localhost")
DB_NAME = os.getenv("postgres")
DB_USER = os.getenv("postgres")
DB_PASSWORD = os.getenv("Vijaya$1")
DB_PORT = os.getenv("DB_PORT", "5432")

REQUIRED_VARS = {
    "DB_HOST": DB_HOST,
    "DB_NAME": DB_NAME,
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,
}

missing_vars = [name for name, value in REQUIRED_VARS.items() if not value]
if missing_vars:
    raise EnvironmentError(
        f"Missing required database environment variables: {', '.join(missing_vars)}"
    )

class Database:
    """PostgreSQL database connection manager using psycopg2 connection pooling."""

    _pool = None

    @classmethod
    def initialize_pool(cls, minconn=1, maxconn=10):
        if cls._pool is None:
            try:
                cls._pool = psycopg2.pool.SimpleConnectionPool(
                    minconn,
                    maxconn,
                    host=DB_HOST,
                    database=DB_NAME,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    port=DB_PORT,
                )
            except psycopg2.Error as exc:
                raise ConnectionError(
                    f"Unable to create connection pool: {exc.pgerror or exc}"
                ) from exc

        return cls._pool

    @classmethod
    def close_pool(cls):
        if cls._pool is not None:
            cls._pool.closeall()
            cls._pool = None

    @classmethod
    @contextmanager
    def get_connection(cls):
        if cls._pool is None:
            cls.initialize_pool()

        conn = None
        try:
            conn = cls._pool.getconn()
            yield conn
        except psycopg2.Error as exc:
            raise ConnectionError(f"Database connection error: {exc.pgerror or exc}") from exc
        finally:
            if conn is not None:
                cls._pool.putconn(conn)

    @classmethod
    @contextmanager
    def cursor(cls, cursor_factory=RealDictCursor):
        with cls.get_connection() as conn:
            with conn.cursor(cursor_factory=cursor_factory) as cur:
                try:
                    yield cur
                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise


def test_connection():
    """Simple test helper to verify connectivity."""
    try:
        Database.initialize_pool()
        with Database.cursor() as cur:
            cur.execute("SELECT version();")
            return cur.fetchone()
    except Exception as exc:
        raise ConnectionError(f"Database test query failed: {exc}") from exc


if __name__ == "__main__":
    try:
        result = test_connection()
        print("Database connected successfully:", result)
    except Exception as err:
        print("Database connection failed:", err)
