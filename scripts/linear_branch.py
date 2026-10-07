#!/usr/bin/env python3
"""Linear Branch CLI Helper.

Quickly create or verify branches matching the naming convention:
{type}/{ticket_id}_{ticket_name}
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def slugify(text: str) -> str:
    """Convert text to a clean git-safe slug."""
    text = text.lower()
    text = re.sub(r"\[.*?\]", "", text)  # remove [T-19] etc
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text).strip("-")
    # Truncate to reasonable branch name length
    return text[:45].rstrip("-")


def get_cached_tickets() -> dict:
    cache_path = ROOT_DIR / ".linear_cache.json"
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"tickets": []}


def cmd_list(args):
    """List available tickets in cache."""
    data = get_cached_tickets()
    tickets = data.get("tickets", [])
    print(f"\n📋 Tickets registrados en {data.get('project', 'Linear')}:")
    for t in tickets:
        print(f"  • {t}")
    print("\nPara crear una rama a partir de un ticket:")
    print("  python3 scripts/linear_branch.py new <ticket_id> [type] [nombre]")
    print("  Ejemplo: python3 scripts/linear_branch.py new CPS-88 feature proteger-rama-main\n")


def cmd_new(args):
    """Create and checkout a new compliant branch."""
    ticket_id = args.ticket.upper()
    branch_type = args.type.lower()
    name = args.name.strip() if args.name else "task"
    name_slug = slugify(name)

    branch_name = f"{branch_type}/{ticket_id}_{name_slug}"
    print(f"Creando y cambiando a rama: {branch_name}")
    try:
        subprocess.check_call(["git", "checkout", "-b", branch_name])
        print(f"✓ Rama creada exitosamente: {branch_name}")
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)


def main():
    parser = argparse.ArgumentParser(description="Linear branch helper")
    subparsers = parser.add_subparsers(dest="command")

    list_parser = subparsers.add_parser("list", help="List cached Linear tickets")

    new_parser = subparsers.add_parser("new", help="Create a new compliant branch")
    new_parser.add_argument("ticket", help="Linear ticket ID (e.g. CPS-88)")
    new_parser.add_argument("type", nargs="?", default="feature", help="Branch type (feature, bug, chore, etc.)")
    new_parser.add_argument("name", nargs="?", default="", help="Descriptive name slug")

    args = parser.parse_args()
    if args.command == "list":
        cmd_list(args)
    elif args.command == "new":
        cmd_new(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
