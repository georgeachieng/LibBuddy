import hashlib
import os
import hmac
from datetime import datetime
from typing import Optional, Dict, Any

# Validation stays outside the service so input rules do not get copy-pasted everywhere.
# Delete these imports and auth starts trusting bad data way too early.
from utils.validators import require_non_empty, is_valid_email
from storage.json_store import JSONStore


# This service owns registration, login, and in-memory session state.
# Delete it and the rest of the app loses its auth backbone.
class AuthService:
    def __init__(self):
        # Users persist to JSON so accounts survive app restarts.
        # Remove this and registration becomes fake because nothing sticks.
        self.users_store = JSONStore("users.json")

        # This tracks the logged-in user for role checks and admin-only flows.
        # Delete it and permissions stop having any real state.
        self.current_user = None

    # Password hashing exists so raw passwords never get stored directly.
    # Delete this and you are basically saving secrets in plain sight. Bad look.
    def _hash_password(self, password: str, salt: bytes = None) -> tuple[str, str]:
        # Fresh salt makes identical passwords hash differently.
        # Remove this and password reuse becomes way easier to spot and abuse.
        if salt is None:
            salt = os.urandom(16)

        # PBKDF2 slows brute force attacks down on purpose.
        # Replace/remove it and password security gets paper-thin fast.
        hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120000)
        return salt.hex(), hashed.hex()

    # This re-hashes login input and compares safely against the stored hash.
    # Delete it and login can never verify credentials correctly.
    def _verify_password(self, password: str, salt_hex: str, stored_hash_hex: str) -> bool:
        # Stored salt comes back as hex, so convert it before reusing it.
        # Remove this and the hash check breaks on every login attempt.
        salt = bytes.fromhex(salt_hex)

        # Recreate the candidate hash using the exact same salt.
        # Delete this and password comparison becomes nonsense.
        _, check_hash = self._hash_password(password, salt)

        # compare_digest avoids sketchy timing leaks from normal string comparison.
        # Remove it and auth gets a little sloppier than it needs to be.
        return hmac.compare_digest(check_hash, stored_hash_hex)

    # Registration validates input, enforces uniqueness, and writes a new user record.
    # Delete it and there is no supported path for new accounts.
    def register(self, name: str, email: str, password: str, role: str = "user") -> Dict[str, Any]:
        # Trim and validate early so the JSON layer only gets sane input.
        # Remove these and weird whitespace or blanks leak into stored users.
        name = require_non_empty(name, "Name")
        email = require_non_empty(email, "Email").lower()
        password = require_non_empty(password, "Password")

        # Email format check stops obvious junk before persistence.
        # Delete it and your user data gets messy fast.
        if not is_valid_email(email):
            raise ValueError("Invalid email format.")

        # Pull all users so we can enforce email uniqueness and id generation.
        # Remove this and duplicates slide in or id logic breaks later.
        users = self.users_store.all()

        # Email uniqueness matters because login assumes one account per email.
        # Delete this and auth becomes ambiguous in the worst possible way.
        if any(u["email"].lower() == email for u in users):
            raise ValueError("Email already registered.")

        # First user becomes admin so the app is not born with zero admins.
        # Delete this and nobody may be able to manage the system cleanly.
        if len(users) == 0:
            role = "admin"
        else:
            # Normalize role input because users type weird stuff. Always.
            # Remove this and harmless casing/spacing starts causing pointless bugs.
            role = role.lower().strip()
            if role not in ("admin", "user"):
                # Unknown roles get downgraded instead of poisoning auth logic.
                # Delete this and random role strings can leak into permission checks.
                role = "user"

            # Only admins can mint more admins. Pretty basic containment rule.
            # Delete this and anyone can escalate privileges by passing role="admin".
            if role == "admin":
                if not self.current_user or self.current_user.get("role") != "admin":
                    raise PermissionError("Only an admin can create another admin.")

        # Hashing happens before the record is built so plain text never touches storage.
        # Delete this and passwords end up exposed or login logic breaks.
        salt, password_hash = self._hash_password(password)

        # Record shape is explicit so other services know what to expect.
        # Remove fields here and reads break later in subtle ways.
        new_user = {
            "id": self.users_store._generate_id(users),
            "name": name,
            "email": email,
            "role": role,
            "salt": salt,
            "password_hash": password_hash,
            "created_at": datetime.now().isoformat(timespec="seconds")
        }

        # auto_id=False matters because we already generated the id ourselves.
        # Delete that flag and the store may duplicate or override ids.
        self.users_store.save(new_user, auto_id=False)
        return new_user

    # Login checks user existence, verifies password, then sets session state.
    # Delete it and the app has auth data but no way to use it.
    def login(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        # Same validation story as register: catch junk before business logic.
        # Remove this and auth errors get noisier and less predictable.
        email = require_non_empty(email, "Email").lower()
        password = require_non_empty(password, "Password")

        # Read user list fresh so login sees the current file state.
        # Delete this and login has nothing to authenticate against.
        users = self.users_store.all()

        # next(..., None) gives us a clean "not found" path instead of a crash.
        # Delete the default and bad emails raise StopIteration like a gremlin.
        user = next((u for u in users if u["email"].lower() == email), None)

        if not user:
            raise ValueError("No user found with that email.")

        # Password verification is the whole point of login.
        # Delete it and any password works, which is obviously game over.
        if not self._verify_password(password, user["salt"], user["password_hash"]):
            raise ValueError("Incorrect password.")

        # This is the actual session handoff other code relies on.
        # Delete it and auth "succeeds" but menus still act logged out.
        self.current_user = user
        return user

    # Logout only needs to clear in-memory state. Simple, but very not optional.
    # Delete it and users stay authenticated until process death.
    def logout(self) -> None:
        self.current_user = None

    # Listing users supports admin views and tests.
    # Delete it and account visibility disappears from the app layer.
    def list_users(self) -> list[Dict[str, Any]]:
        return self.users_store.all()

    # This gives callers the active session without poking internals directly.
    # Delete it and every caller starts reaching into service state manually.
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        return self.current_user

    # ID lookup is used anywhere the app needs one user record fast.
    # Delete it and callers have to scan the whole user file themselves.
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        return self.users_store.find_by_id(user_id)
