#!/usr/bin/env python3
"""Run release regressions, including the bundled workbench contract tests. No dependencies."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    # Tests use isolated temporary project/install directories, never the user's installed skill.
    sys.dont_write_bytecode = True
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTests(loader.discover(str(ROOT / "skills/ai-dev-workbench/scripts"), pattern="test_workbench.py"))
    suite.addTests(unittest.TestLoader().discover(str(ROOT / "tests"), pattern="test_*.py"))
    result = unittest.TextTestRunner(verbosity=2 if args.verbose else 1).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
