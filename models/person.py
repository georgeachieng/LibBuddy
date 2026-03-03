"""Base Person class for LibBuddy."""


# This base model keeps shared name/email logic in one place.
# Delete it and child models start duplicating the same validation mess.
class Person:
    """Represents a person with name and email."""

    def __init__(self, name: str, email: str):
        """Initialize a Person.

        Args:
            name: The person's name
            email: The person's email address
        """
        # Start blank so the setters do the real validation work.
        # Delete this pattern and invalid constructor data can sneak in untouched.
        self._name = None
        self._email = None

        # Route constructor input through the setters on purpose.
        # Delete these lines and blank names / bad emails can bypass validation.
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
        # This check is basic, but it still blocks obvious junk.
        # Delete it and fake emails get stored like they are real.
        if "@" not in value or "." not in value:
            raise ValueError("Invalid email format.")
        self._email = value
