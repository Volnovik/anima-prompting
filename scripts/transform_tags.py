#!/usr/bin/env python3
"""transform_tags.py — one-time setup: raw Danbooru wiki JSONL -> prompt-ready JSONL.

Cross-platform (Windows/Linux/macOS), standard library only — no installs.

Usage:
  python3 transform_tags.py [input.jsonl] [output.jsonl]

  input   defaults to the newest danbooru_wiki_*.jsonl in this skill's data/
          (excluding the *_prompt.jsonl output) — i.e. the raw file you
          downloaded per the setup steps in SKILL.md
  output  defaults to <skill>/data/danbooru_wiki_prompt.jsonl

What it does:
  - title and every other_names alias: "_" -> " ", "(" -> "\\(", ")" -> "\\)"
    (booru "asuna_(blue_archive)" becomes the prompt-ready "asuna \\(blue archive\\)")
  - every other field (body, category, post_count, ...) byte-identical
  - one JSON object per line, ensure_ascii=False (CJK kept readable)

Run it once after downloading the raw dataset. tagfetch.py works on either
file, but the prompt file gives copy-paste-ready tag strings.
"""
import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PROMPT_NAME = "danbooru_wiki_prompt.jsonl"


def transform(s: str) -> str:
    return s.replace("_", " ").replace("(", "\\(").replace(")", "\\)")


def resolve_input() -> str:
    raw = sorted(p for p in DATA_DIR.glob("danbooru_wiki_*.jsonl") if p.name != PROMPT_NAME)
    if raw:
        return str(raw[-1])
    if (DATA_DIR / PROMPT_NAME).exists():
        sys.exit(f"no raw dataset in {DATA_DIR} (only the transformed {PROMPT_NAME}); "
                 f"download the raw file first — see SKILL.md — or pass it as [input.jsonl]")
    sys.exit(f"no dataset in {DATA_DIR} — run the one-time setup from SKILL.md "
             f"(hf download kierarkia/danbooru-wiki-2026 --include '*.jsonl' --local-dir {DATA_DIR})")


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = args[0] if len(args) > 0 else resolve_input()
    out = args[1] if len(args) > 1 else str(DATA_DIR / PROMPT_NAME)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    n = 0
    t = a = 0
    with open(path, encoding="utf-8") as f, open(out, "w", encoding="utf-8") as o:
        for line in f:
            line = line.strip()
            if not line:
                continue
            n += 1
            r = json.loads(line)
            if r.get("title"):
                r["title"] = transform(r["title"])
                t += 1
            if r.get("other_names"):
                r["other_names"] = [transform(x) for x in r["other_names"]]
                a += 1
            o.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"rows={n:,} titles_transformed={t:,} rows_with_aliases_transformed={a:,}")
    print(f"input : {path}")
    print(f"output: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())