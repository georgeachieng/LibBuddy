"""JSON file storage utility for LibBuddy.

Person 3 scope - Stub implementation for CLI testing.
"""

import json
import os
from typing import Any


class JsonStore:
    """Simple JSON file storage."""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self._ensure_file()

    def _ensure_file(self) -> None:
        """Create the file if it doesn't exist."""
        if not os.path.exists(self.file_path):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, "w") as f:
                json.dump([], f)

    def load(self) -> list[dict[str, Any]]:
        """Load all records from the JSON file."""
        try:
            with open(self.file_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save(self, data: list[dict[str, Any]]) -> None:
        """Save all records to the JSON file."""
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def add(self, record: dict[str, Any]) -> dict[str, Any]:
        """Add a new record."""
        data = self.load()
        # Auto-generate ID if not present
        if "id" not in record:
            max_id = max((r.get("id", 0) for r in data), default=0)
            record["id"] = max_id + 1
        data.append(record)
        self.save(data)
        return record

    def find_by_id(self, record_id: int) -> dict[str, Any] | None:
        """Find a record by ID."""
        data = self.load()
        for record in data:
            if record.get("id") == record_id:
                return record
        return None

    def update(self, record_id: int, updates: dict[str, Any]) -> bool:
        """Update a record by ID."""
        data = self.load()
        for record in data:
            if record.get("id") == record_id:
                record.update(updates)
                self.save(data)
                return True
        return False

    def delete(self, record_id: int) -> bool:
        """Delete a record by ID."""
        data = self.load()
        original_len = len(data)
        data = [r for r in data if r.get("id") != record_id]
        if len(data) < original_len:
            self.save(data)
            return True
        return False

    def find_by(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Find records matching all given criteria."""
        data = self.load()
        results = []
        for record in data:
            if all(record.get(k) == v for k, v in kwargs.items()):
                results.append(record)
        return results
