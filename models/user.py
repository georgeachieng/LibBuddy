import os
import hashlib

from models.person import Person


# User extends Person with auth-specific fields.
# Delete it and there is no real user model with passwords or roles.
class User(Person):
    def __init__(self, user_id: int, name: str, email: str, password: str, role: str = "user"):
        # Base class handles shared person validation.
        # Delete this and user objects stop validating core identity fields.
        super().__init__(name, email)

        # Explicit ids matter because services and tests use them for lookups.
        # Delete this and user objects lose their identity in the app.
        self.id = user_id

        # Route role through the setter so invalid values get blocked.
        # Delete this and the constructor can create nonsense permission states.
        self.role = role

        # Salt makes same-password users hash differently.
        # Remove it and password hashing gets much weaker.
        self._salt = os.urandom(16)

        # Store only the derived hash, never the raw password.
        # Delete this and auth becomes impossible or insecure.
        self._password_hash = self._hash_password(password)

    # Local hashing keeps model-level password checks deterministic.
    # Delete it and verify_password has nothing trustworthy to compare.
    def _hash_password(self, password: str) -> str:
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self._salt,
            100000
        ).hex()

    # This recomputes the candidate hash instead of storing plain passwords.
    # Delete it and password checks stop working.
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
        # Hard-limiting roles keeps permission logic small and sane.
        # Delete this and random strings can pass as "roles."
        if value not in ["user", "admin"]:
            raise ValueError("Role must be 'user' or 'admin'.")
        self._role = value
