from functools import wraps


def _get_current_user(app):
    if getattr(app, "current_user", None) is not None:
        return app.current_user

    auth_service = getattr(app, "auth_service", None)
    if auth_service is not None:
        return getattr(auth_service, "current_user", None)

    return None


def login_required(func):
    @wraps(func)
    def wrapper(app, *args, **kwargs):
        if _get_current_user(app) is None:
            print("Please login first.")
            return

        return func(app, *args, **kwargs)

    return wrapper


def role_required(role):
    def decorator(func):
        @wraps(func)
        def wrapper(app, *args, **kwargs):
            user = _get_current_user(app)

            if user is None:
                print("Please login first.")
                return

            if user.get("role") != role:
                print(f"Access denied. Requires role: {role}.")
                return

            return func(app, *args, **kwargs)

        return wrapper

    return decorator
