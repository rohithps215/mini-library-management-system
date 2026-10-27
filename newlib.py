
import json
from datetime import datetime, timedelta
from pathlib import Path

# ---------------- FILE PATHS ----------------

BASE_DIR = Path(__file__).resolve().parent
BOOKS_FILE = BASE_DIR / "books.json"
RECORDS_FILE = BASE_DIR / "borrowing_records.txt"
RECORDS_DATA_FILE = BASE_DIR / "borrowing_records.json"


# ---------------- LOAD DATA ----------------

def load_books():
    try:
        with open(BOOKS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            print("Invalid books data. Starting with an empty library.")
            return []

        return data

    except FileNotFoundError:
        print("books.json not found. Starting with an empty library.")
        return []

    except (json.JSONDecodeError, OSError) as error:
        print("Could not load books:", error)
        return []


def load_records():
    try:
        with open(RECORDS_DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

        return []

    except FileNotFoundError:
        return []

    except (json.JSONDecodeError, OSError) as error:
        print("Could not load borrowing history:", error)
        return []


books = load_books()
borrowing_records = load_records()


# ---------------- SAVE BOOK DATA ----------------

def save_books():
    try:
        with open(BOOKS_FILE, "w", encoding="utf-8") as file:
            json.dump(books, file, indent=4, ensure_ascii=False)
        return True

    except OSError as error:
        print("Could not save books:", error)
        return False


# ---------------- SAVE BORROWING RECORDS ----------------

def save_records():
    try:
        # Save structured records so history survives restarts
        with open(RECORDS_DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(
                borrowing_records,
                file,
                indent=4,
                ensure_ascii=False
            )

        # Generate the required readable text file
        with open(RECORDS_FILE, "w", encoding="utf-8") as file:
            file.write("LIBRARY BORROWING RECORDS\n")
            file.write("=========================\n\n")

            if not borrowing_records:
                file.write("No borrowing records available.\n")

            for record in borrowing_records:
                file.write(f"Book ID: {record['book_id']}\n")
                file.write(f"Book: {record['book']}\n")
                file.write(f"Borrower: {record['borrower']}\n")
                file.write(f"Borrow date: {record['borrow_date']}\n")
                file.write(f"Due date: {record['due_date']}\n")
                file.write(
                    f"Return date: "
                    f"{record['return_date'] or 'Not returned'}\n"
                )
                file.write("-------------------------\n")

        print("Borrowing records saved successfully!")
        return True

    except (OSError, KeyError) as error:
        print("Could not save borrowing records:", error)
        return False


# ---------------- ADD BOOK ----------------

def add_book():
    try:
        book_id = int(input("Enter book ID: ").strip())
    except ValueError:
        print("Please enter a valid numeric ID.")
        return

    if any(book["id"] == book_id for book in books):
        print("Book ID already exists!")
        return

    title = input("Enter book title: ").strip()
    author = input("Enter author name: ").strip()

    if not title or not author:
        print("Title and author cannot be empty!")
        return

    new_book = {
        "id": book_id,
        "title": title,
        "author": author,
        "available": True,
        "borrower": None,
        "borrow_date": None,
        "due_date": None
    }

    books.append(new_book)

    if save_books():
        print("Book added successfully!")
    else:
        books.remove(new_book)
        print("Book was not added because saving failed.")


# ---------------- SEARCH BOOK ----------------

def search_book():
    search = input("Enter book title to search: ").strip().lower()

    if not search:
        print("Please enter a title.")
        return

    found = False

    for book in books:
        if search in book["title"].lower():
            print("\nBook found!")
            print("ID:", book["id"])
            print("Title:", book["title"])
            print("Author:", book["author"])
            print(
                "Status:",
                "Available" if book["available"] else "Borrowed"
            )

            if not book["available"]:
                print("Borrower:", book["borrower"])
                print("Due date:", book["due_date"])

            found = True

    if not found:
        print("Book not found.")


# ---------------- BORROW BOOK ----------------

def borrow_book():
    try:
        book_id = int(input("Enter book ID to borrow: ").strip())
    except ValueError:
        print("Please enter a valid book ID.")
        return

    book = next(
        (item for item in books if item["id"] == book_id),
        None
    )

    if book is None:
        print("Book not found!")
        return

    if not book["available"]:
        print("This book is already borrowed!")
        return

    borrower = input("Enter borrower name: ").strip()

    if not borrower:
        print("Borrower name cannot be empty!")
        return

    borrow_date = datetime.today().date()
    due_date = borrow_date + timedelta(days=14)

    record = {
        "book": book["title"],
        "book_id": book["id"],
        "borrower": borrower,
        "borrow_date": borrow_date.isoformat(),
        "due_date": due_date.isoformat(),
        "return_date": None
    }

    book["available"] = False
    book["borrower"] = borrower
    book["borrow_date"] = borrow_date.isoformat()
    book["due_date"] = due_date.isoformat()

    borrowing_records.append(record)

    if save_books() and save_records():
        print("Book borrowed successfully!")
        print("Borrow date:", borrow_date)
        print("Due date:", due_date)
    else:
        borrowing_records.remove(record)
        book["available"] = True
        book["borrower"] = None
        book["borrow_date"] = None
        book["due_date"] = None
        save_books()
        save_records()
        print("Borrowing could not be saved. Please try again.")


# ---------------- RETURN BOOK ----------------

def return_book():
    try:
        book_id = int(input("Enter book ID to return: ").strip())
    except ValueError:
        print("Please enter a valid book ID.")
        return

    book = next(
        (item for item in books if item["id"] == book_id),
        None
    )

    if book is None:
        print("Book not found!")
        return

    if book["available"]:
        print("This book is not currently borrowed!")
        return

    return_date = datetime.today().date()

    record = next(
        (
            item for item in reversed(borrowing_records)
            if item["book_id"] == book_id
            and item["return_date"] is None
        ),
        None
    )

    if record is None:
        print("No active borrowing record found for this book.")
        return

    old_values = (
        book["available"],
        book["borrower"],
        book["borrow_date"],
        book["due_date"],
        record["return_date"]
    )

    record["return_date"] = return_date.isoformat()

    book["available"] = True
    book["borrower"] = None
    book["borrow_date"] = None
    book["due_date"] = None

    if not save_books() or not save_records():
        (
            book["available"],
            book["borrower"],
            book["borrow_date"],
            book["due_date"],
            record["return_date"]
        ) = old_values

        print("Return could not be saved. Please try again.")
        return

    print("Book returned successfully!")
    print("Return date:", return_date)

    due_date = datetime.strptime(
        record["due_date"], "%Y-%m-%d"
    ).date()

    if return_date > due_date:
        print("This book was returned late.")
    else:
        print("Book returned on time.")


# ---------------- LIBRARY SUMMARY ----------------

def show_summary():
    total = len(books)
    available = sum(1 for book in books if book["available"])
    borrowed = total - available

    print("\n========== LIBRARY SUMMARY ==========")
    print("Total books:", total)
    print("Available books:", available)
    print("Borrowed books:", borrowed)
    print("Total borrowing records:", len(borrowing_records))


# ---------------- SHOW OVERDUE BOOKS ----------------

def show_overdue():
    today = datetime.today().date()
    found = False

    print("\n========== OVERDUE BOOKS ==========")

    for book in books:
        if not book["available"] and book["due_date"]:
            due_date = datetime.strptime(
                book["due_date"], "%Y-%m-%d"
            ).date()

            if today > due_date:
                print("Book:", book["title"])
                print("Borrower:", book["borrower"])
                print("Due date:", due_date)
                print("Days overdue:", (today - due_date).days)
                print("-------------------------")
                found = True

    if not found:
        print("No overdue books!")


# ---------------- SHOW ALL BOOKS ----------------

def show_all_books():
    if not books:
        print("No books available in the library.")
        return

    for book in books:
        print("\nID:", book["id"])
        print("Title:", book["title"])
        print("Author:", book["author"])
        print(
            "Status:",
            "Available" if book["available"] else "Borrowed"
        )

        if not book["available"]:
            print("Borrower:", book["borrower"])
            print("Due date:", book["due_date"])


# ---------------- SHOW BORROWING HISTORY ----------------

def show_history():
    if not borrowing_records:
        print("No borrowing records available.")
        return

    print("\n========== BORROWING HISTORY ==========")

    for record in borrowing_records:
        print("\nBook:", record["book"])
        print("Book ID:", record["book_id"])
        print("Borrower:", record["borrower"])
        print("Borrow date:", record["borrow_date"])
        print("Due date:", record["due_date"])
        print("Return date:", record["return_date"] or "Not returned")


# ---------------- MAIN MENU ----------------

def main():
    while True:
        print("\n====== MINI LIBRARY MANAGEMENT SYSTEM ======")
        print("1. Add Book")
        print("2. Search Book")
        print("3. Borrow Book")
        print("4. Return Book")
        print("5. Library Summary")
        print("6. Show Overdue Books")
        print("7. Save Borrowing Records")
        print("8. Show All Books")
        print("9. Show Borrowing History")
        print("10. Exit")

        try:
            choice = input("Enter your choice: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nInput interrupted. Saving data before exit...")
            save_books()
            save_records()
            break

        if choice == "1":
            add_book()

        elif choice == "2":
            search_book()

        elif choice == "3":
            borrow_book()

        elif choice == "4":
            return_book()

        elif choice == "5":
            show_summary()

        elif choice == "6":
            show_overdue()

        elif choice == "7":
            save_records()

        elif choice == "8":
            show_all_books()

        elif choice == "9":
            show_history()

        elif choice == "10":
            save_books()
            save_records()
            print("Thank you for using the library system!")
            break

        else:
            print("Invalid choice! Please enter a number from 1 to 10.")


# ---------------- RUN PROGRAM ----------------

if __name__ == "__main__":
    main()
