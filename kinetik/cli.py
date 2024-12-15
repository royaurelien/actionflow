import argparse
import atexit
import os
import sys
from multiprocessing import Lock

from kinetik.core import Flow

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


def run(filepath: str, verbose: bool):
    # Validate the file path
    if not os.path.isfile(filepath):
        print(f"Error: The file '{filepath}' does not exist.", file=sys.stderr)
        sys.exit(1)

    if verbose:
        print(f"Processing file: {filepath}")

    try:
        create_lock_file()
        Flow.load_all_actions()
        flow = Flow.from_file(filepath)
        flow.execute()
        flow.summary()

    except Exception as e:
        print(f"Error processing file: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        atexit.register(remove_lock_file)


def logs():
    """Fetch and display logs."""
    print("Fetching logs...")  # Replace with actual log fetching logic
    print("Logs fetched successfully.")  # Example of success message


def status():
    """Check and display the current status."""
    print("Fetching current status...")  # Replace with actual status checking logic
    print("Status fetched successfully.")  # Example of success message


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="ActionFlow CLI")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    run_parser = subparsers.add_parser("run", help="Run the main process")
    run_parser.add_argument(
        "filepath", type=str, help="Path to the file to be processed"
    )
    run_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    logs_parser = subparsers.add_parser("logs", help="Fetch logs")
    status_parser = subparsers.add_parser("status", help="Fetch current status")

    args = parser.parse_args()

    if args.command == "run":
        run(args.filepath, args.verbose)
    elif args.command == "logs":
        logs()
    elif args.command == "status":
        status()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
