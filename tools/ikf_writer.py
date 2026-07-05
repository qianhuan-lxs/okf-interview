#!/usr/bin/env python3
"""Shared IKF question writer. Import `q` from here instead of from seeders.

Extracted so that importing a helper does NOT trigger another seeder's
module-level q() calls (which would resurrect deleted files as a side effect).
"""
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent.parent
SRC = "_interviews/2026-05-louis-ai-java"
DEFAULT_DATE = date.today().isoformat()


def write(rel_path: str, fm: dict, body: str) -> None:
    p = ROOT / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    fm_lines = ["---"]
    for k, v in fm.items():
        if isinstance(v, list):
            fm_lines.append(f"{k}: [{', '.join(str(x) for x in v)}]")
        elif v == "":
            fm_lines.append(f'{k}: ""')
        else:
            fm_lines.append(f"{k}: {v}")
    fm_lines.append("---")
    p.write_text("\n".join(fm_lines) + "\n\n" + body.lstrip("\n"), encoding="utf-8")
    print(f"[w] {rel_path}")


def q(rel, title, category, subcategory, difficulty, tags, companies, body,
      languages=None, role=None, links=None, source=SRC, status="reviewed",
      timestamp=DEFAULT_DATE):
    """Write one IKF question markdown file with frontmatter + body + 延伸."""
    fm = {
        "type": "question",
        "id": rel[:-3] if rel.endswith(".md") else rel,
        "title": title,
        "category": category,
        "subcategory": subcategory,
        "difficulty": difficulty,
        "tags": tags,
        "languages": languages or [],
        "role": role or ["ai-app", "sde", "backend"],
        "companies": companies,
        "source": source,
        "status": status,
        "timestamp": timestamp,
    }
    if links:
        body = body.rstrip() + "\n\n## 延伸\n\n" + "\n".join(
            f"- 关联题：[[{l}]]" for l in links) + "\n"
    write(rel, fm, body)
