# Re-exporting services here makes package-level imports shorter for callers.
# Delete these and any `from LibBuddy import AuthService` style import breaks.
from services.auth_service import AuthService
from services.library_service import LibraryService
from services.review_service import ReviewService

# Version constant gives the package one obvious identity marker.
# Delete it and external version checks lose their target.
__version__ = "1.0.0"

# __all__ controls what wildcard imports expose on purpose.
# Delete it and package exports become more accidental than intentional.
__all__ = ["AuthService", "LibraryService", "ReviewService"]
