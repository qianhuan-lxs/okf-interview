#!/usr/bin/env python3
"""Interview Knowledge Format (IKF) management CLI.

Subcommands:
  add         Interactively scaffold a new question from _templates/question.md
  gen-index   (Re)generate every index.md from the tree of question files
  search      Filter questions by frontmatter fields
  move        Move/rename a question and rewrite incoming [[wiki]] links
  validate    Check all question files against SPEC (required fields, id==path)

Design goals (mirrors OKF):
- One file per question, with stable YAML frontmatter as the Agent query contract.
- index.md per directory for progressive disclosure.
- Wiki-link [[id]] graph between questions, with auto backlinks in index.md.

Requires: Python 3.10+ (stdlib only).
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "_templates" / "question.md"
REQUIRED_FIELDS = ("type", "id", "title", "category", "difficulty", "timestamp")
CATEGORIES = [
    "algorithms", "system-design", "databases", "operating-systems",
    "networks", "distributed-systems", "concurrency", "languages",
    "frontend", "backend", "devops", "ml-ai", "behavioral",
]
WIKI_RE = re.compile(r"\[\[([^\]]+)\]\]")


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


# --------------------------------------------------------------------------- #
# Frontmatter parsing
# --------------------------------------------------------------------------- #

@dataclass
class Question:
    path: Path
    fm: dict = field(default_factory=dict)
    body: str = ""


def parse_fm(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    # Frontmatter must start with a `---` line.
    if not text.startswith("---"):
        return None
    # Strip leading fence; split on the next `---` line.
    rest = text[3:]
    if rest.startswith("\r\n"):
        rest = rest[2:]
    elif rest.startswith("\n"):
        rest = rest[1:]
    else:
        return None
    # Find closing fence on its own line.
    m = re.search(r"^---\s*$", rest, re.MULTILINE)
    if not m:
        return None
    raw = rest[: m.start()]
    body = rest[m.end():].lstrip("\n")
    if yaml is not None:
        try:
            data = yaml.safe_load(raw) or {}
        except yaml.YAMLError as e:  # pragma: no cover
            print(f"[warn] {path}: YAML error: {e}", file=sys.stderr)
            return None
        return data
    # Fallback: very small line parser for `key: value` / `key: [a, b]`
    data: dict = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            data[k] = [x.strip() for x in inner.split(",") if x.strip()] if inner else []
        else:
            data[k] = v
    return data


def read_question(path: Path) -> Question | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    rest = text[3:].lstrip("\n")
    m = re.search(r"^---\s*$", rest, re.MULTILINE)
    if not m:
        return None
    fm = parse_fm(path)
    if fm is None:
        return None
    body = rest[m.end():].lstrip("\n")
    return Question(path=path, fm=fm, body=body)


def iter_questions(root: Path = ROOT) -> list[Question]:
    qs = []
    for p in sorted(root.rglob("*.md")):
        rel = p.relative_to(root)
        parts = rel.parts
        if parts[0] in ("_templates", "tools"):
            continue
        if p.name == "index.md":
            continue
        if parts[0] not in CATEGORIES:
            continue
        q = read_question(p)
        if q is not None:
            qs.append(q)
    return qs


# --------------------------------------------------------------------------- #
# gen-index
# --------------------------------------------------------------------------- #

def _md_escape(s: str) -> str:
    return s.replace("|", "\\|")


def _row(q: Question) -> str:
    diff = q.fm.get("difficulty", "?")
    tags = q.fm.get("tags", []) or []
    tag_str = ", ".join(tags) if isinstance(tags, list) else str(tags)
    rel = q.path.relative_to(ROOT).as_posix()
    return f"| [{_md_escape(q.fm.get('title', rel))}]({rel}) | {diff} | {tag_str} |"


def _backlinks(target_id: str, questions: list[Question]) -> list[str]:
    """Find questions whose body links to target_id via [[id]] or relative md link."""
    backs: list[str] = []
    target_stem = target_id
    for q in questions:
        links = WIKI_RE.findall(q.body)
        rel_links = re.findall(r"\]\(([^)]+\.md)\)", q.body)
        norm_rel = [Path(l).resolve() for l in rel_links]
        if target_id in links:
            backs.append(q.fm.get("id", q.path.relative_to(ROOT).as_posix()))
            continue
        # also match by path
        target_path = (ROOT / (target_id + ".md")).resolve()
        if target_path in norm_rel:
            backs.append(q.fm.get("id", q.path.relative_to(ROOT).as_posix()))
    return backs


def build_index_for(dir_path: Path, questions: list[Question]) -> str:
    rel = dir_path.relative_to(ROOT)
    title = rel.as_posix() if rel.parts else "Root"
    lines = [f"# Index — {title}", ""]

    # Subdirectories
    subdirs = sorted([d for d in dir_path.iterdir() if d.is_dir() and not d.name.startswith(".")])
    subdirs = [d for d in subdirs if d.name not in ("tools", "_templates")]
    if subdirs:
        lines.append("## 子目录")
        lines.append("")
        lines.append("| 目录 | 题目数 |")
        lines.append("| --- | --- |")
        for d in subdirs:
            count = sum(1 for q in questions if q.path.is_relative_to(d))
            lines.append(f"| [`{d.name}`](./{d.name}/index.md) | {count} |")
        lines.append("")

    # Direct questions in this dir only
    direct = [q for q in questions if q.path.parent == dir_path]
    if direct:
        lines.append("## 题目")
        lines.append("")
        lines.append("| 标题 | 难度 | 标签 |")
        lines.append("| --- | --- | --- |")
        for q in sorted(direct, key=lambda x: x.fm.get("title", "")):
            lines.append(_row(q))
        lines.append("")

    # Backlinks to this directory's own index id (i.e. questions linking INTO this dir)
    if rel.parts:
        dir_id = rel.as_posix()
        # any question whose links point at any id starting with dir_id/
        incoming = []
        for q in questions:
            # Skip questions that live inside this directory — sibling links are
            # backlinks on the *target file*, not on the directory index.
            if _is_within(q.path, dir_path):
                continue
            wiki = WIKI_RE.findall(q.body)
            if any(w.startswith(dir_id + "/") for w in wiki):
                incoming.append(q)
            else:
                rel_links = re.findall(r"\]\(([^)]+\.md)\)", q.body)
                for l in rel_links:
                    lp = (q.path.parent / l).resolve()
                    try:
                        lr = lp.relative_to(ROOT).as_posix()
                    except ValueError:
                        continue
                    if lr.startswith(dir_id + "/"):
                        incoming.append(q)
                        break
        if incoming:
            lines.append("## 被引用 (cited by)")
            lines.append("")
            for q in sorted(incoming, key=lambda x: x.fm.get("id", "")):
                qid = q.fm.get("id", q.path.relative_to(ROOT).as_posix())
                lines.append(f"- [[{qid}]] — {q.fm.get('title', '')}")
            lines.append("")

    lines.append("<!-- 由 `tools/okf.py gen-index` 自动生成，请勿手动编辑正文。 -->")
    return "\n".join(lines) + "\n"


def cmd_gen_index(_: argparse.Namespace) -> int:
    questions = iter_questions()
    # Walk every dir under root that is a category or below
    target_dirs: list[Path] = [ROOT]
    for cat in CATEGORIES:
        cat_dir = ROOT / cat
        if cat_dir.is_dir():
            target_dirs.append(cat_dir)
            for d in cat_dir.rglob("*"):
                if d.is_dir():
                    target_dirs.append(d)
    for d in target_dirs:
        (d / "index.md").write_text(build_index_for(d, questions), encoding="utf-8")
    print(f"[ok] generated index.md for {len(target_dirs)} directories")
    return 0


# --------------------------------------------------------------------------- #
# add
# --------------------------------------------------------------------------- #

def _prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"{label}{suffix}: ").strip()
    return val or default


def cmd_add(args: argparse.Namespace) -> int:
    if not TEMPLATE.exists():
        print(f"[err] template not found: {TEMPLATE}", file=sys.stderr)
        return 1
    print("=== Add new question ===")
    category = _prompt("category (algorithms/system-design/...)", args.category)
    if category not in CATEGORIES:
        print(f"[err] unknown category '{category}'. valid: {CATEGORIES}", file=sys.stderr)
        return 1
    sub = _prompt("subcategory (e.g. dynamic-programming; empty for none)", "")
    slug = _prompt("slug (kebab-case file name, e.g. longest-increasing-subsequence)", "")
    if not slug:
        print("[err] slug is required", file=sys.stderr)
        return 1
    title = _prompt("title", slug.replace("-", " ").title())
    difficulty = _prompt("difficulty (easy/medium/hard)", "medium")
    tags_raw = _prompt("tags (comma separated)", "")
    langs_raw = _prompt("languages (comma separated, e.g. python,cpp)", "")
    role_raw = _prompt("role (comma separated, e.g. sde,backend)", "sde")
    companies_raw = _prompt("companies (comma separated)", "")
    source = _prompt("source (e.g. leetcode-300)", "")
    status = _prompt("status (todo/draft/reviewed/mastered)", "todo")

    def split_list(s: str) -> list[str]:
        return [x.strip() for x in s.split(",") if x.strip()]

    rel_dir = ROOT / category / sub if sub else ROOT / category
    rel_dir.mkdir(parents=True, exist_ok=True)
    out = rel_dir / f"{slug}.md"
    if out.exists():
        print(f"[err] already exists: {out}", file=sys.stderr)
        return 1
    qid = f"{category}/{sub}/{slug}" if sub else f"{category}/{slug}"

    tmpl = TEMPLATE.read_text(encoding="utf-8")
    tmpl = tmpl.replace("<category>/<subcategory>/<slug>", qid)
    tmpl = tmpl.replace("<category>", category)
    tmpl = tmpl.replace("<subcategory>", sub or "<subcategory>")
    tmpl = tmpl.replace("<slug>", slug)
    tmpl = tmpl.replace("<题目标题>", title)
    tmpl = tmpl.replace("difficulty: easy   # easy / medium / hard", f"difficulty: {difficulty}")
    tmpl = tmpl.replace("tags: []           # e.g. [binary-search, monotonic-stack]",
                        f"tags: {split_list(tags_raw)}")
    tmpl = tmpl.replace("languages: []      # e.g. [python, cpp]",
                        f"languages: {split_list(langs_raw)}")
    tmpl = tmpl.replace("role: []           # e.g. [sde, backend]",
                        f"role: {split_list(role_raw)}")
    tmpl = tmpl.replace("companies: []      # e.g. [Google, ByteDance]",
                        f"companies: {split_list(companies_raw)}")
    tmpl = tmpl.replace('source: ""         # e.g. leetcode-300 / interview-2026-06',
                        f'source: "{source}"')
    tmpl = tmpl.replace("status: todo       # todo / draft / reviewed / mastered",
                        f"status: {status}")
    tmpl = tmpl.replace("timestamp: 2026-07-04",
                        f"timestamp: {dt.date.today().isoformat()}")
    # If sub was empty, drop the subcategory line entirely
    if not sub:
        tmpl = re.sub(r"^subcategory: <subcategory>\n", "", tmpl, flags=re.M)

    out.write_text(tmpl, encoding="utf-8")
    print(f"[ok] created {out.relative_to(ROOT)}")
    print("     run `python tools/okf.py gen-index` to refresh navigation.")
    return 0


# --------------------------------------------------------------------------- #
# search
# --------------------------------------------------------------------------- #

def _fm_get(q: Question, key: str):
    v = q.fm.get(key)
    if v is None:
        return [] if key in {"tags", "languages", "role", "companies"} else ""
    return v


def _matches(q: Question, args: argparse.Namespace) -> bool:
    pairs = [
        ("difficulty", args.difficulty),
        ("category", args.category),
        ("subcategory", args.subcategory),
        ("source", args.source),
        ("status", args.status),
    ]
    for key, want in pairs:
        if not want:
            continue
        if str(_fm_get(q, key)).lower() != str(want).lower():
            return False
    for tag in args.tags or []:
        tags = _fm_get(q, "tags")
        if not isinstance(tags, list) or tag.lower() not in [t.lower() for t in tags]:
            return False
    for role in args.role or []:
        roles = _fm_get(q, "role")
        if not isinstance(roles, list) or role.lower() not in [r.lower() for r in roles]:
            return False
    for c in args.companies or []:
        cs = _fm_get(q, "companies")
        if not isinstance(cs, list) or c.lower() not in [x.lower() for x in cs]:
            return False
    if args.text:
        if args.text.lower() not in q.path.read_text(encoding="utf-8").lower():
            return False
    return True


def cmd_search(args: argparse.Namespace) -> int:
    questions = iter_questions()
    hits = [q for q in questions if _matches(q, args)]
    if not hits:
        print("(no matches)")
        return 0
    for q in hits:
        rel = q.path.relative_to(ROOT).as_posix()
        diff = q.fm.get("difficulty", "?")
        print(f"[{diff:6}] {rel}  —  {q.fm.get('title', '')}")
    print(f"\n{len(hits)} match(es)")
    return 0


# --------------------------------------------------------------------------- #
# validate
# --------------------------------------------------------------------------- #

def cmd_validate(_: argparse.Namespace) -> int:
    questions = iter_questions()
    if not questions:
        print("(no questions yet)")
        return 0
    errors = 0
    for q in questions:
        rel = q.path.relative_to(ROOT).as_posix()
        for f in REQUIRED_FIELDS:
            if f not in q.fm or q.fm[f] in (None, "", []):
                print(f"[err] {rel}: missing required field '{f}'", file=sys.stderr)
                errors += 1
        expected_id = rel[:-3] if rel.endswith(".md") else rel
        if str(q.fm.get("id", "")) != expected_id:
            print(f"[err] {rel}: id '{q.fm.get('id')}' != expected '{expected_id}'",
                  file=sys.stderr)
            errors += 1
        cat = str(q.fm.get("category", ""))
        if cat and not rel.startswith(cat + "/"):
            print(f"[err] {rel}: category '{cat}' != path prefix", file=sys.stderr)
            errors += 1
        diff = q.fm.get("difficulty")
        if diff not in ("easy", "medium", "hard"):
            print(f"[err] {rel}: difficulty '{diff}' invalid", file=sys.stderr)
            errors += 1
        for list_field in ("tags", "languages", "role", "companies"):
            v = q.fm.get(list_field)
            if v is not None and not isinstance(v, list):
                print(f"[warn] {rel}: {list_field} should be a list, got {type(v).__name__}",
                      file=sys.stderr)
    if errors:
        print(f"\n{errors} error(s)", file=sys.stderr)
        return 1
    print(f"[ok] {len(questions)} question(s) valid")
    return 0


# --------------------------------------------------------------------------- #
# move
# --------------------------------------------------------------------------- #

def cmd_move(args: argparse.Namespace) -> int:
    src = ROOT / args.src
    dst = ROOT / args.dst
    if not src.exists():
        print(f"[err] src not found: {src}", file=sys.stderr)
        return 1
    if dst.exists():
        print(f"[err] dst already exists: {dst}", file=sys.stderr)
        return 1
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    # Update id in moved file
    q = read_question(dst)
    if q:
        new_id = dst.relative_to(ROOT).as_posix()[:-3]
        text = dst.read_text(encoding="utf-8")
        text = re.sub(r"^id: .*$", f"id: {new_id}", text, flags=re.M)
        # Update category/subcategory if path changed
        parts = dst.relative_to(ROOT).parts
        if len(parts) >= 2:
            text = re.sub(r"^category: .*$", f"category: {parts[0]}", text, flags=re.M)
            if len(parts) >= 3 and parts[1] != args.dst.split("/")[-1]:
                pass
        dst.write_text(text, encoding="utf-8")
    # Rewrite incoming wiki links
    old_id = src.relative_to(ROOT).as_posix()[:-3]
    new_id = dst.relative_to(ROOT).as_posix()[:-3]
    for q in iter_questions():
        if q.path == dst:
            continue
        t = q.path.read_text(encoding="utf-8")
        new_t = t.replace(f"[[{old_id}]]", f"[[{new_id}]]")
        new_t = new_t.replace(f"]({args.src})", f"]({args.dst})")
        if new_t != t:
            q.path.write_text(new_t, encoding="utf-8")
            print(f"[ok] rewrote links in {q.path.relative_to(ROOT)}")
    print(f"[ok] moved {args.src} -> {args.dst}")
    return 0


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="okf", description="Interview knowledge catalog CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    pa = sub.add_parser("add", help="Interactively create a new question")
    pa.add_argument("--category", default="")
    pa.set_defaults(func=cmd_add)

    pg = sub.add_parser("gen-index", help="Regenerate every index.md")
    pg.set_defaults(func=cmd_gen_index)

    pv = sub.add_parser("validate", help="Validate all questions against SPEC")
    pv.set_defaults(func=cmd_validate)

    pm = sub.add_parser("move", help="Move a question and rewrite incoming links")
    pm.add_argument("src", help="relative path e.g. algorithms/dp/x.md")
    pm.add_argument("dst", help="relative path e.g. algorithms/dp/y.md")
    pm.set_defaults(func=cmd_move)

    ps = sub.add_parser("search", help="Filter questions by frontmatter fields")
    ps.add_argument("--difficulty")
    ps.add_argument("--category")
    ps.add_argument("--subcategory")
    ps.add_argument("--source")
    ps.add_argument("--status")
    ps.add_argument("--tags", nargs="*", default=[])
    ps.add_argument("--role", nargs="*", default=[])
    ps.add_argument("--companies", nargs="*", default=[])
    ps.add_argument("--text", help="full-text substring search")
    ps.set_defaults(func=cmd_search)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
