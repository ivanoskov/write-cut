#!/usr/bin/env python3
"""Dependency-free structural checks for the write-cut skill."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
README = ROOT / "README.md"
OPENAI = ROOT / "agents" / "openai.yaml"
CLAUDE_PLUGIN = ROOT / ".claude-plugin" / "plugin.json"
CLAUDE_MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
EVALS = ROOT / "evals" / "cases.json"
REQUIRED = (
    SKILL,
    ROOT / "README.md",
    ROOT / "LICENSE",
    ROOT / "references" / "language.md",
    ROOT / "references" / "structure-and-evidence.md",
    ROOT / "references" / "product-and-career.md",
    ROOT / "agents" / "openai.yaml",
    CLAUDE_PLUGIN,
    CLAUDE_MARKETPLACE,
    EVALS,
)


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate_skill() -> None:
    text = SKILL.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail("SKILL.md must start with YAML frontmatter")
    frontmatter = text.split("---", 2)[1]
    if not re.search(r"^name:\s*write-cut\s*$", frontmatter, re.MULTILINE):
        fail("SKILL.md must declare name: write-cut")
    if not re.search(r"^description:\s*.+$", frontmatter, re.MULTILINE):
        fail("SKILL.md must contain a description")
    if "TODO" in text or "PLACEHOLDER" in text:
        fail("SKILL.md contains unfinished placeholders")
    for target in re.findall(r"\]\(([^)]+\.md)\)", text):
        if not (ROOT / target).is_file():
            fail(f"broken Markdown link in SKILL.md: {target}")


def validate_repository() -> None:
    readme = README.read_text(encoding="utf-8")
    for target in re.findall(r"\]\(([^)]+)\)", readme):
        if "://" not in target and not (ROOT / target).is_file():
            fail(f"broken local link in README.md: {target}")

    openai = OPENAI.read_text(encoding="utf-8")
    if "$write-cut" not in openai:
        fail("agents/openai.yaml must mention $write-cut in default_prompt")
    if not re.search(r"allow_implicit_invocation:\s*true\s*$", openai, re.MULTILINE):
        fail("agents/openai.yaml must allow implicit invocation")

    plugin = json.loads(CLAUDE_PLUGIN.read_text(encoding="utf-8"))
    if plugin.get("name") != "write-cut":
        fail("Claude plugin must be named write-cut")

    marketplace = json.loads(CLAUDE_MARKETPLACE.read_text(encoding="utf-8"))
    plugins = marketplace.get("plugins")
    if marketplace.get("name") != "write-cut" or not isinstance(plugins, list):
        fail("Claude marketplace must declare the write-cut catalog")
    if not any(
        item.get("name") == "write-cut" and item.get("source") == "."
        for item in plugins
    ):
        fail("Claude marketplace must expose the repository root as write-cut")


def validate_evals() -> None:
    data = json.loads(EVALS.read_text(encoding="utf-8"))
    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) < 12:
        fail("evals/cases.json must contain at least 12 diverse cases")
    ids: set[str] = set()
    for case in cases:
        missing = {"id", "request", "input", "expect"} - case.keys()
        if missing:
            fail(f"eval case is missing fields: {sorted(missing)}")
        if case["id"] in ids:
            fail(f"duplicate eval id: {case['id']}")
        ids.add(case["id"])
        if not isinstance(case["expect"], list) or not case["expect"]:
            fail(f"eval {case['id']} has no expectations")


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.is_file()]
    if missing:
        fail(f"missing required files: {', '.join(missing)}")
    validate_skill()
    validate_repository()
    validate_evals()
    print("write-cut: OK")


if __name__ == "__main__":
    main()
