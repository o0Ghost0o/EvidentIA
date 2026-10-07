#!/usr/bin/env python3
"""Branch protection and Linear ticket convention validator.

Enforces:
1. No direct commits to 'main' or 'master' (only PR merges allowed).
2. Branch naming convention: {type}/{ticket_id}_{ticket_name}
3. Linear ticket validation against Linear API or local project cache.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

BRANCH_PATTERN = re.compile(
    r"^(?P<type>feature|feat|bug|fix|bugfix|chore|refactor|hotfix|test|docs)/"
    r"(?P<ticket>[A-Za-z0-9]+-\d+)_"
    r"(?P<name>[a-zA-Z0-9_\-]+)$"
)

PROTECTED_BRANCHES = {"main", "master"}
INTEGRATION_BRANCHES = {"dev", "develop"}
ALLOWED_TYPES = ["feature", "feat", "bug", "fix", "bugfix", "chore", "refactor", "hotfix", "test", "docs"]


def get_current_branch() -> str:
    """Get the current active git branch name."""
    try:
        output = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return output
    except Exception:
        return ""


def load_env_file(root_dir: Path) -> dict[str, str]:
    """Load key-value pairs from .env if present."""
    env_vars: dict[str, str] = {}
    env_path = root_dir / ".env"
    if not env_path.exists():
        return env_vars

    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env_vars[k.strip()] = v.strip().strip("'\"")
    except Exception:
        pass
    return env_vars


def query_linear_api(ticket_id: str, api_key: str) -> dict | None:
    """Query Linear GraphQL API to verify issue existence."""
    query = """
    query GetIssue($id: String!) {
      issue(id: $id) {
        id
        identifier
        title
        state {
          name
        }
      }
    }
    """
    payload = json.dumps({"query": query, "variables": {"id": ticket_id}}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.linear.app/graphql",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": api_key,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            issue = data.get("data", {}).get("issue")
            return issue
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        return None
    except Exception:
        return None


def get_cached_tickets(root_dir: Path) -> set[str]:
    """Load cached ticket identifiers from .linear_cache.json if present."""
    cache_path = root_dir / ".linear_cache.json"
    if not cache_path.exists():
        return set()
    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return {item.get("id") or item for item in data if isinstance(item, (dict, str))}
        if isinstance(data, dict):
            return set(data.get("tickets", []))
    except Exception:
        pass
    return set()


def validate_branch():
    branch = get_current_branch()

    # Allow detached HEAD states (e.g. during rebases, bisects, or CI checkouts)
    if not branch or branch == "HEAD" or branch in INTEGRATION_BRANCHES:
        return

    # 1. Protect main / master
    if branch in PROTECTED_BRANCHES:
        print("\n" + "=" * 78, file=sys.stderr)
        print("🛑 [BRANCH PROTECTION] Commits directos en la rama '{}' están prohibidos.".format(branch), file=sys.stderr)
        print("=" * 78, file=sys.stderr)
        print("Para realizar cambios, sigue el flujo estándar de mejores prácticas:\n", file=sys.stderr)
        print("  1. Crea una rama según la convención:", file=sys.stderr)
        print("     git checkout -b {type}/{ticket_id}_{ticket_name}", file=sys.stderr)
        print("     Ejemplo: git checkout -b feature/CPS-88_proteger-rama-main\n", file=sys.stderr)
        print("  2. Realiza tus commits en la rama de trabajo.", file=sys.stderr)
        print("  3. Abre un Pull Request (PR) hacia 'main'.", file=sys.stderr)
        print("=" * 78 + "\n", file=sys.stderr)
        sys.exit(1)

    # 2. Validate branch name format
    match = BRANCH_PATTERN.match(branch)
    if not match:
        print("\n" + "=" * 78, file=sys.stderr)
        print("🛑 [CONVENCIÓN DE RAMA INVÁLIDA] Rama: '{}'".format(branch), file=sys.stderr)
        print("=" * 78, file=sys.stderr)
        print("El nombre de la rama DEBE cumplir con la convención requerida:\n", file=sys.stderr)
        print("    {type}/{ticket_id}_{ticket_name}\n", file=sys.stderr)
        print("Componentes requeridos:", file=sys.stderr)
        print("  • {type}        : " + " | ".join(ALLOWED_TYPES), file=sys.stderr)
        print("  • {ticket_id}   : Identificador del ticket en Linear (ej. CPS-88, CPS-73)", file=sys.stderr)
        print("  • {ticket_name} : Nombre o slug descriptivo de la tarea (letras, números, guiones)", file=sys.stderr)
        print("\nEjemplos válidos:", file=sys.stderr)
        print("  ✓ feature/CPS-88_proteger-rama-main", file=sys.stderr)
        print("  ✓ bug/CPS-85_fix-modo-offline", file=sys.stderr)
        print("  ✓ chore/CPS-70_sync-notion-pages", file=sys.stderr)
        print("=" * 78 + "\n", file=sys.stderr)
        sys.exit(1)

    branch_type = match.group("type")
    ticket_id = match.group("ticket").upper()
    ticket_name = match.group("name")

    # 3. Verify Linear Ticket Existence
    root_dir = Path(__file__).resolve().parent.parent
    dotenv = load_env_file(root_dir)
    api_key = os.environ.get("LINEAR_API_KEY") or dotenv.get("LINEAR_API_KEY")

    if api_key:
        issue = query_linear_api(ticket_id, api_key)
        if not issue:
            print("\n" + "=" * 78, file=sys.stderr)
            print("🛑 [LINEAR TICKET NO ENCONTRADO] Ticket: '{}'".format(ticket_id), file=sys.stderr)
            print("=" * 78, file=sys.stderr)
            print("No se encontró ningún issue con el ID '{}' en tu workspace de Linear.".format(ticket_id), file=sys.stderr)
            print("Verifica el número del ticket en Linear o crea el issue correspondiente antes de commitear.", file=sys.stderr)
            print("=" * 78 + "\n", file=sys.stderr)
            sys.exit(1)
        state_name = issue.get("state", {}).get("name", "Unknown")
        title = issue.get("title", "")
        print(f"✓ Linear Ticket verificado [en vivo]: {ticket_id} - \"{title}\" ({state_name})")
    else:
        cached = get_cached_tickets(root_dir)
        if cached and ticket_id in cached:
            print(f"✓ Linear Ticket verificado [en caché local]: {ticket_id}")
        else:
            # Ticket format is valid syntactically
            print(f"✓ Rama válida: {branch_type}/{ticket_id}_{ticket_name}")
            print("  ℹ️ (Configura LINEAR_API_KEY en .env o variables de entorno para verificación en vivo contra la API de Linear)")


if __name__ == "__main__":
    validate_branch()
