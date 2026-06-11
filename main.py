import sys
from typing import Any

from library_operations import (
    add_book,
    register_member,
    borrow_book,
    return_book,
    list_overdue_books,
)


def input_non_empty(prompt: str) -> str:
    while True:
        try:
            value = input(prompt).strip()
        except EOFError:
            print()
            continue
        if value:
            return value
        print("Input cannot be empty.")


def input_int(prompt: str) -> int:
    while True:
        s = input_non_empty(prompt)
        try:
            return int(s)
        except ValueError:
            print("Please enter a valid integer.")


def handle_add_book() -> None:
    title = input_non_empty("Title: ")
    author = input_non_empty("Author: ")
    isbn = input_non_empty("ISBN: ")
    total_copies = input_int("Total copies: ")
    res = add_book(title, author, isbn, total_copies)
    if res.get("success"):
        print(f"Success: {res.get('message')}. Book ID: {res.get('book_id')}")
    else:
        print(f"Error: {res.get('error')}")


def handle_register_member() -> None:
    first_name = input_non_empty("First name: ")
    last_name = input_non_empty("Last name: ")
    email = input_non_empty("Email: ")
    res = register_member(first_name, last_name, email)
    if res.get("success"):
        print(f"Success: {res.get('message')}. Member ID: {res.get('member_id')}")
    else:
        print(f"Error: {res.get('error')}")


def handle_borrow_book() -> None:
    member_id = input_int("Member ID: ")
    book_id = input_int("Book ID: ")
    res = borrow_book(member_id, book_id)
    if res.get("success"):
        print(f"Success: {res.get('message')}. Borrow Record ID: {res.get('borrow_record_id')}")
    else:
        print(f"Error: {res.get('error')}")


def handle_return_book() -> None:
    borrow_id = input_int("Borrow record ID: ")
    res = return_book(borrow_id)
    if res.get("success"):
        print(f"Success: {res.get('message')}")
    else:
        print(f"Error: {res.get('error')}")


def handle_view_overdue() -> None:
    res = list_overdue_books()
    if not res.get("success"):
        print(f"Error: {res.get('error')}")
        return
    overdue = res.get("overdue", [])
    if not overdue:
        print("No overdue books.")
        return
    print("Overdue books:")
    for od in overdue:
        print("-" * 60)
        print(f"Borrow ID: {od.get('borrow_id')}")
        print(f"Book ID: {od.get('book_id')} — {od.get('title')} by {od.get('author')}")
        print(f"Member: {od.get('member_first_name')} {od.get('member_last_name')} <{od.get('member_email')}>")
        print(f"Borrowed: {od.get('borrow_date')}")
        print(f"Due: {od.get('due_date')}")
    print("-" * 60)


def main() -> None:
    menu = (
        "\nLibrary CLI\n"
        "1. Add Book\n"
        "2. Register Member\n"
        "3. Borrow Book\n"
        "4. Return Book\n"
        "5. View Overdue\n"
        "6. Exit\n"
    )

    while True:
        try:
            print(menu)
            choice = input_non_empty("Choose an option (1-6): ")
            if choice == "1":
                handle_add_book()
            elif choice == "2":
                handle_register_member()
            elif choice == "3":
                handle_borrow_book()
            elif choice == "4":
                handle_return_book()
            elif choice == "5":
                handle_view_overdue()
            elif choice == "6":
                print("Exiting.")
                break
            else:
                print("Invalid choice. Enter a number between 1 and 6.")
        except KeyboardInterrupt:
            print("\nExiting.")
            break
        except Exception as exc:  # Catch unexpected errors to keep the loop alive
            print(f"An error occurred: {exc}")


if __name__ == "__main__":
    main()
