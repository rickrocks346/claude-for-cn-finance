#!/usr/bin/env python3
"""check.py — lint all plugin manifests + validate cross-references.

Checks performed:
  1. All plugin.json files are valid JSON with required fields
  2. All hooks.json files are valid JSON with format {"hooks": {}}
  3. All SKILL.md files have YAML frontmatter (name + description)
  4. Marketplace references point to existing paths
  5. Outputs PASS/FAIL summary
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_PLUGIN_FIELDS = {"name", "version", "description"}
TOTAL_CHECKS = 0
FAILURES = []


def fail(msg: str):
    FAILURES.append(msg)
    print(f"  FAIL: {msg}")


def check_plugin_json(path: Path):
    """Check a plugin.json file is valid JSON with required fields."""
    global TOTAL_CHECKS
    TOTAL_CHECKS += 1
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        fail(f"{path} is not valid JSON: {e}")
        return

    if "plugins" in data and isinstance(data["plugins"], list):
        # Marketplace manifest with top-level plugins array
        for plugin in data["plugins"]:
            ref_path_str = plugin.get("source") or plugin.get("path")
            if not ref_path_str:
                fail(f"{path}: marketplace plugin missing 'source' or 'path' field")
                continue
            ref_path = ROOT / ref_path_str
            if not ref_path.is_dir():
                fail(f"{path}: marketplace references nonexistent path '{ref_path_str}'")
    else:
        # Vertical plugin manifest
        for field in REQUIRED_PLUGIN_FIELDS:
            if field not in data:
                fail(f"{path}: missing required field '{field}'")
    print(f"  OK: {relative(path)}")


def check_hooks_json(path: Path):
    """Check hooks.json format is {"hooks": {}}."""
    global TOTAL_CHECKS
    TOTAL_CHECKS += 1
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        fail(f"{path} is not valid JSON: {e}")
        return

    if not isinstance(data, dict) or "hooks" not in data:
        fail(f"{path}: missing 'hooks' key")
    elif not isinstance(data["hooks"], dict):
        fail(f"{path}: 'hooks' must be a dict")
    else:
        print(f"  OK: {relative(path)}")


def check_skill_md(path: Path):
    """Check SKILL.md has YAML frontmatter with name + description."""
    global TOTAL_CHECKS
    TOTAL_CHECKS += 1
    with open(path, encoding="utf-8") as f:
        content = f.read()

    if not content.startswith("---"):
        fail(f"{relative(path)}: missing YAML frontmatter (must start with ---)")
        return

    parts = content.split("---", 2)
    if len(parts) < 3:
        fail(f"{relative(path)}: malformed YAML frontmatter")
        return

    frontmatter = parts[1]
    if "name:" not in frontmatter:
        fail(f"{relative(path)}: frontmatter missing 'name'")
    if "description:" not in frontmatter:
        fail(f"{relative(path)}: frontmatter missing 'description'")

    print(f"  OK: {relative(path)}")


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def main():
    print("=" * 60)
    print("check.py — Plugin Manifest Linter")
    print("=" * 60)

    # 1. Check all plugin.json / marketplace.json files
    print("\n[1] Checking plugin.json / marketplace.json files...")
    manifests = sorted(list(ROOT.glob("**/plugin.json")) + list(ROOT.glob("**/marketplace.json")))
    for plugin_json in manifests:
        check_plugin_json(plugin_json)

    # 2. Check all hooks.json files
    print("\n[2] Checking hooks.json files...")
    for hooks_json in sorted(ROOT.glob("**/hooks.json")):
        check_hooks_json(hooks_json)

    # 3. Check all SKILL.md files
    print("\n[3] Checking SKILL.md files...")
    skill_mds = list(sorted(ROOT.glob("**/SKILL.md")))
    if skill_mds:
        for skill_md in skill_mds:
            check_skill_md(skill_md)
    else:
        print("  (no SKILL.md files found — OK, Phase 4+ will add them)")

    # Summary
    print("\n" + "=" * 60)
    print(f"SUMMARY: {TOTAL_CHECKS} checks run, {len(FAILURES)} failures")
    if FAILURES:
        print(f"\nFAILURES ({len(FAILURES)}):")
        for f in FAILURES:
            print(f"  - {f}")
        print("\nRESULT: FAIL")
        sys.exit(1)
    else:
        print("RESULT: PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
