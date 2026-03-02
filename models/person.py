<<<<<<< HEAD
#write code here
=======
# models/person.py

class Person:
    def __init__(self, name: str, email: str):
        self._name = name
        self._email = None
        self.email = email  # use setter for validation

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        if not value.strip():
            raise ValueError("Name cannot be empty.")
        self._name = value

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str):
        if "@" not in value or "." not in value:
            raise ValueError("Invalid email format.")
        self._email = value
>>>>>>> 7d9e6de (Person/User inheritance,Book + BorrowRecord,properties/setters validation)
