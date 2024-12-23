import argparse
import atexit
import os
import sys

from actionflow.core import Flow
from actionflow.logger import configure_logger
from actionflow.tools import create_pidfile, remove_pidfile, tail_logs


def run(filepath: str, verbose: bool):
    """
    Executes the flow defined in the given file.

    Args:
        filepath (str): The path to the file containing the flow definition.
        verbose (bool): If True, prints additional information during execution.

    Raises:
        SystemExit: If the file does not exist or an error occurs during processing.

    The function performs the following steps:
        1. Checks if the specified file exists. If not, prints an error message and exits.
        2. If verbose is True, prints the file being processed.
        3. Creates a PID file to indicate the process is running.
        4. Loads all available actions.
        5. Prints the list of available actions.
        6. Loads the flow from the specified file.
        7. Executes the flow.
        8. Prints a summary of the flow execution.
        9. Handles any exceptions that occur during processing, prints an error message, and exits.
        10. Ensures the PID file is removed upon exit.
    """

    if not os.path.isfile(filepath):
        print(f"Error: The file '{filepath}' does not exist.", file=sys.stderr)
        sys.exit(1)

    if verbose:
        print(f"Processing file: {filepath}")

    try:
        create_pidfile()
        Flow.load_all_actions()
        # available_actions = Flow.get_available_actions()

        # print(
        #     f'Available actions ({len(available_actions)}):\n\t{"\n\t".join(available_actions)}'
        # )

        flow = Flow.from_file(filepath)
        flow.execute()
        # for line in flow.summary():
        #     print(line)

    except Exception as e:
        print(f"Error processing file: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        atexit.register(remove_pidfile)


def logs():
    """Fetch and display logs."""
    tail_logs()


def status():
    """Check and display the current status."""


def main():
    """
    Entry point for the ActionFlow CLI.
    This function sets up the command-line interface (CLI) for the ActionFlow tool.
    It defines three subcommands: 'run', 'logs', and 'status'.
    Subcommands:
        - run: Run the main process with the specified file.
            Arguments:
                filepath (str): Path to the file to be processed.
                -v, --verbose (bool): Enable verbose output.
        - logs: Fetch logs.
        - status: Fetch current status.
    Parses the command-line arguments and calls the appropriate function based on the subcommand.
    If no valid subcommand is provided, it prints the help message and exits with status code 1.
    """

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
    configure_logger()
    main()
