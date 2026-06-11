"""Initialize the library database schema."""

from sqlalchemy import text
from database import get_connection


def init_db():
    """Create all required tables for the library system."""
    tables = [
        # Create books table
        """
        CREATE TABLE IF NOT EXISTS books (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            author VARCHAR(255) NOT NULL,
            isbn VARCHAR(20) UNIQUE NOT NULL,
            total_copies INTEGER NOT NULL,
            available_copies INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        # Create members table
        """
        CREATE TABLE IF NOT EXISTS members (
            id SERIAL PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        # Create borrow_records table
        """
        CREATE TABLE IF NOT EXISTS borrow_records (
            id SERIAL PRIMARY KEY,
            member_id INTEGER NOT NULL REFERENCES members(id),
            book_id INTEGER NOT NULL REFERENCES books(id),
            borrow_date TIMESTAMP NOT NULL,
            due_date TIMESTAMP NOT NULL,
            return_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
    ]

    try:
        with get_connection() as conn:
            for table_sql in tables:
                conn.execute(text(table_sql))
            conn.commit()
        print("✓ Database tables initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        return False


if __name__ == "__main__":
    init_db()
