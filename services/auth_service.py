
#write code here
import hashlib
import os
import hmac
from datetime import datetime

from utils.validators import require_non_empty, is_valid_email
from storage.json_store import JsonStore


class AuthService:
    def __init__(self):
        self.store = JsonStore()
        self.current_user = None

    def _hash_password(self, password: str, salt: bytes = None):
        if salt is None:
            salt = os.urandom(16)
        hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120000)
        return salt.hex(), hashed.hex()

    def _verify_password(self, password: str, salt_hex: str, stored_hash_hex: str) -> bool:
        salt = bytes.fromhex(salt_hex)
        _, check_hash = self._hash_password(password, salt)
        return hmac.compare_digest(check_hash, stored_hash_hex)

    def register(self, name: str, email: str, password: str, role: str = "user"):
        name = require_non_empty(name, "Name")
        email = require_non_empty(email, "Email").lower()
        password = require_non_empty(password, "Password")

        if not is_valid_email(email):
            raise ValueError("Invalid email format.")

        users = self.store.load("users.json")

        if any(u["email"].lower() == email for u in users):
            raise ValueError("Email already registered.")

        # First user becomes admin automatically
        if len(users) == 0:
            role = "admin"
        else:
            role = role.lower().strip()
            if role not in ("admin", "user"):
                role = "user"
            if role == "admin":
                if not self.current_user or self.current_user.get("role") != "admin":
                    raise PermissionError("Only an admin can create another admin.")

        salt, password_hash = self._hash_password(password)

        new_user = {
            "id": (max([u["id"] for u in users], default=0) + 1),
            "name": name,
            "email": email,
            "role": role,
            "salt": salt,
            "password_hash": password_hash,
            "created_at": datetime.now().isoformat(timespec="seconds")
        }

        users.append(new_user)
        self.store.save("users.json", users)
        return new_user

    def login(self, email: str, password: str):
        email = require_non_empty(email, "Email").lower()
        password = require_non_empty(password, "Password")

        users = self.store.load("users.json")
        user = next((u for u in users if u["email"].lower() == email), None)

        if not user:
            raise ValueError("No user found with that email.")

        if not self._verify_password(password, user["salt"], user["password_hash"]):
            raise ValueError("Incorrect password.")

        self.current_user = user
        return user

    def logout(self):
        self.current_user = None

    def list_users(self):
        return self.store.load("users.json")

    def get_current_user(self):
        return self.current_user
