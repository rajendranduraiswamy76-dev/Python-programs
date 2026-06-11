import os
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

load_dotenv()  # Load .env variables into environment

# Allow either a single DATABASE_URL or individual DB_* variables.
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # SQLAlchemy prefers the 'postgresql://' scheme; normalize if needed.
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    DB_HOST = os.getenv("DB_HOST")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
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

    DATABASE_URL = (
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

try:
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        future=True,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
except SQLAlchemyError as exc:
    raise ConnectionError(
        f"Unable to initialize SQLAlchemy engine: {exc}"
    ) from exc


@contextmanager
def get_session():
    """Provide a transactional SQLAlchemy session."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        raise ConnectionError(f"Database session error: {exc}") from exc
    finally:
        session.close()


@contextmanager
def get_connection():
    """Provide a raw SQLAlchemy connection from the engine."""
    try:
        with engine.connect() as connection:
            yield connection
    except SQLAlchemyError as exc:
        raise ConnectionError(f"Database connection error: {exc}") from exc


def test_connection():
    """Verify the database connection can be opened."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            return result.scalar()
    except SQLAlchemyError as exc:
        raise ConnectionError(f"Database test query failed: {exc}") from exc


if __name__ == "__main__":
    try:
        result = test_connection()
        print("Database connected successfully:", result)
    except Exception as err:
        print("Database connection failed:", err)
