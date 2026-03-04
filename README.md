# LibBuddy

LibBuddy is a Python CLI library system with:
- registration and login
- password hashing
- admin vs member menus
- book borrowing and returns
- review and rating support
- Open Library search/import for quick catalog seeding
- JSON file persistence
- Optional `tabulate` support for cleaner table views when installed

## Project Structure

```text
libbuddy/
  main.py
  README.md
  cli/
  data/
    users.json
    books.json
    borrow_records.json
    reviews.json
  models/
  services/
  storage/
  utils/
  tests/
```

## Run It

```bash
python3 main.py
```

## Run Tests

```bash
python3 -m unittest discover -s tests -v
```

## Demo Data

This branch ships with:
- 6 sample users
- 20 books
- 14 borrow records
- 10 reviews

Sample login:
- Admin: `joyburgei` / `JoyAdmin123!`
- Member: `abdalabakari` / `Reader123!`

You can also log in with the matching email instead of the username.

## Notes

- The first registered user becomes admin.
- Members can only review books they have actually borrowed.
- Borrowing is capped at 3 active books per user.
- Admins can import books from Open Library without editing JSON by hand.
