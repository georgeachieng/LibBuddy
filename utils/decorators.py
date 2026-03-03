from functools import wraps


# This decorator blocks actions unless a user is logged in.
# Delete it and protected flows can run with no session check.
def login_required(func):
    @wraps(func)
    def wrapper(app, *args, **kwargs):
        # getattr keeps this from exploding if the app shape changes slightly.
        # Remove it and missing auth attributes become runtime crashes.
        if not getattr(app, "auth", None) or app.auth.current_user is None:
            print("Please login first.")
            return

        # Only run the protected function when auth state is real.
        # Delete this return and the wrapped function never runs.
        return func(app, *args, **kwargs)

    return wrapper


# This decorator adds a role gate on top of normal login checks.
# Delete it and admin-only actions stop being admin-only.
def role_required(role):
    def decorator(func):
        @wraps(func)
        def wrapper(app, *args, **kwargs):
            # This short-circuit avoids touching current_user when auth is missing.
            # Delete it and malformed app state can crash the permission check.
            user = getattr(app, "auth", None) and app.auth.current_user

            if user is None:
                print("Please login first.")
                return

            # Role mismatch exits early so the protected action never runs.
            # Delete this and every role can reach restricted logic.
            if user.get("role") != role:
                print(f"Access denied. Requires role: {role}.")
                return

            return func(app, *args, **kwargs)

        return wrapper

    return decorator
