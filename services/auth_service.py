"""Authentication service for LibBuddy.

Person 1 scope - Stub implementation for CLI testing.
"""

import hashlib
import os
from typing import Any

# Ensure we can import from sibling packages
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.json_store import JsonStore


class AuthService:
    """Handles user registration, login, and authentication."""

    BORROW_LIMIT = 3  # Maximum books a user can borrow at once

    def __init__(self) -> None:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        self.user_store = JsonStore(os.path.join(data_dir, "users.json"))

    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def register(self, name: str, email: str, password: str, role: str = "user") -> dict[str, Any] | None:
        """Register a new user."""
        # Check if email already exists
        existing = self.user_store.find_by(email=email)
        if existing:
            return None

        user = {
            "name": name,
            "email": email,
            "password_hash": self._hash_password(password),
            "role": role,
        }
        return self.user_store.add(user)

    def login(self, email: str, password: str) -> dict[str, Any] | None:
        """Authenticate a user by email and password."""
        users = self.user_store.find_by(email=email)
        if not users:
            return None

        user = users[0]
        if user.get("password_hash") == self._hash_password(password):
            # Return user without password hash
            return {k: v for k, v in user.items() if k != "password_hash"}
        return None

    def logout(self) -> None:
        """Log out the current user (no-op for stateless auth)."""
        pass

    def list_users(self) -> list[dict[str, Any]]:
        """List all users (admin only)."""
        users = self.user_store.load()
        # Return users without password hashes
        return [{k: v for k, v in u.items() if k != "password_hash"} for u in users]

    def get_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        """Get a user by ID."""
        user = self.user_store.find_by_id(user_id)
        if user:
            return {k: v for k, v in user.items() if k != "password_hash"}
        return None
