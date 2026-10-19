# anima-prompting

An AI-agent skill for writing, rewriting, and debugging prompts for **[Anima](https://huggingface.co/circlestone-labs/Anima)** — the 2B-parameter anime/illustration text-to-image model by CircleStone Labs × Comfy Org (derived from `nvidia/Cosmos-Predict2-2B-Text2Image`, run in ComfyUI / Forge / A1111-style WebUIs).

Anima reads prompts through a **small Qwen3-0.6B LLM text encoder with a booru-tag adapter** — a "really small and stupid encoder" that will not get nuance. This skill teaches an agent to prompt for that encoder: **booru tags where a tag names the thing, caveman prose everywhere else** — simple words, one visible fact per clause, every detail tied to a character by name.

## What the skill does

- **Prompt structure** — the four-block convention (quality/meta/year/safety → character count/character/series/artist → general tags → natural language) with version-specific prefixes and negatives (Base / Aesthetic / Turbo).
- **On-demand tag lookup** — resolves any booru tag (spelling, meaning, alias, post-count/strength) against a **local copy of the Danbooru wiki** (~202k tags with full wiki bodies), so an agent never guesses a tag's bias or invents spellings.
- **Trap-tag awareness** — ordinary English words that are also booru tags (`high contrast`, `anime`, `simple background`, `censored`, …) that silently snap a generation to a specific look; checked before every prompt and every "why does this look like X" debug.
- **Multi-character discipline** — the bleed rule (describe every feature for every character), reading-order placement, per-character "X from Series" identification.
- **Safety ratings as categories, not a ladder** — `safe` / `sensitive` / `nsfw` / `explicit`, exactly one (or none), `censored` negative-only.
- **15-step workflow** — user request pinned first, scene expansion bounded by the request, and two final gates: check against the user's request, then verify against the skill. The deliverable is prompt text — seeds-first iteration, never img2img suggestions.
- **Troubleshooting** — wrong style, washed-out backgrounds, character drift/merging, soft or censored NSFW renders on degraded checkpoints.

## Install

**Preferred: feed this repo's link to your AI agent.** Tell it something like:

> Add this skill to your skills directory and run its one-time setup: https://github.com/<owner>/anima-prompting

The agent clones the repo into the skills directory (e.g. `~/.dsh/skills/anima-prompting/` for DeepSeek Harness, `~/.claude/skills/anima-prompting/` for Claude Code) and does the rest. Manual install: clone/copy the repo as an `anima-prompting/` folder inside your agent's skills directory — the repo root *is* the skill folder (`SKILL.md` sits at the top level).

## One-time data setup (per machine)

The skill works without the tag database (it falls back to the bundled starter set and curated lists, and says so); the database makes tag lookups much better. `huggingface_hub` may already be installed on the machine — try your regular Python first, and only fall back to a dedicated venv if it isn't. Run from the skill folder:

```powershell
# Windows — regular Python first
python -m huggingface_hub download kierarkia/danbooru-wiki-2026 --include "*.jsonl" --local-dir data
python scripts/transform_tags.py
# ...only if the download failed because huggingface_hub is not installed:
python -m venv .hfvenv
.\.hfvenv\Scripts\pip install -U "huggingface_hub[cli]"
.\.hfvenv\Scripts\python.exe -m huggingface_hub download kierarkia/danbooru-wiki-2026 --include "*.jsonl" --local-dir data
python scripts/transform_tags.py
```

```bash
# Linux/macOS — regular Python first
python3 -m huggingface_hub download kierarkia/danbooru-wiki-2026 --include "*.jsonl" --local-dir data
python3 scripts/transform_tags.py
# ...only if the download failed because huggingface_hub is not installed:
python3 -m venv .hfvenv
./.hfvenv/bin/pip install -U "huggingface_hub[cli]"
./.hfvenv/bin/python -m huggingface_hub download kierarkia/danbooru-wiki-2026 --include "*.jsonl" --local-dir data
python3 scripts/transform_tags.py
```

The venv (if created) is only for the download — tag lookups use standard-library Python. The raw dump and the venv may be deleted afterwards; the scripts only read `data/danbooru_wiki_prompt.jsonl`.

Smoke test (works from any working directory):

```bash
python3 scripts/tagfetch.py smile                # tag page: meaning, aliases, post count
python3 scripts/tagfetch.py amatsukaze --list    # every tag whose title contains the word
python3 scripts/tagfetch.py FAMAS --in-body      # which pages *mention* the keyword
```

Without the database the skill falls back to the bundled starter tag set, the curated model-known sets, and its own knowledge — and says so.

## Tag database: provenance

The lookup database is **derived from Danbooru** — specifically the [kierarkia/danbooru-wiki-2026](https://huggingface.co/datasets/kierarkia/danbooru-wiki-2026) Hugging Face dataset (WTFPL): every Danbooru tag that has a wiki page, with the full wiki body and aliases. The bundled snapshot is frozen at **2026-04-28**; tags whose pages were created after that date are simply absent from it. `transform_tags.py` rewrites only tag spelling into prompt-ready form (`_`→space, `(`→`\(`); everything else is byte-identical to the source. Danbooru data in this repo/dataset is WTFPL; this does not make the rest of the repo WTFPL, and Danbooru's own terms apply to the upstream data.

## Repository layout

```
SKILL.md                     the skill (agent entry point)
references/model-card.md     official Anima model card (verbatim snapshot, CircleStone Labs)
references/prompting-guide.md  distilled prompting guide (model card + author's Part 4 article)
references/starter-tags.txt  most common booru tags by group (offline fallback vocabulary)
scripts/tagfetch.py          on-demand tag lookup (standard-library Python 3.8+)
scripts/transform_tags.py    one-time raw-dump → prompt-ready JSONL conversion
data/                        (not in the repo — created by the one-time setup above)
```

## Sources

- Anima model card: [circlestone-labs/Anima](https://huggingface.co/circlestone-labs/Anima) (bundled verbatim in `references/model-card.md`)
- The author's prompting guide, Part 4: [civitai.com/articles/33857](https://civitai.com/articles/33857)
- Part 5 (img2img/inpainting, referenced by the skill's scope note): [civitai.com/articles/34963](https://civitai.com/articles/34963)
- Tag database: [kierarkia/danbooru-wiki-2026](https://huggingface.co/datasets/kierarkia/danbooru-wiki-2026) (Danbooru, WTFPL)
- Tag spelling cross-checks: [Danbooru](https://danbooru.donmai.us/) and [Gelbooru](https://gelbooru.com/) (Gelbooru spelling preferred where the two differ)

## License

Skill code, scripts, and documentation: **MIT** (see `LICENSE`).

Tag database: derived from the Danbooru wiki via the `kierarkia/danbooru-wiki-2026` dataset, **WTFPL**. Model card: official snapshot, © CircleStone Labs / Comfy Org — bundled for reference with attribution.

## Note: Danbooru data, Gelbooru spelling

Everything in this repo — the tag database, the starter tag set, the wiki bodies and post counts — is **based on Danbooru**, not Gelbooru. The model itself, per its author, prefers **Gelbooru** naming where a tag differs between the two sites, and the skill follows the model there: when a spelling disagrees, it emits the Gelbooru form. In practice the difference is niche and minimal — Danbooru and Gelbooru share the overwhelming majority of their tag vocabulary and spellings, so the Danbooru-based data is directly usable for Anima almost everywhere.