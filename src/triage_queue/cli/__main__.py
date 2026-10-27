"""Module execution entry point for python -m triage_queue.cli."""

import sys
from triage_queue.cli.menu import run_menu_loop


def main() -> None:
    """Run CLI interface."""
    sys.exit(run_menu_loop())


if __name__ == "__main__":
    main()
