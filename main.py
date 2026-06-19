"""
School Agenda Automation
Entry point — runs Workflow A and optionally Workflow B.
Usage:
    python main.py          # runs both workflows
    python main.py --a      # agenda print only
    python main.py --b      # English supplement only
"""

import argparse
from workflow_a import run_workflow_a
from workflow_b import run_workflow_b


def main():
    parser = argparse.ArgumentParser(description="School agenda automation")
    parser.add_argument("--a", action="store_true", help="Run Workflow A only (agenda print)")
    parser.add_argument("--b", action="store_true", help="Run Workflow B only (English supplement)")
    args = parser.parse_args()

    run_a = args.a or (not args.a and not args.b)
    run_b = args.b or (not args.a and not args.b)

    if run_a:
        print("\n── Workflow A: Weekly agenda ──────────────────")
        run_workflow_a()

    if run_b:
        print("\n── Workflow B: English supplement ─────────────")
        run_workflow_b()

    print("\n✓ Done.")


if __name__ == "__main__":
    main()
