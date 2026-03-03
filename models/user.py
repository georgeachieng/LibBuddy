import os
import hashlib

from models.person import Person


class User(Person):
    def __init__(self, user_id: int, name: str, email: str, password: str, role: str = "user"):
        super().__init__(name, email)

        self.id = user_id

        self.role = role

        self._salt = os.urandom(16)

        self._password_hash = self._hash_password(password)

    def _hash_password(self, password: str) -> str:
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self._salt,
            100000
        ).hex()

    def verify_password(self, password: str) -> bool:
        test_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self._salt,
            100000
        ).hex()
        return test_hash == self._password_hash

    @property
    def role(self) -> str:
        return self._role

    @role.setter
    def role(self, value: str):
        if value not in ["user", "admin"]:
            raise ValueError("Role must be 'user' or 'admin'.")
        self._role = value
