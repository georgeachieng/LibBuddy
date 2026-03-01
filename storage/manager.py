from storage.json_store import load_list, save_list, generate_id


FILES = {
    'users': 'users.json',
    'books': 'books.json',
    'records': 'borrow_records.json'
}

def get_all(entity_type):
    """Returns list of dicts (e.g., all books for the Admin Menu)."""
    return load_list(FILES.get(entity_type))

def find_by_field(entity_type, field, value):
    """
    Crucial for Auth: find_by_field('users', 'email', 'user@example.com')
    Crucial for CLI: find_by_field('books', 'isbn', '12345')
    """
    data = get_all(entity_type)
    return next((item for item in data if item.get(field) == value), None)

def add_record(entity_type, record_dict):
    """Used for: Registering Users, Adding Books, Creating Borrow Records."""
    filename = FILES.get(entity_type)
    data = load_list(filename)
    
    # Auto-assign ID to maintain the 'Entities' structure
    record_dict['id'] = generate_id(filename)
    data.append(record_dict)
    
    save_list(filename, data)
    return record_dict

def update_record(entity_type, record_id, updates):
    """Used for: Returning books (updates status) or Updating book copies."""
    filename = FILES.get(entity_type)
    data = load_list(filename)
    
    for item in data:
        if item['id'] == record_id:
            item.update(updates) # Merges new data into the existing dict
            save_list(filename, data)
            return True
    return False

def delete_record(entity_type, record_id):
    """Used for: Admin deleting a book."""
    filename = FILES.get(entity_type)
    data = load_list(filename)
    
    new_data = [item for item in data if item['id'] != record_id]
    if len(new_data) < len(data):
        save_list(filename, new_data)
        return True
    return False