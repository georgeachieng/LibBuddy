from functools import wraps


# This helper normalizes session lookup for the actual CLI object shape.
# Delete it and the decorators keep checking the wrong attribute like it's still on an old branch.
def _get_current_user(app):
    # The CLI keeps session state on itself, not on a nested auth object.
    # Remove this and direct method protection stops working for the real app.
    if getattr(app, "current_user", None) is not None:
        return app.current_user

    # This fallback keeps older auth-service-backed flows from fully breaking.
    # Delete it and compatibility drops for no reason.
    auth_service = getattr(app, "auth_service", None)
    if auth_service is not None:
        return getattr(auth_service, "current_user", None)

    return None


# This decorator blocks actions unless a user is logged in.
# Delete it and protected flows can run with no session check.
def login_required(func):
    @wraps(func)
    def wrapper(app, *args, **kwargs):
        # Centralized user lookup keeps the auth check honest across app shapes.
        # Remove it and the decorator starts denying valid sessions again.
        if _get_current_user(app) is None:
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
            # Shared lookup keeps role checks aimed at the real session object.
            # Delete it and admin/user gating goes back to guessing.
            user = _get_current_user(app)

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
