#!/usr/bin/env python3
"""Regenerate llms-full.txt: the entire bundle concatenated for single-paste LLM context.

Usage: python scripts/build-llms-full.py  (writes llms-full.txt from repo sources)
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "llms-full.txt"

ORDERED = [
    "README.md",
    "INSTAGRAM_GRAPH_API.md",
    "openapi.yaml",
    "types/instagram-graph.d.ts",
    "data/chunks.jsonl",
]
EXAMPLES = sorted((ROOT / "examples").glob("*.ts")) + sorted((ROOT / "examples").glob("*.py"))


def main():
    parts = [
        "# Instagram Graph API — Full Documentation (single-file for LLM context)",
        "> Generated: 2026-10-13",
        "> Source bundle: README.md + INSTAGRAM_GRAPH_API.md + openapi.yaml +",
        "> types/instagram-graph.d.ts + data/chunks.jsonl + examples/*",
        "",
    ]
    files = [ROOT / p for p in ORDERED] + EXAMPLES
    for path in files:
        rel = path.relative_to(ROOT)
        parts.append(f"\n===== FILE: {rel} =====\n")
        parts.append(path.read_text(encoding="utf-8").rstrip() + "\n")
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes, {len(files)} files)")


if __name__ == "__main__":
    main()
