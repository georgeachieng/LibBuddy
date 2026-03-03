# LibBuddy

LibBuddy is a Python command-line library management system built as a group project.

It supports:
- user registration and login
- role-based access for admins and regular users
- book management
- borrowing and returning books
- review and rating support
- JSON-based persistence

## Project Goal

This project was built to demonstrate:
- object-oriented programming
- modular Python structure
- persistent data storage with JSON
- authentication and role-based access
- CLI-driven user flows
- collaborative development with feature branches

## Tech Stack

- Python 3
- Standard library only
- JSON files for persistence
- `unittest` for tests

## Features

### Authentication
- Register a new user
- Login with hashed password verification
- Logout
- First registered user becomes admin automatically
- Prevent duplicate email registration

### Admin Features
- Add books
- Update total copies
- Delete books
- View all users
- View all borrow records
- View book reviews

### User Features
- List all books
- Search books by title or author
- Borrow books
- Return books
- View personal borrow history
- View current borrowed books
- Add reviews
- View reviews for a book

### Persistence
- Users are stored in `data/users.json`
- Books are stored in `data/books.json`
- Borrow records are stored in `data/borrow_records.json`
- Reviews are stored in `data/reviews.json`

## Project Structure

```text
LibBuddy/
├── main.py
├── __init__.py
├── README.md
├── data/
│   ├── books.json
│   ├── borrow_records.json
│   ├── reviews.json
│   └── users.json
├── models/
│   ├── __init__.py
│   ├── book.py
│   ├── borrow_record.py
│   ├── person.py
│   ├── review.py
│   └── user.py
├── services/
│   ├── __init__.py
│   ├── auth_service.py
│   ├── library_service.py
│   └── review_service.py
├── storage/
│   ├── __init__.py
│   └── json_store.py
├── tests/
│   ├── test_cli.py
│   ├── test_models.py
│   └── test_services.py
└── utils/
    ├── __init__.py
    ├── decorators.py
    └── validators.py
```

## Running the App

From the project root:

```bash
python3 main.py
```

## Running Tests

From the project root:

```bash
python3 -m unittest discover -s tests -v
```

Current test coverage includes:
- model validation and behavior
- auth, library, and review services
- basic CLI interaction flow with mocks

## Example CLI Flow

### First Run
1. Start the app
2. Register the first user
3. That first user becomes admin automatically
4. Log in and manage books

### Regular User Flow
1. Register a normal user
2. Log in
3. Browse or search books
4. Borrow a book
5. Return a book later
6. Leave a review

## Data Notes

- This application uses JSON files instead of a database.
- Data persists between runs unless the JSON files are manually edited or cleared.
- Passwords are hashed before storage.

## Limitations

- No external database
- No password reset flow
- No overdue fines or due-date tracking
- No concurrency protection for simultaneous writes
- The root `json_store.py` file is legacy-looking and not the active storage layer

## Submission Notes

This repository includes:
- modular source code
- persistent data files
- automated tests
- a working CLI entrypoint

This covers the core project requirements without overstating the scope of the system.
