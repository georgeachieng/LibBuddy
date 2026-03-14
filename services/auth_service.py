import hashlib
import os
import hmac
from datetime import datetime
from typing import Optional, Dict, Any

from utils.validators import require_non_empty, is_valid_email
from storage.json_store import JSONStore


class AuthService:
    def __init__(self):
        self.users_store = JSONStore("users.json")

        self.current_user = None

    def _hash_password(self, password: str, salt: bytes = None) -> tuple[str, str]:
        if salt is None:
            salt = os.urandom(16)

        hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120000)
        return salt.hex(), hashed.hex()

    def _verify_password(self, password: str, salt_hex: str, stored_hash_hex: str) -> bool:
        salt = bytes.fromhex(salt_hex)

        _, check_hash = self._hash_password(password, salt)

        return hmac.compare_digest(check_hash, stored_hash_hex)

    def register(
        self,
        name: str,
        email: str,
        password: str,
        role: str = "user",
        username: str | None = None,
    ) -> Dict[str, Any]:
        name = require_non_empty(name, "Name")
        email = require_non_empty(email, "Email").lower()
        password = require_non_empty(password, "Password")
        username = require_non_empty(username, "Username").lower() if username else email.split("@", 1)[0]

        if not is_valid_email(email):
            raise ValueError("Invalid email format.")

        users = self.users_store.all()

        if any(u["email"].lower() == email for u in users):
            raise ValueError("Email already registered.")

        if any(u.get("username", "").lower() == username for u in users):
            raise ValueError("Username already taken.")

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
            "id": self.users_store._generate_id(users),
            "name": name,
            "username": username,
            "email": email,
            "role": role,
            "salt": salt,
            "password_hash": password_hash,
            "created_at": datetime.now().isoformat(timespec="seconds")
        }

        self.users_store.save(new_user, auto_id=False)
        return new_user

    def login(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        identifier = require_non_empty(email, "Email or username").lower()
        password = require_non_empty(password, "Password")

        users = self.users_store.all()

        user = next(
            (
                u for u in users
                if u["email"].lower() == identifier or u.get("username", "").lower() == identifier
            ),
            None,
        )

        if not user:
            raise ValueError("No user found with that email or username.")

        if not self._verify_password(password, user["salt"], user["password_hash"]):
            raise ValueError("Incorrect password.")

        self.current_user = user
        return user

    def logout(self) -> None:
        self.current_user = None

    def list_users(self) -> list[Dict[str, Any]]:
        return self.users_store.all()

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        return self.current_user

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        return self.users_store.find_by_id(user_id)
