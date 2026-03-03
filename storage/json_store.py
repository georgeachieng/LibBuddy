import json
import os
from typing import List, Dict, Any, Optional

# Central data dir keeps every JSON-backed feature writing to one predictable place.
# Delete this and file paths start drifting into chaos.
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


# This tiny storage layer is the repo's fake database.
# Delete it and most services lose persistence immediately.
class JSONStore:
    def __init__(self, filename: str):
        # Each store instance points at one concrete JSON file.
        # Delete this and the class has no clue where to read or write.
        self.filepath = os.path.join(DATA_DIR, filename)

        # Ensure the data folder exists before any write happens.
        # Delete this and first-run writes fail on missing directories.
        os.makedirs(DATA_DIR, exist_ok=True)

        # Seed missing files with an empty list so reads have a sane shape.
        # Remove this and first access can blow up or return weird state.
        if not os.path.exists(self.filepath):
            self._write([])

    # Private read helper so all storage methods share the same error handling.
    # Delete it and every caller has to reinvent file parsing.
    def _read(self) -> List[Dict[str, Any]]:
        try:
            # utf-8 keeps reads explicit and cross-platform safe enough.
            # Delete encoding and you are back to default-behavior roulette.
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            # Missing file should behave like empty storage, not a crash.
            # Delete this and startup becomes fragile.
            return []
        except json.JSONDecodeError:
            # Corrupt JSON gets reset instead of poisoning the whole app.
            # Delete this and one bad file bricks all dependent features.
            self._write([])
            return []

    # Private write helper so formatting and encoding stay consistent.
    # Delete it and every write path duplicates file logic.
    def _write(self, data: List[Dict[str, Any]]) -> None:
        with open(self.filepath, "w", encoding="utf-8") as f:
            # indent=4 keeps the files human-readable for debugging and grading.
            # Delete it and diffs get uglier, fast.
            json.dump(data, f, indent=4)

    # load exists mostly for compatibility with other branch code.
    # Delete it and some older call sites stop working.
    def load(self, filename: str = None) -> List[Dict[str, Any]]:
        if filename:
            # This lets one store temporarily read a different file if needed.
            # Delete it and compatibility helpers lose flexibility.
            store = JSONStore(filename)
            return store.all()
        return self.all()

    # all is the canonical "give me every record" method.
    # Delete it and the service layer loses its simplest read path.
    def all(self) -> List[Dict[str, Any]]:
        return self._read()

    # save appends a record and assigns an id when needed.
    # Delete it and no feature can create new persisted data.
    def save(self, record: Dict[str, Any], auto_id: bool = True) -> Dict[str, Any]:
        data = self._read()

        # Auto ids keep storage simple without a real database.
        # Remove this and callers have to manage every id manually.
        if auto_id and "id" not in record:
            record["id"] = self._generate_id(data)

        data.append(record)
        self._write(data)
        return record

    # update mutates one record in place by id.
    # Delete it and edit flows for users/books/reviews stop working.
    def update(self, record_id: int, updates: Dict[str, Any]) -> bool:
        data = self._read()
        for item in data:
            if item.get("id") == record_id:
                item.update(updates)
                self._write(data)
                return True
        return False

    # delete removes one record by id.
    # Delete it and cleanup flows leave dead data everywhere.
    def delete(self, record_id: int) -> bool:
        data = self._read()
        new_data = [item for item in data if item.get("id") != record_id]

        # No size change means no matching record existed.
        # Delete this check and you falsely report successful deletes.
        if len(new_data) == len(data):
            return False

        self._write(new_data)
        return True

    # ID lookup is the fastest common read path in this project.
    # Delete it and every service has to scan records manually.
    def find_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        data = self._read()
        for item in data:
            if item.get("id") == record_id:
                return item
        return None

    # Single-field lookup is a small convenience with big repetition savings.
    # Delete it and services get cluttered with the same loops.
    def find_by_field(self, field: str, value: Any) -> Optional[Dict[str, Any]]:
        data = self._read()
        for item in data:
            if item.get(field) == value:
                return item
        return None

    # Multi-match lookup supports history and filtered lists.
    # Delete it and callers start writing the same list comprehension everywhere.
    def find_all_by_field(self, field: str, value: Any) -> List[Dict[str, Any]]:
        data = self._read()
        return [item for item in data if item.get(field) == value]

    # ID generation is the fake-auto-increment for this file-based setup.
    # Delete it and new records collide or arrive without ids.
    def _generate_id(self, data: List[Dict[str, Any]]) -> int:
        if not data:
            return 1
        return max((item.get("id", 0) for item in data), default=0) + 1
