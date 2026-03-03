# Dead code warning: this file looks like an old storage helper that got half-gutted.
# Deleting it might be harmless if nobody imports it, but touching it blind is how mystery bugs spawn.
from storage.json_store import JSONStore

# This export points callers at the real storage class.
# Delete it and any legacy import from this file breaks immediately.
__all__ = ["JSONStore"]

# Dead code warning: everything below looks orphaned and incomplete.
# It is commented lightly on purpose because the file is already structurally sketchy.
    try:
        # If this old helper still gets called somewhere, it expects JSON reads from `path`.
        # Delete it and that hidden caller crashes on import or call.
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        # This fallback stops corrupt/failed reads from throwing raw exceptions.
        # Remove it and old callers get noisier failures.
        return []

# Dead code warning: this function depends on helpers not defined in this file anymore.
# If somebody revives it without fixing that, it will fail fast.
def save_list(filename, data):
    _ensure_data_dir()
    path = get_file_path(filename)
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)


# Dead code warning: same issue here, legacy helper with missing dependencies.
# Leaving it undocumented would be meaner than the bug itself.
def generate_id(filename):
    data = load_list(filename)
    if not data:
        return 1
    return max(item.get('id', 0) for item in data) + 1
