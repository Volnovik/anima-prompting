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
  - refuses to convert a file that is already prompt-ready: feeding the
    prompt file back in as input would double-escape every tag's parens
    (a tag stored as \\( becomes \\\\() and corrupt the database

Display note: in the .jsonl output the escape backslash appears doubled —
the tag value  asuna \\(blue archive\\)  is stored in the raw file text as
asuna \\\\ (blue archive\\\\) . That is standard JSON escaping, not a double
escape: tagfetch.py decodes it and prints the single-backslash form. Copy
tag strings from tagfetch.py output, never from the raw file text.

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
             f"(hf download --repo-type dataset kierarkia/danbooru-wiki-2026 --include '*.jsonl' --local-dir {DATA_DIR})")


def already_prompt_ready(path: str) -> bool:
    """True if the file is (almost certainly) an already-transformed prompt
    file. In raw wiki data titles/aliases contain no backslash-paren at all
    (a handful of ASCII-art tag names excepted); in prompt-ready data every
    paren in titles/aliases is preceded by a backslash."""
    total = escaped = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            for v in [r.get("title", "")] + list(r.get("other_names") or []):
                total += v.count("(") + v.count(")")
                escaped += v.count("\\(") + v.count("\\)")
    return total > 0 and escaped * 2 > total


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = args[0] if len(args) > 0 else resolve_input()
    out = args[1] if len(args) > 1 else str(DATA_DIR / PROMPT_NAME)

    if Path(path).name == PROMPT_NAME or already_prompt_ready(path):
        sys.exit(f"input {path} is already prompt-ready (its title/alias parens are "
                 f"already escaped). Converting it again would double-escape every tag "
                 f"and corrupt the database. Pass the RAW dataset "
                 f"(danbooru_wiki_dataset_*.jsonl) as [input.jsonl] instead, or omit the "
                 f"argument to convert the newest raw file in {DATA_DIR}.")

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