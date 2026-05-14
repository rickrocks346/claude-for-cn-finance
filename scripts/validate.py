#!/usr/bin/env python3
"""validate.py — validate SKILL.md frontmatter format constraints.

Checks performed:
  1. description field does not exceed 200 characters
  2. name field does not exceed 64 characters
  3. body (content after frontmatter) does not exceed 500 lines
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MAX_DESC_LEN = 200
MAX_NAME_LEN = 64
MAX_BODY_LINES = 500

FAILURES = []


def fail(msg: str):
    FAILURES.append(msg)
    print(f"  FAIL: {msg}")


def parse_frontmatter(content: str):
    """Extract YAML-like frontmatter key-value pairs."""
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    fm = {}
    for line in parts[1].strip().split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm


def check_skill(path: Path):
    with open(path, encoding="utf-8") as f:
        content = f.read()

    fm = parse_frontmatter(content)
    rel = str(path.relative_to(ROOT))

    name = fm.get("name", "")
    desc = fm.get("description", "")

    if len(desc) > MAX_DESC_LEN:
        fail(f"{rel}: description is {len(desc)} chars (max {MAX_DESC_LEN})")

    if len(name) > MAX_NAME_LEN:
        fail(f"{rel}: name is {len(name)} chars (max {MAX_NAME_LEN})")

    # Check body line count
    parts = content.split("---", 2)
    body = parts[2] if len(parts) >= 3 else content
    body_lines = [l for l in body.split("\n") if l.strip() != ""]
    if len(body_lines) > MAX_BODY_LINES:
        fail(f"{rel}: body has {len(body_lines)} non-empty lines (max {MAX_BODY_LINES})")

    if len(desc) <= MAX_DESC_LEN and len(name) <= MAX_NAME_LEN and len(body_lines) <= MAX_BODY_LINES:
        print(f"  OK: {rel}")


def main():
    print("=" * 60)
    print("validate.py — SKILL.md Format Validator")
    print("=" * 60)

    skills = list(sorted(ROOT.glob("**/SKILL.md")))
    if not skills:
        print("\n(no SKILL.md files found — OK)")
        print("\nRESULT: PASS")
        sys.exit(0)

    print(f"\nChecking {len(skills)} SKILL.md file(s)...\n")
    for skill in skills:
        check_skill(skill)

    print(f"\n{'=' * 60}")
    print(f"SUMMARY: {len(skills)} files checked, {len(FAILURES)} failures")
    if FAILURES:
        for f in FAILURES:
            print(f"  - {f}")
        print("RESULT: FAIL")
        sys.exit(1)
    else:
        print("RESULT: PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
