import argparse
import atexit
import os
import sys
from multiprocessing import Lock

from kinetik.flow import Flow

LOCK_FILE = "/tmp/my_program.lock"

lock = Lock()


def create_lock_file():
    if os.path.exists(LOCK_FILE):
        print(
            f"Le programme est déjà en cours d'exécution. Fichier de verrou : {LOCK_FILE}"
        )
        sys.exit(1)
    with open(LOCK_FILE, "w") as lock_file:
        lock_file.write(str(os.getpid()))


def remove_lock_file():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Process a file using my_package.")

    parser.add_argument(
        "filepath",
        type=str,
        help="Path to the file to be processed.",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output."
    )

    args = parser.parse_args()

    filepath = args.filepath
    verbose = args.verbose

    # Validate the file path
    if not os.path.isfile(filepath):
        print(f"Error: The file '{filepath}' does not exist.", file=sys.stderr)
        sys.exit(1)

    if verbose:
        print(f"Processing file: {filepath}")

    try:
        create_lock_file()
        flow = Flow.from_file(filepath)
        flow.execute()

    except Exception as e:
        print(f"Error processing file: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        atexit.register(remove_lock_file)


if __name__ == "__main__":
    main()
