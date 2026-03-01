
#write code here
import json
import os

DATA_DIR = "data"

def _ensure_data_dir():
    """Creates the data directory if it doesn't exist."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def get_file_path(filename):
    return os.path.join(DATA_DIR, filename)

def load_list(filename):
    """Reads a JSON file and returns a list. Returns [] if empty/missing."""
    path = get_file_path(filename)
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save_list(filename, data):
    """Writes a list of dictionaries to a JSON file."""
    _ensure_data_dir()
    path = get_file_path(filename)
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

def generate_id(filename):
    """Calculates the next available ID based on existing records."""
    data = load_list(filename)
    if not data:
        return 1
    return max(item.get('id', 0) for item in data) + 1

