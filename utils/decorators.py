
#write code here
from functools import wraps

def login_required(func):
    @wraps(func)
    def wrapper(app, *args, **kwargs):
        if not getattr(app, "auth", None) or app.auth.current_user is None:
            print("Please login first.")
            return
        return func(app, *args, **kwargs)
    return wrapper

def role_required(role):
    def decorator(func):
        @wraps(func)
        def wrapper(app, *args, **kwargs):
            user = getattr(app, "auth", None) and app.auth.current_user
            if user is None:
                print("Please login first.")
                return
            if user.get("role") != role:
                print(f"Access denied. Requires role: {role}.")
                return
            return func(app, *args, **kwargs)
        return wrapper
    return decorator
