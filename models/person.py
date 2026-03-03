class Person:    
    def __init__(self, name: str, email: str):
        self._name = name
        self._email = None
        self.email = email  

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if not value.strip():
            raise ValueError("Name cannot be empty.")
        self._name = value

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        if "@" not in value or "." not in value:
            raise ValueError("Invalid email format.")
        self._email = value

