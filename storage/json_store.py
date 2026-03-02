
#write code here

# storage/json_store.py

import json
import os
from typing import List, Dict, Any, Optional

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

class JSONStore:
    def __init__(self, filename: str):
        self.filepath = os.path.join(DATA_DIR, filename)
        # Ensure data directory exists
        os.makedirs(DATA_DIR, exist_ok=True)
        # Initialize file if missing
        if not os.path.exists(self.filepath):
            self._write([])

    def _read(self) -> List[Dict[str, Any]]:
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            # Reset corrupted file safely
            self._write([])
            return []

    def _write(self, data: List[Dict[str, Any]]):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def all(self) -> List[Dict[str, Any]]:
        """Return all records from the JSON file."""
        return self._read()

    def save(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new record with auto-generated ID."""
        data = self._read()
        record["id"] = self._generate_id(data)
        data.append(record)
        self._write(data)
        return record

    def update(self, record_id: int, updates: Dict[str, Any]) -> bool:
        """Update a record by ID. Returns True if successful."""
        data = self._read()
        for item in data:
            if item["id"] == record_id:
                item.update(updates)
                self._write(data)
                return True
        return False

    def delete(self, record_id: int) -> bool:
        """Delete a record by ID. Returns True if successful."""
        data = self._read()
        new_data = [item for item in data if item["id"] != record_id]
        if len(new_data) == len(data):
            return False  # nothing deleted
        self._write(new_data)
        return True

    def find_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """Find a record by ID."""
        data = self._read()
        for item in data:
            if item["id"] == record_id:
                return item
        return None

    def _generate_id(self, data: List[Dict[str, Any]]) -> int:
        """Generate a unique incremental ID."""
        if not data:
            return 1
        return max(item["id"] for item in data) + 1





        #wrote the  code here

