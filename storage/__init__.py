# Re-export the storage class so callers can import from `storage` directly.
# Delete it and package-level storage imports break.
from .json_store import JSONStore

__all__ = ["JSONStore"]
