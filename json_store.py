from storage.json_store import JSONStore

__all__ = ["JSONStore"]
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save_list(filename, data):
    _ensure_data_dir()
    path = get_file_path(filename)
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

def generate_id(filename):
    data = load_list(filename)
    if not data:
        return 1
    return max(item.get('id', 0) for item in data) + 1

