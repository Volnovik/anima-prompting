#!/usr/bin/env python3
"""tagfetch.py — fetch Danbooru wiki tag pages from this skill's local database.

Cross-platform (Windows/Linux/macOS), standard library only — no installs.
Works from any working directory: the default file resolves against this
skill folder (scripts/ .. = skill root, data/ = the database).

Usage:
  python3 tagfetch.py <query> [--full] [--list] [--in-body] [file.jsonl]

  <query>     any form works for title matches: "tareme", "asuna_(blue_archive)",
              or the prompt form "asuna (blue archive)" — all hit the same row
  --full      print the complete body (default: first 2500 chars, or a
              ~200-char context snippet in --in-body mode)
  --list      case-insensitive substring search over titles (no body printed)
  --in-body   case-insensitive substring search over the body column
              (prints context around the first hit, not the whole body).
              Combined with --list, a row matches if title OR body matches.
  file        dataset, defaults to <skill>/data/danbooru_wiki_prompt.jsonl
              (created by the one-time setup in SKILL.md; the raw
              danbooru_wiki_dataset_*.jsonl also works — titles there are
              not yet prompt-ready)
"""
import json
import sys
import time
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PROMPT_NAME = "danbooru_wiki_prompt.jsonl"
BODY_CAP = 2500
SNIP_SPAN = 100  # chars of context around a body hit, per side


def default_file() -> str:
    prompt = DATA_DIR / PROMPT_NAME
    if prompt.exists():
        return str(prompt)
    raw = sorted(p for p in DATA_DIR.glob("danbooru_wiki_*.jsonl") if p.name != PROMPT_NAME)
    if raw:
        print(f"note: using raw file {raw[-1].name} (titles not prompt-ready); "
              f"run scripts/transform_tags.py first", file=sys.stderr)
        return str(raw[-1])
    sys.exit(f"no dataset in {DATA_DIR} — run the one-time setup from SKILL.md "
             f"(hf download kierarkia/danbooru-wiki-2026 --include '*.jsonl' --local-dir {DATA_DIR})")


def canon(s: str) -> str:
    """Normalize a tag name to the booru form so any spelling matches:
    unescape parens, spaces -> underscores, lowercase."""
    return s.replace("\\(", "(").replace("\\)", ")").replace(" ", "_").lower()


def snippet(body: str, idx: int, qlen: int) -> str:
    start = max(0, idx - SNIP_SPAN)
    end = min(len(body), idx + qlen + SNIP_SPAN)
    text = body[start:end].replace("\n", " ")
    return ("…" if start > 0 else "") + text + ("…" if end < len(body) else "")


def main() -> int:
    # Wiki bodies are dense with CJK/emoji: a non-UTF-8 Windows console
    # (cp1251 etc.) would crash a plain print.
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass

    args = sys.argv[1:]
    full = "--full" in args
    listing = "--list" in args
    inbody = "--in-body" in args
    pos = [a for a in args if not a.startswith("--")]
    if not pos:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    query = pos[0]
    path = pos[1] if len(pos) > 1 else default_file()

    q = canon(query)
    qb = query.lower()
    t0 = time.time()
    n = 0
    hits = []  # (lineno, row, body-match-index or -1)
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            n += 1
            r = json.loads(line)
            t = canon(r["title"])
            body = r.get("body") or ""
            bidx = -1
            if inbody:
                bidx = body.lower().find(qb)
            title_hit = (q == t) if not listing else (q in t)
            if inbody:
                if bidx >= 0 or (listing and title_hit):
                    hits.append((lineno, r, bidx))
            elif title_hit:
                hits.append((lineno, r, -1))

    dt = time.time() - t0
    mode = "in body" if inbody else ("substring" if listing else "exact")
    if not hits:
        print(f"no {mode} match for {query!r} in {path}", file=sys.stderr)
        print(f"[scan] {n} rows in {dt:.1f}s -> 0 matches", file=sys.stderr)
        return 1

    for lineno, r, bidx in hits:
        body = r.get("body") or ""
        if listing:
            print(f"{r['title']} | id={r['id']} | {r['category_name']} | "
                  f"posts={r['post_count']:,} | line={lineno}")
            if bidx >= 0:
                print("    " + snippet(body, bidx, len(query)))
            continue
        if not inbody:
            print(f"=== {r['title']} | id={r['id']} | {r['category_name']} | "
                  f"posts={r['post_count']:,} | deleted={'yes' if r['is_deleted'] else 'no'}"
                  f" | updated={r['updated_at']} | line={lineno} ===")
            if len(body) > BODY_CAP and not full:
                print(body[:BODY_CAP])
                print(f"[... truncated at {BODY_CAP} chars, use --full for the complete body]")
            else:
                print(body)
            if r.get("other_names"):
                print("other_names: " + ", ".join(r["other_names"]))
        else:
            # in-body search: header + context around the first hit
            print(f"=== {r['title']} | id={r['id']} | {r['category_name']} | "
                  f"posts={r['post_count']:,} | line={lineno} ===")
            if full and body:
                print(body)
            elif bidx >= 0:
                print("    " + snippet(body, bidx, len(query)))
            elif body:
                print(body[:BODY_CAP])

    print(f"[scan] {n} rows in {dt:.1f}s -> {len(hits)} match(es) for {query!r} {mode}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())