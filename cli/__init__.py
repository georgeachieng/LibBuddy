# Re-exporting here keeps imports short after the CLI package split.
# Delete it and callers have to know the internal file layout.
from cli.app import LibBuddyCLI, ServiceNotReadyError, main

__all__ = ["LibBuddyCLI", "ServiceNotReadyError", "main"]
