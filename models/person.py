"""Base Person class for LibBuddy."""


class Person:
    """Represents a person with name and email."""

    def __init__(self, name: str, email: str):
        """Initialize a Person.

        Args:
            name: The person's name
            email: The person's email address
        """
        self._name = None
        self._email = None
        self.name = name
        self.email = email

    @property
    def name(self) -> str:
        """Get the person's name."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Set the person's name."""
        if not value.strip():
            raise ValueError("Name cannot be empty.")
        self._name = value

    @property
    def email(self) -> str:
        """Get the person's email."""
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        """Set the person's email."""
        if "@" not in value or "." not in value:
            raise ValueError("Invalid email format.")
        self._email = value
