# LibBuddy

LibBuddy is a Python Command-Line Interface (CLI) app for managing a small digital library system.

The project was built for a summative group lab focused on object-oriented design, modular structure, authentication, JSON persistence, testing, and Git collaboration.

## Problem Statement

Manual tracking of books and borrowing records gets messy fast.
Availability becomes inaccurate, records drift, and nobody trusts the data.

LibBuddy fixes that with a CLI that lets users:
- register and log in securely
- browse and search books
- borrow and return books
- view borrowing history
- rate and review books they have actually borrowed

## Core Features

### Authentication and Access Control
- secure user registration and login
- password hashing before storage
- first registered user becomes admin automatically
- role-based access for admin and regular user actions
- decorator-based access checks for protected CLI actions

### Library Management
- add, update, and delete books
- track total and available copies
- borrow and return books with stored borrow records
- enforce a borrowing limit for each user
- view current borrows and full borrow history

### Reviews
- users can rate books from 1 to 5
- users can leave one review per book
- existing review updates instead of duplicating
- reviews are only allowed after the user has borrowed that book

### Persistence
- JSON file storage for users, books, borrow records, and reviews
- data survives app restarts without needing a database

## OOP and Structure

LibBuddy uses multiple interacting classes and a modular structure:
- `Person` is a base model
- `User` inherits from `Person`
- `Book`, `BorrowRecord`, and `Review` model core library behavior
- services handle auth, library actions, and reviews
- storage is separated into a reusable JSON store
- validators and decorators live in `utils/`

## Project Structure

```text
LibBuddy/
├── main.py
├── README.md
├── requirements.txt
├── data/
│   ├── users.json
│   ├── books.json
│   ├── borrow_records.json
│   └── reviews.json
├── models/
│   ├── person.py
│   ├── user.py
│   ├── book.py
│   ├── borrow_record.py
│   └── review.py
├── services/
│   ├── auth_service.py
│   ├── library_service.py
│   └── review_service.py
├── storage/
│   └── json_store.py
└── utils/
    ├── decorators.py
    └── validators.py
```

Note:
- The repo also includes package `__init__.py` files, tests, and one legacy root `json_store.py` file that is not the active storage layer.

## Requirements

- Python 3.10+
- `tabulate` for cleaner CLI tables
- JSON files for persistence
- `unittest` for automated testing

Install from the project root:

```bash
python3 -m pip install -r requirements.txt
```

## Running the App

```bash
python3 main.py
```

## Running Tests

```bash
python3 -m unittest discover -s tests -v
```

Current automated coverage includes:
- model validation and behavior
- auth, library, and review service rules
- CLI input and output flow with mocks

## External Package Usage

LibBuddy uses `tabulate` to render cleaner table output for:
- book listings
- borrow records
- user listings

If the package is not installed yet, the CLI falls back to plain text output instead of crashing.

## Example Flow

1. Register the first user
2. Log in as admin
3. Add books to the system
4. Register a regular user
5. Borrow and return books
6. View borrow history
7. Leave a review for a borrowed book

## Known Limits

- JSON storage is simple, not concurrent-safe
- there is no due-date or fines system
- there is no password reset flow
- the CLI is menu-driven instead of using subcommands
