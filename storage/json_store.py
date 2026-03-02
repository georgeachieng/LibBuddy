
"""JSON-based storage system for LibBuddy."""

import json
import os
from typing import List, Dict, Any, Optional

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


class JSONStore:
    """Handles JSON file storage with auto-generated IDs."""
    
    def __init__(self, filename: str):
        """Initialize JSONStore with a specific filename.
        
        Args:
            filename: Name of the JSON file in the data directory
        """
        self.filepath = os.path.join(DATA_DIR, filename)
        # Ensure data directory exists
        os.makedirs(DATA_DIR, exist_ok=True)
        # Initialize file if missing
        if not os.path.exists(self.filepath):
            self._write([])

    def _read(self) -> List[Dict[str, Any]]:
        """Read and parse JSON file."""
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            # Reset corrupted file safely
            self._write([])
            return []

    def _write(self, data: List[Dict[str, Any]]) -> None:
        """Write data to JSON file."""
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def load(self, filename: str = None) -> List[Dict[str, Any]]:
        """Load data from a specific file or current file.
        
        Args:
            filename: Optional filename to load from. If not provided, uses the current file.
            
        Returns:
            List of all records
        """
        if filename:
            store = JSONStore(filename)
            return store.all()
        return self.all()

    def all(self) -> List[Dict[str, Any]]:
        """Return all records from the JSON file."""
        return self._read()

    def save(self, record: Dict[str, Any], auto_id: bool = True) -> Dict[str, Any]:
        """Add a new record with optional auto-generated ID.
        
        Args:
            record: Dictionary to save
            auto_id: Whether to auto-generate the ID
            
        Returns:
            The saved record with ID
        """
        data = self._read()
        if auto_id and "id" not in record:
            record["id"] = self._generate_id(data)
        data.append(record)
        self._write(data)
        return record

    def update(self, record_id: int, updates: Dict[str, Any]) -> bool:
        """Update a record by ID.
        
        Args:
            record_id: ID of the record to update
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False if record not found
        """
        data = self._read()
        for item in data:
            if item.get("id") == record_id:
                item.update(updates)
                self._write(data)
                return True
        return False

    def delete(self, record_id: int) -> bool:
        """Delete a record by ID.
        
        Args:
            record_id: ID of the record to delete
            
        Returns:
            True if successful, False if record not found
        """
        data = self._read()
        new_data = [item for item in data if item.get("id") != record_id]
        if len(new_data) == len(data):
            return False  # nothing deleted
        self._write(new_data)
        return True

    def find_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """Find a record by ID.
        
        Args:
            record_id: ID of the record to find
            
        Returns:
            The record dictionary or None if not found
        """
        data = self._read()
        for item in data:
            if item.get("id") == record_id:
                return item
        return None

    def find_by_field(self, field: str, value: Any) -> Optional[Dict[str, Any]]:
        """Find a record by field value.
        
        Args:
            field: Field name to search
            value: Value to match
            
        Returns:
            The first matching record or None
        """
        data = self._read()
        for item in data:
            if item.get(field) == value:
                return item
        return None

    def find_all_by_field(self, field: str, value: Any) -> List[Dict[str, Any]]:
        """Find all records matching a field value.
        
        Args:
            field: Field name to search
            value: Value to match
            
        Returns:
            List of matching records
        """
        data = self._read()
        return [item for item in data if item.get(field) == value]

    def _generate_id(self, data: List[Dict[str, Any]]) -> int:
        """Generate a unique incremental ID.
        
        Args:
            data: List of existing records
            
        Returns:
            A new unique ID
        """
        if not data:
            return 1
        return max((item.get("id", 0) for item in data), default=0) + 1

