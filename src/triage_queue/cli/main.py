#!/usr/bin/env python3
"""Standalone script entry point for Emergency Unit Triage Queue Manager."""

from pathlib import Path
import sys

# Ensure src/ is in sys.path when executed directly as a standalone script
_SRC_DIR = Path(__file__).resolve().parent.parent.parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from triage_queue.cli.menu import run_menu_loop


def main() -> int:
    """Execute main application menu loop."""
    return run_menu_loop()


if __name__ == "__main__":
    sys.exit(main())
