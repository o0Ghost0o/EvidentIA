#!/usr/bin/env python3
"""Publish ``docs/notion/*.md`` to a Notion Business space.

Usage:
    export NOTION_TOKEN=... NOTION_PARENT_PAGE_ID=...
    uv --project backend run python scripts/sync_notion.py [--dry-run]

Markdown→blocks is intentionally simple: headings, bullets, numbered lists,
code fences and paragraphs map natively; tables render as code blocks (the
Notion API table model needs one request per cell). Re-running creates new
child pages (Notion has no Markdown upsert); delete stale pages manually.
``--dry-run`` parses everything and prints block counts without calling Notion.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTION_DIR = ROOT / "docs" / "notion"
NOTION_VERSION = "2022-06-28"


def markdown_to_blocks(text: str) -> list[dict]:
    blocks: list[dict] = []
    in_code = False
    code_lines: list[str] = []
    table_lines: list[str] = []

    def flush_table() -> None:
        if table_lines:
            blocks.append({
                "type": "code",
                "code": {"language": "plain text",
                         "rich_text": [{"type": "text",
                                        "text": {"content": "\n".join(table_lines)[:1900]}}]},
            })
            table_lines.clear()

    for line in text.splitlines():
        if line.strip().startswith("```"):
            if in_code:
                blocks.append({
                    "type": "code",
                    "code": {"language": "plain text",
                             "rich_text": [{"type": "text",
                                            "text": {"content": "\n".join(code_lines)[:1900]}}]},
                })
                code_lines = []
                in_code = False
            else:
                flush_table()
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        if re.match(r"^\s*\|", line):
            table_lines.append(line)
            continue
        flush_table()
        if not line.strip():
            continue
        heading = re.match(r"^(#{1,3})\s+(.*)", line)
        if heading:
            level = len(heading.group(1))
            htype = f"heading_{level}"
            blocks.append({  # type: ignore[dict-item]
                "type": htype,
                htype: {"rich_text": [{"type": "text",
                                       "text": {"content": heading.group(2)[:1900]}}]},
            })
            continue
        bullet = re.match(r"^\s*[-*]\s+(.*)", line)
        if bullet:
            blocks.append({
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text",
                    "text": {"content": bullet.group(1)[:1900]}}]},
            })
            continue
        numbered = re.match(r"^\s*\d+[.)]\s+(.*)", line)
        if numbered:
            blocks.append({
                "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": [{"type": "text",
                    "text": {"content": numbered.group(1)[:1900]}}]},
            })
            continue
        blocks.append({
            "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text",
                                         "text": {"content": line.strip()[:1900]}}]},
        })
    flush_table()
    return blocks


def main(dry_run: bool = False) -> int:
    pages = sorted(NOTION_DIR.glob("*.md"))
    if not pages:
        print(f"No markdown pages in {NOTION_DIR}")
        return 1

    parsed = []
    for page in pages:
        text = page.read_text(encoding="utf-8")
        title = page.stem.replace("-", " ").replace("_", " ").title()
        first_heading = re.search(r"^#\s+(.*)", text, re.M)
        if first_heading:
            title = first_heading.group(1).strip()
        blocks = markdown_to_blocks(text)
        parsed.append((page.name, title, blocks))
        print(f"{page.name}: {len(blocks)} blocks")

    if dry_run:
        print("dry-run: nothing uploaded")
        return 0

    token = os.environ.get("NOTION_TOKEN", "")
    parent = os.environ.get("NOTION_PARENT_PAGE_ID", "")
    if not token or not parent:
        print("Missing NOTION_TOKEN or NOTION_PARENT_PAGE_ID")
        return 1

    import httpx

    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=60.0) as client:
        for name, title, blocks in parsed:
            resp = client.post(
                "https://api.notion.com/v1/pages",
                headers=headers,
                json={
                    "parent": {"page_id": parent},
                    "properties": {"title": [{"type": "text", "text": {"content": title}}]},
                },
            )
            resp.raise_for_status()
            page_id = resp.json()["id"]
            for i in range(0, len(blocks), 100):
                resp = client.patch(
                    f"https://api.notion.com/v1/blocks/{page_id}/children",
                    headers=headers,
                    json={"children": blocks[i : i + 100]},
                )
                resp.raise_for_status()
            print(f"uploaded {name} → {page_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main(dry_run="--dry-run" in sys.argv))
