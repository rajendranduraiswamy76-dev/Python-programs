from datetime import datetime, timedelta
from typing import Dict, Any, List

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database import get_session


DEFAULT_LOAN_DAYS = 14


def add_book(title: str, author: str, isbn: str, total_copies: int) -> Dict[str, Any]:
    """Insert a new book into the `books` table.

    Expects a `books` table with columns: id, title, author, isbn, total_copies, available_copies
    """
    try:
        with get_session() as session:
            stmt = text(
                "INSERT INTO books (title, author, isbn, total_copies, available_copies)"
                " VALUES (:title, :author, :isbn, :total_copies, :available_copies) RETURNING id"
            )
            params = {
                "title": title,
                "author": author,
                "isbn": isbn,
                "total_copies": int(total_copies),
                "available_copies": int(total_copies),
            }
            result = session.execute(stmt, params)
            book_id = result.scalar_one()
        return {"success": True, "message": "Book added", "book_id": int(book_id)}
    except SQLAlchemyError as exc:
        return {"success": False, "error": str(exc)}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def register_member(first_name: str, last_name: str, email: str) -> Dict[str, Any]:
    """Register a new library member.

    Expects a `members` table with columns: id, first_name, last_name, email
    """
    try:
        with get_session() as session:
            stmt = text(
                "INSERT INTO members (first_name, last_name, email) VALUES (:fn, :ln, :email) RETURNING id"
            )
            params = {"fn": first_name, "ln": last_name, "email": email}
            result = session.execute(stmt, params)
            member_id = result.scalar_one()
        return {"success": True, "message": "Member registered", "member_id": int(member_id)}
    except SQLAlchemyError as exc:
        return {"success": False, "error": str(exc)}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def borrow_book(member_id: int, book_id: int, loan_days: int = DEFAULT_LOAN_DAYS) -> Dict[str, Any]:
    """Borrow a book using a transaction.

    - Checks available_copies > 0 (row locked FOR UPDATE)
    - Decrements available_copies
    - Inserts a record into `borrow_records` with borrow_date and due_date

    Expects `borrow_records` with columns: id, member_id, book_id, borrow_date, due_date, return_date
    """
    try:
        with get_session() as session:
            # Lock the book row to prevent race conditions
            sel = text("SELECT available_copies FROM books WHERE id = :book_id FOR UPDATE")
            row = session.execute(sel, {"book_id": int(book_id)}).fetchone()
            if row is None:
                return {"success": False, "error": "Book not found"}
            available = row[0]
            if available <= 0:
                return {"success": False, "error": "No copies available"}

            # Decrement available_copies
            upd = text(
                "UPDATE books SET available_copies = available_copies - 1 WHERE id = :book_id"
            )
            session.execute(upd, {"book_id": int(book_id)})

            borrow_date = datetime.utcnow()
            due_date = borrow_date + timedelta(days=int(loan_days))

            ins = text(
                "INSERT INTO borrow_records (member_id, book_id, borrow_date, due_date)"
                " VALUES (:member_id, :book_id, :borrow_date, :due_date) RETURNING id"
            )
            params = {
                "member_id": int(member_id),
                "book_id": int(book_id),
                "borrow_date": borrow_date,
                "due_date": due_date,
            }
            result = session.execute(ins, params)
            borrow_id = result.scalar_one()

        return {"success": True, "message": "Book borrowed", "borrow_record_id": int(borrow_id)}
    except SQLAlchemyError as exc:
        return {"success": False, "error": str(exc)}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def return_book(borrow_record_id: int) -> Dict[str, Any]:
    """Return a book using a transaction.

    - Sets `return_date` on the borrow_records row (if not already set)
    - Increments the book's available_copies by 1
    """
    try:
        with get_session() as session:
            # Get borrow record and lock the related book row
            sel_br = text(
                "SELECT book_id, return_date FROM borrow_records WHERE id = :br_id FOR UPDATE"
            )
            br = session.execute(sel_br, {"br_id": int(borrow_record_id)}).fetchone()
            if br is None:
                return {"success": False, "error": "Borrow record not found"}
            book_id = br[0]
            return_date_existing = br[1]
            if return_date_existing is not None:
                return {"success": False, "error": "Book already returned"}

            # Update return_date
            now = datetime.utcnow()
            upd_br = text(
                "UPDATE borrow_records SET return_date = :now WHERE id = :br_id"
            )
            session.execute(upd_br, {"now": now, "br_id": int(borrow_record_id)})

            # Increment available_copies
            upd_book = text(
                "UPDATE books SET available_copies = available_copies + 1 WHERE id = :book_id"
            )
            session.execute(upd_book, {"book_id": int(book_id)})

        return {"success": True, "message": "Book returned"}
    except SQLAlchemyError as exc:
        return {"success": False, "error": str(exc)}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def list_overdue_books() -> Dict[str, Any]:
    """List overdue books: borrow_records with return_date IS NULL and due_date < now()."""
    try:
        with get_session() as session:
            stmt = text(
                "SELECT br.id as borrow_id, br.member_id, br.book_id, br.borrow_date, br.due_date, b.title, b.author, m.first_name, m.last_name, m.email"
                " FROM borrow_records br"
                " JOIN books b ON br.book_id = b.id"
                " JOIN members m ON br.member_id = m.id"
                " WHERE br.return_date IS NULL AND br.due_date < :now"
            )
            now = datetime.utcnow()
            rows = session.execute(stmt, {"now": now}).fetchall()

            overdue: List[Dict[str, Any]] = []
            for r in rows:
                overdue.append(
                    {
                        "borrow_id": int(r[0]),
                        "member_id": int(r[1]),
                        "book_id": int(r[2]),
                        "borrow_date": r[3].isoformat() if r[3] else None,
                        "due_date": r[4].isoformat() if r[4] else None,
                        "title": r[5],
                        "author": r[6],
                        "member_first_name": r[7],
                        "member_last_name": r[8],
                        "member_email": r[9],
                    }
                )

        return {"success": True, "overdue": overdue}
    except SQLAlchemyError as exc:
        return {"success": False, "error": str(exc)}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


if __name__ == "__main__":
    # Quick self-check (won't modify DB if called without arguments)
    print("library_operations module loaded. Use functions programmatically.")
