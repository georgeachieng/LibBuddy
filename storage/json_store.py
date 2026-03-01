import json
import os
from typing import List, Dict, Any, Optional

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


class JSONStore:
    def __init__(self, filename: str):
        self.filepath = os.path.join(DATA_DIR, filename)
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(self.filepath):
            self._write([])

    def _read(self) -> List[Dict[str, Any]]:
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            self._write([])
            return []

    def _write(self, data: List[Dict[str, Any]]) -> None:
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def load(self, filename: str = None) -> List[Dict[str, Any]]:
        if filename:
            store = JSONStore(filename)
            return store.all()
        return self.all()

    def all(self) -> List[Dict[str, Any]]:
        return self._read()

    def save(self, record: Dict[str, Any], auto_id: bool = True) -> Dict[str, Any]:
        data = self._read()
        if auto_id and "id" not in record:
            record["id"] = self._generate_id(data)
        data.append(record)
        self._write(data)
        return record

    def update(self, record_id: int, updates: Dict[str, Any]) -> bool:
        data = self._read()
        for item in data:
            if item.get("id") == record_id:
                item.update(updates)
                self._write(data)
                return True
        return False

    def delete(self, record_id: int) -> bool:
        data = self._read()
        new_data = [item for item in data if item.get("id") != record_id]
        if len(new_data) == len(data):
            return False  # nothing deleted
        self._write(new_data)
        return True

    def find_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        data = self._read()
        for item in data:
            if item.get("id") == record_id:
                return item
        return None

    def find_by_field(self, field: str, value: Any) -> Optional[Dict[str, Any]]:
        data = self._read()
        for item in data:
            if item.get(field) == value:
                return item
        return None

    def find_all_by_field(self, field: str, value: Any) -> List[Dict[str, Any]]:
        data = self._read()
        return [item for item in data if item.get(field) == value]

    def _generate_id(self, data: List[Dict[str, Any]]) -> int:
        if not data:
            return 1
        return max((item.get("id", 0) for item in data), default=0) + 1
