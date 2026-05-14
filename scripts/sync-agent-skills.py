#!/usr/bin/env python3
"""sync-agent-skills.py — sync skills from vertical-plugins to agent-plugins.

Usage:
  python3 scripts/sync-agent-skills.py              # sync all
  python3 scripts/sync-agent-skills.py --check-only # dry run, report drift only
"""

import filecmp
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERTICAL_DIR = ROOT / "plugins" / "vertical-plugins"
AGENT_DIR = ROOT / "plugins" / "agent-plugins"


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def sync_vertical_to_agent(vertical_name: str, agent_slug: str, check_only: bool = False):
    """Copy skills from vertical-plugins/<vertical>/skills/ to agent-plugins/<slug>/skills/."""
    src = VERTICAL_DIR / vertical_name / "skills"
    dst = AGENT_DIR / agent_slug / "skills"

    if not src.is_dir():
        print(f"  SKIP: source {relative(src)} does not exist")
        return

    drifts = []

    # Walk source skills
    for src_file in sorted(src.rglob("*")):
        if src_file.is_dir():
            continue
        rel_path = src_file.relative_to(src)
        dst_file = dst / rel_path

        if dst_file.exists():
            if not filecmp.cmp(str(src_file), str(dst_file), shallow=False):
                drifts.append(relative(rel_path))
                if not check_only:
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(src_file), str(dst_file))
                    print(f"  SYNC: {relative(rel_path)} (drifted, updated)")
            else:
                print(f"  OK: {relative(rel_path)} (in sync)")
        else:
            if not check_only:
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src_file), str(dst_file))
                print(f"  NEW: {relative(rel_path)} (copied)")
            else:
                print(f"  MISSING: {relative(rel_path)} (not in agent)")

    if drifts and check_only:
        print(f"\n  DRIFT DETECTED ({len(drifts)} files):")
        for d in drifts:
            print(f"    - {d}")


def main():
    check_only = "--check-only" in sys.argv

    print("=" * 60)
    print("sync-agent-skills.py")
    if check_only:
        print("MODE: check-only (dry run)")
    print("=" * 60)

    # Read marketplace config to get vertical → agent mappings
    manifest_path = ROOT / ".claude-plugin" / "plugin.json"
    if not manifest_path.exists():
        print("ERROR: top-level plugin.json not found")
        sys.exit(1)

    import json
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    plugins = manifest.get("marketplace", {}).get("plugins", [])
    if not plugins:
        print("No plugins found in marketplace manifest")
        return

    synced = 0
    for plugin in plugins:
        name = plugin["name"]
        print(f"\n--- {name} ---")
        sync_vertical_to_agent(name, name, check_only)
        synced += 1

    print(f"\n{'=' * 60}")
    print(f"Done. {synced} vertical(s) processed.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
