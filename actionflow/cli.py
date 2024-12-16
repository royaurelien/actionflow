import argparse
import atexit
import os
import sys

from actionflow.core import Flow
from actionflow.tools import create_pidfile, remove_pidfile


def run(filepath: str, verbose: bool):
    if not os.path.isfile(filepath):
        print(f"Error: The file '{filepath}' does not exist.", file=sys.stderr)
        sys.exit(1)

    if verbose:
        print(f"Processing file: {filepath}")

    try:
        create_pidfile()
        Flow.load_all_actions()
        available_actions = Flow.get_available_actions()

        print(
            f'Available actions ({len(available_actions)}):\n\t{"\n\t".join(available_actions)}'
        )

        flow = Flow.from_file(filepath)
        flow.execute()
        flow.summary()

    except Exception as e:
        print(f"Error processing file: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        atexit.register(remove_pidfile)


def logs():
    """Fetch and display logs."""


def status():
    """Check and display the current status."""


def main():
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
