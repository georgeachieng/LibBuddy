"""Authentication service for LibBuddy."""

import hashlib
import os
import hmac
from datetime import datetime
from typing import Optional, Dict, Any

from utils.validators import require_non_empty, is_valid_email
from storage.json_store import JSONStore


class AuthService:
    """Handles user authentication and registration."""
    
    def __init__(self):
        """Initialize AuthService with JSON stores for users."""
        self.users_store = JSONStore("users.json")
        self.current_user = None

    def _hash_password(self, password: str, salt: bytes = None) -> tuple[str, str]:
        """Hash a password with PBKDF2.
        
        Args:
            password: The password to hash
            salt: Optional salt bytes. If None, generates a new one
            
        Returns:
            Tuple of (salt_hex, hash_hex)
        """
        if salt is None:
            salt = os.urandom(16)
        hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120000)
        return salt.hex(), hashed.hex()

    def _verify_password(self, password: str, salt_hex: str, stored_hash_hex: str) -> bool:
        """Verify a password against a stored hash.
        
        Args:
            password: The password to verify
            salt_hex: The salt hex string
            stored_hash_hex: The stored hash hex string
            
        Returns:
            True if password matches, False otherwise
        """
        salt = bytes.fromhex(salt_hex)
        _, check_hash = self._hash_password(password, salt)
        return hmac.compare_digest(check_hash, stored_hash_hex)

    def register(self, name: str, email: str, password: str, role: str = "user") -> Dict[str, Any]:
        """Register a new user.
        
        Args:
            name: User's name
            email: User's email
            password: User's password
            role: User's role ('user' or 'admin')
            
        Returns:
            Dictionary with the new user's data
            
        Raises:
            ValueError: If validation fails or email already exists
            PermissionError: If trying to create admin without permission
        """
        name = require_non_empty(name, "Name")
        email = require_non_empty(email, "Email").lower()
        password = require_non_empty(password, "Password")

        if not is_valid_email(email):
            raise ValueError("Invalid email format.")

        users = self.users_store.all()

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
            "id": self.users_store._generate_id(users),
            "name": name,
            "email": email,
            "role": role,
            "salt": salt,
            "password_hash": password_hash,
            "created_at": datetime.now().isoformat(timespec="seconds")
        }

        self.users_store.save(new_user, auto_id=False)
        return new_user

    def login(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Login a user.
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            Dictionary with user data if successful, None otherwise
            
        Raises:
            ValueError: If validation fails or credentials are invalid
        """
        email = require_non_empty(email, "Email").lower()
        password = require_non_empty(password, "Password")

        users = self.users_store.all()
        user = next((u for u in users if u["email"].lower() == email), None)

        if not user:
            raise ValueError("No user found with that email.")

        if not self._verify_password(password, user["salt"], user["password_hash"]):
            raise ValueError("Incorrect password.")

        self.current_user = user
        return user

    def logout(self) -> None:
        """Logout the current user."""
        self.current_user = None

    def list_users(self) -> list[Dict[str, Any]]:
        """Get all users (admin only).
        
        Returns:
            List of all users
        """
        return self.users_store.all()

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get the currently logged-in user.
        
        Returns:
            Current user dict or None if not logged in
        """
        return self.current_user

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get a user by ID.
        
        Args:
            user_id: The user's ID
            
        Returns:
            User dictionary or None if not found
        """
        return self.users_store.find_by_id(user_id)
