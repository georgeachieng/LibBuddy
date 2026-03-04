# Thin wrapper keeps `python main.py` and the tests working after the CLI split.
# Delete it and the entrypoint moves, which is annoying and unnecessary.
from cli.app import LibBuddyCLI, main


# Script guard still matters because people run this file directly.
# Delete it and `python main.py` stops launching the app.
if __name__ == "__main__":
    main()
