---
name: anima-prompting
description: Write, rewrite, improve, or debug image-generation prompts for the Anima model (2B anime/illustration text-to-image model by CircleStone Labs with a small Qwen LLM text encoder, run in ComfyUI / Forge / A1111-style WebUIs). Use whenever the user asks for a prompt "for Anima", wants Anima booru-style tags written or checked, multi-character scenes, an Anima 4koma/comic layout, or an Anima generation that keeps misfiring (wrong style, unexpected high-contrast look, washed-out backgrounds, unwanted content). Covers tag structure, the mix of booru tags and natural language, per-version rules (Base/Aesthetic/Turbo), trap tags, troubleshooting, and on-demand lookup of exact tag spellings and meanings in a local Danbooru wiki database.
---

# Anima Prompting

Write prompts for **Anima** (`circlestone-labs/Anima`) — a 2B-parameter text-to-image model (derivative of `nvidia/Cosmos-Predict2-2B-Text2Image`, CircleStone Labs × Comfy Org). Focused on anime concepts/characters/styles plus other non-photorealistic art; **not** a photorealism model. Trained on several million anime images + ~800k non-anime artistic images (ye-pop LAION-POP, DeviantArt; no synthetic data; anime knowledge cutoff Sep 2025). Its text encoder is a small Qwen3 LLM (0.6B) plus an adapter that separates booru tags, so it genuinely understands prose as well as tags.

**The model card is the authoritative reference: `references/model-card.md` (bundled).** When this skill and the card differ, the card wins; when the model author's guide (civitai article 33857, distilled in `references/prompting-guide.md`) adds practical nuance, both apply.

**Precedence when rules conflict: the user's explicit request wins.** If the user explicitly asks for something a rule in this skill forbids (e.g. `score_*` on Aesthetic, `censored` in the positive), follow the user — but add one line explaining why the skill forbids it and what will likely happen, and let the user decide.

## Versions — check first

| Version | Behavior | Prompting consequences |
|---|---|---|
| **Anima-Base** | Unrefined base; maximum flexibility, diversity, style adherence. LoRAs are trained on Base (e.g. the author's Detailer/Delolifier work here). Default style is plain/neutral without artist or quality tags. | Recommended positive prefix: `masterpiece, best quality, score_7, safe,` — use it unless the user wants a flat/retro/painterly look (then drop quality tags). Recommended negative: `worst quality, low quality, score_1, score_2, score_3, artist name, blurry, jpeg artifacts, chromatic aberration` |
| **Anima-Aesthetic** | Style- and stabilization-tuned full finetune (v1.0b is the pure-aesthetics variant); consistent, high-quality default. | Quality tags unnecessary (safe to leave `masterpiece, best quality`); **do NOT use `score_*` tags in either positive or negative** — they push it into slop. Recommended negative: `worst quality, low quality, score_1, score_2, score_3, artist name, censored, signature, twins, jpeg artifacts, chromatic aberration` (Base's negative plus author's picks). |
| **Anima-Turbo** | Distilled; CFG 1, 8–12 steps; strong default style, reduced diversity; good for fast prompt iteration. | Same rules as Base for tags; expect less seed-to-seed variation. |

If the user doesn't specify, assume **Base** (and say so in one line; side note: the card recommends starting with **Anima-Turbo** for fast iteration). Also remember: sampler matters for style (er_sde = neutral default, euler_a = softer/thinner lines, dpmpp_2m_sde_gpu = wilder variety) — mention it when debugging style. If questioned - propose euler_a simple.

## The one rule

**Prompt for what you want to *see*, not what you want to feel.** Concrete, visible, specific. Anima was trained with tag dropout → enormous seed variation; a short grounded prompt beats a long vague one. For pure natural language, aim for at least two sentences — extremely short prompts give unexpected results.

## Prose: write for a 0.6B brain

The encoder is a small LLM. It understands prose, but it is small and literal — **write the prompt as if a caveman is supposed to use it: simple words, simple sentences, one visible fact per clause.**

- **No ambiguous pronouns.** In multi-character scenes, tie every detail to the character **by name in the same sentence** — "Mina grips his collar", never "she grips it". A stray "her" attaches to the wrong character (her hand ends up on someone else's head) and breaks the scene. Repeating the character name is fine and good.
- **Excess description of a single thing is not.** The model draws exactly what you describe, with its own limited skill: an exact description of every finger joint produces doll-like joints, not clean hands. Name the small features that matter, or commit to the achievable look. Never stack `detailed` / `clearly defined` / `highly` on an element — aspirational detail words add seed noise, not detail.
- **Do not describe what is not visible** in the requested scene (the color of a lollipop while it is in her mouth, the eyes behind a visor, anatomy under a closed garment) — the model will attempt to draw it.


## Prompt structure

Four main blocks, in this order (the model mixes everything into one bag anyway — order is a training-matched convention, but keep it):

```
quality/meta/year/safety tags
character count, character, series, artist
general tags
natural language description
```

- **Block 1** — the version's recommended prefix (Base: `masterpiece, best quality, highres,`; Aesthetic: `masterpiece, best quality,` + rating — do not suggest `score_*` in positive prompt if not asked by user) + time tags (`year 2025`, `newest`, `recent`, `mid`, `early`, `old`) + meta tags. Drop quality tags for low-detail looks or when debugging specific style.

## Safety tags — pick the rating

| Rating | Use for |
|---|---|
| `safe` | anything safe for work. **Default pick.** |
| `sensitive` | mild suggestiveness or non-sexual nudity. Content that may cause discomfort if viewed in public or in the workplace, but is not pornographic. |
| `nsfw` | strongly suggestive sexual content **without organs exposure**. |
| `explicit` | complete non-artistic exposure, hardcore pornography or extremely graphic content, exposed genitalia and gore — basically anything that does not fit in the other categories. |

Rules:
- Exactly **one** rating in the positive prompt, chosen by the most explicit content actually in the scene. `safe` is the default; the four ratings are categories, not a ladder — pick the one that fits, do not climb between them. Never mix ratings — `safe` in an explicit scene is a self-conflict and the render comes out soft/censored. `nsfw` alone is soft for scenes with exposed genitalia — that is `explicit`.
- **Remove rating tags if the scene structure/composition and user preference does not allow clear identification** — an unrateable scene gets no rating tag, not a guess.
- Put `censored` in the **negative** when you want explicit content uncensored; never `uncensored` in the positive.


- **Block 2** — count tag (`1girl`, `2girls`, `1boy`, `1other`, …), then character, then series, then `@artist` (the `@` prefix is **mandatory** — without it the artist effect is very weak). Canonical characters are identified as **"X from Series"** in their own prose sentence (e.g. "Mina from Blue Archive is lying on her stomach"); character/series **tags** in this block are reliable only for high-representation characters (check `post_count` in the tag database — couple hundred+ posts). For long-tail characters or characters with no tag at all, the prose name is the identifier — a sparse character tag at the top of the prompt confuses the model and can drop or merge characters. Advise user to search for a Lora in this case. 

- **Block 3** — one line of spaced tags: pose, attire, hair, expression, setting, composition, lighting. If a canonical tag names the thing, the tag is the instruction — prose adds placement, camera, and context only.
- **Block 4** — natural language description: caveman prose (above), at least two sentences for pure-NL prompts, standard capitalization for character and series names.
- **Non-anime art styles** use their own door instead of the anime bias: dataset tag at the very start of the prompt, then a newline: `ye-pop\n<alt-text line (optional)>\n<caption>` or `deviantart\n<title (optional)>\n<caption>`. Or specific tags that have \(medium\) in them.
- **4koma / comic strips** — the one layout where deep nesting works: `4koma` / `comic strip` + per-panel content (full recipe in `references/prompting-guide.md`). 
- Do **not** invent existing character deatures. Fetch them from database first.

## Visual clarity
** Always structure your prompts** Use double newline to separate blocks visually. You can have any number of blocks, for example separate description of the characters or background or comic panels etc.

## Left to right, top to bottom
When describing complex scenes - describe them left to right, top to bottom

## Multi-character bleed

**If you describe a feature of one character — facial expression, hand position, attire, hair state, *anything* — describe it for every character in the scene**, or the model bleeds it across characters (one girl's open mouth ends up on both). Undescribed characters inherit whatever the described ones have.

Placement: **no positional tags exist** in booru. Place characters with prose in reading order — left → right, then top → bottom, one clause per character; interleaving two characters back and forth invites identity swaps and misplaced elements.

## Workflow

1. **Load the starter tag set once** — read `references/starter-tags.txt` (some booru tags by group: backgrounds, body parts, character count, face tags, hair, image composition, posture, sex acts). It covers the everyday vocabulary; anything beyond it goes to the tag database (below). Do not re-read it mid-task. Skip it for a pure natural-language prompt that uses no tags.
2. **Pin the user's core request** — restate in one sentence exactly what the user asked for: subjects, count, action, setting, style, and anything they said must *not* be there. Every later step serves this sentence. If the user gives a mood, translate it into visible details.
3. **Expand the scene** — fill only what is unspecified (pose, clothing, expression, background). Expansion adds detail to the requested elements; it never replaces, overrides, or adds new actions, props, characters, or age descriptors the user did not ask for.
4. **Pick the prompt shape** — pure tags / natural language / mixed ("boorified language": prose with tags embedded where booru names the thing precisely). Mixed is the recommended default beyond a simple 1girl; pure NL for on-image text, precise scene logic, non-anime styles.
5. **Draft in caveman prose** — rules in "Prose: write for a 0.6B brain": simple words, simple sentences, one visible fact per clause, every detail tied to a character by name, no aspirational detail words, nothing invisible described.
6. **Tag it** — turn every precisely-named concept into a tag; look up in the tag database any tag you are not 100% sure of (spelling, meaning, bias strength); resolve aliases to canonical titles; read the body of unfamiliar tags before using them.
7. **Check the traps** — every ordinary English word in the prompt that is also a booru tag must be intentional: start from the trap table below (the pre-built worst offenders) and run any other suspicious word through the tag database — keep the tag deliberately, or replace the word with the meaning you actually want.
8. **Set the safety rating** — per the Safety section: exactly one rating, or none.
9. **Multi-character pass** — every described feature described for all characters (bleed rule); placement in reading order; each character identified as "X from Series" in their own natural language sentence.
10. **Assemble the structure** — the four blocks in order (quality/meta/year/safety → count/character/series/artist → general tags → natural language description). Formatting is part of the prompt: lowercase, **spaces instead of underscores** (the prompt-ready form is what `tagfetch.py` prints — copy it verbatim; the underscored form only exists in raw slugs/URLs and never goes into a prompt), `@` on every artist, single space after each comma, `score_N` the only underscored tag.
11. **Negative prompt** — start from the version's recommended negative (table above); add only what actually misfired (the tag whose *dataset bias* leaked, e.g. `simple background` for washed-out backgrounds, `censored` for uncensored scenes); fight styles/artists by naming them in the negative (`artist name` slot is the trick). Don't pre-cram 20 unrelated tags. Natural language works in negatives too. **Do not fill negative in first pass, use it to troubleshoot the image.** But check if standart negaiteve breaks your scene and adjust it in that case.
12. **Weighting — only when something under-reacts.** Anima needs far more weight than SDXL-era models: `(tag:1.5)` bare minimum, `2.0` sweet spot (card example: `(chibi:2)`). Works on tags, on phrases inside sentences, and in the negative. **Do not use weighting preliminary, only to troubleshoot the image**
13. **Check against the user's request** — before delivering, verify against the step-2 sentence: every requested element is present and unbroken by your expansion; nothing was added that the user didn't ask for (actions, props, characters, age descriptors); the scene is physically consistent (every garment permits everything claimed visible, every pose permits the viewpoint, nothing impossible).
14. **Verify against this skill** — final formatting pass: blocks in order, spacing rule, `@artist`, exactly one safety rating, no unhandled trap words, every tag in the prompt verified (tag database, starter list, or the curated sets below), deliverable is prompt text in the reply — **never write files** unless the user explicitly asks for a file.
15. **Deliver and iterate** — copy-pasteable positive + negative (plus LoRA lines, e.g. `<lora:anima_detailer:1>`), a 2–4 sentence rationale, and the next **prompt-level** debugging move: suggest user to roll seeds first; if a specific element misbehaves across several seeds it's a bias, not a seed problem — go to Troubleshooting. Your deliverable is the prompt, not the image — never suggest img2img/inpainting as a fix as a starter.

## Tag database — setup and on-demand lookup

Tag spellings, meanings and post counts come from a **local copy of the Danbooru wiki** (HuggingFace dataset `kierarkia/danbooru-wiki-2026`, WTFPL): ~203k JSON lines, one per tag that has a wiki page — `title`, `body` (the full wiki description: what the tag actually means, see-also links), `other_names` (aliases), `category_name`, `post_count`. Beyond a flat tag list, you get *meanings*, not just names.

Everything runs on two standard-library Python scripts in `scripts/` (Windows/Linux/macOS, nothing to install beyond Python 3.8+):
- `scripts/tagfetch.py` — on-demand tag lookup (the main tool)
- `scripts/transform_tags.py` — one-time conversion of the raw dump into prompt-ready spelling

**One-time setup** (once per machine, run from this skill folder; ~134 MB download):

```powershell
# Windows (PowerShell)
python -m venv .hfvenv
.\.hfvenv\Scripts\pip install -U "huggingface_hub[cli]"
.\.hfvenv\Scripts\hf.exe download kierarkia/danbooru-wiki-2026 --include "*.jsonl" --local-dir data
python scripts/transform_tags.py
```

```bash
# Linux/macOS
python3 -m venv .hfvenv
./.hfvenv/bin/pip install -U "huggingface_hub[cli]"
./.hfvenv/bin/hf download kierarkia/danbooru-wiki-2026 --include "*.jsonl" --local-dir data
python3 scripts/transform_tags.py
```

Step 4 writes `data/danbooru_wiki_prompt.jsonl`: every tag title and alias in prompt-ready form (`_`→space, `(`→`\(`), all other fields byte-identical. After that, lookups just work, and the venv + raw file may be deleted (re-download any time; the raw file is only needed again if the dataset updates). If there is no `data/` file: either run the one-time setup above first, or proceed with the starter list + curated sets below + your own knowledge — state which you did in the answer. The database is a **frozen snapshot (2026-04-28)**: tags whose wiki pages were created after that date are simply absent, so a lookup miss can mean "added later" as much as "never documented".

**Looking up tags** (the scripts work from any working directory; they resolve `data/` against this skill folder). On Windows call it as `python scripts\tagfetch.py …` — `python3` is usually not a command there, and the venv is only needed for the one-time `hf` download, not for lookups:

```bash
python3 scripts/tagfetch.py tareme                        # exact page; any spelling matches (case, underscores, prompt form)
python3 scripts/tagfetch.py "asuna (blue archive)" --full # complete body instead of the first 2500 chars
python3 scripts/tagfetch.py asuna --list                  # substring over all tag titles (e.g. every Asuna character)
python3 scripts/tagfetch.py FAMAS --in-body               # which pages *mention* FAMAS anywhere in the wiki text
python3 scripts/tagfetch.py pants --list --in-body        # match on title OR body
```

The output gives the **prompt-ready title** (copy it verbatim into the prompt), the id, category, `post_count`, the wiki description, and `other_names` aliases. Rules:
- **Copy the prompt-ready title verbatim — never re-introduce underscores from memory** or from a raw slug/URL. Prompt form is lowercase with spaces; `score_N` is the only exception.
- **Read the body before using an unfamiliar tag** — it says what the tag actually means. (`pants pull` = pants pulled down from their normal position; `downpants` = a glimpse down the back of pants — completely different things, easy to confuse.)
- Resolve aliases to the canonical title: users/LLMs usually produce the alias, the model wants the title — the title printed by `tagfetch.py` is the exact prompt string.
- If an exact/`--list` query misses, the concept may simply be named differently — run `--in-body` on a keyword (e.g. "who carries a FAMAS?" → finds `asuna (blue archive)`).
- The database covers the tags that **had a Danbooru wiki page** as of the snapshot (2026-04-28). Model-known tags without one (score tags, most human quality words, most time words) are absent from it — the curated sets below still apply. Never conclude a valid tag "doesn't exist" because a lookup came up empty — a miss can just mean the page post-dates the snapshot.
- `post_count` = how stereotyped/strong a tag's meaning is (high = strong training exposure and bias; a rare tag may do almost nothing) — and the proxy for how well the model knows a character.
- Where a tag differs between Danbooru and Gelbooru, **prefer the Gelbooru spelling** (the model's training naming). For artists, your own knowledge of well-known names/aliases is usually enough (or ask the user).
- **Same name, different franchise:** the same character name often has separate tags per franchise (`amatsukaze (kancolle)` ≠ `amatsukaze (azur lane)`). Check the parenthetical; if the character has no entry in the database, identify them in prose — never borrow another franchise's tag.

**Curated model-known tags** (✓ = has a Danbooru wiki page, confirm with `scripts/tagfetch.py`; unmarked = absent from the wiki but known to the model from training — use exactly as spelled):
- **Meta (generalization tags)**: `highres` ✓, `absurdres` ✓, `anime screenshot` ✓, `official art` ✓, `jpeg artifacts` ✓
- **Quality**: `masterpiece` (its wiki page is a stub saying "do not use" — ignore it; the card's recommended prefix wins), `best quality, good quality, normal quality, low quality, worst quality` · `score_1` … `score_10`
- **Time**: `year 2025`, `year 2024`, … · `newest, recent, mid, early` · `old` ✓
- **Safety**: `safe`, `sensitive`, `nsfw`, `explicit` — each has a wiki page, but it is a stub (post_count 0) whose body is Danbooru *search syntax* ("Use {{is:sfw}} instead.") — that is not a prompt tag: use the rating spelled here and ignore the stub's advice
- **Background anchors** (the washout/blank-wall bias family): `simple background` ✓, `white background` ✓, `dark background` ✓, `detailed background` ✓

**Invented "pseudo-tags"**: Anima accepts invented tag-style phrases for concepts booru never tagged (`platinum-blonde high twintails`), far better than a long prose workaround — but don't go full ham (`85mm anime cinematic lens` doesn't exist).

## Trap tags

Tags that **completely define** the image instead of adding a property. In booru these are ordinary tags with precise meanings; in natural-language prompts they are ordinary English words, so the model quietly applies the booru meaning and the whole generation snaps to a specific look. **Check the table below before writing any prompt**, and before any "why does my generation look like X" debugging.

| Trigger word / tag | What it actually does in Anima | LLM mistake | Do this instead |
|---|---|---|---|
| `high contrast` (DB name `high_contrast`; the hyphen form `high-contrast` is not a tag) | A specific, extreme, posterized high-contrast style — the image is *defined* by it | Writing "high contrast" in prose for "punchy, vibrant colors" | Name the actual colors (`crimson and teal palette`) — or `saturated` (real but weak); otherwise drop the phrase |
| `anime` (meta/screencap anchor; a known model tag that is **not** in the wiki database) | Anchors screencap/anime-styling look | Writing "anime style" in prose — the model is *already* anime, the extra word drags the look | Just describe the subject; style via artist tags or specific look tags |
| `anime_coloring`, `cel_shading_(2d)` | Specific flat cel-shaded fill style (alias of each other) | "clean cel shading" in prose | Use the tag deliberately when that look is wanted; otherwise avoid the word |
| `line art` / `line_art` (canonical tag: `lineart`, one word) | Line art only — black outlines, **no fill color** | "sharp, clean line art" in prose → uncolored line drawing | `lineart` only when that look is wanted; for "crisp lines" say nothing or use an artist tag |
| `lace` | Fabric made of lace — garment/texture is lace | "a little lace trim on the collar" in prose → the whole outfit becomes lace | `lace trim` is a separate tag for small lace accents; or phrase as "ribbon trim" |
| `wet` (aliases: `wet_skin`, `soaked`) | Wet glistening skin/clothing, droplets everywhere | "wet from the rain" in prose | `rain` for weather; `wet` only when glisten is intended |
| `colorful` | A specific saturated-palette tag | "colorful background/clothes" in prose | Name the actual colors (`red and blue dress`); or drop the word |
| `simple_background` (alias `/sbg`), `white_background`, `dark_background` | Strong background anchors; `simple_background` is the #1 dataset bias in the whole corpus — backgrounds wash out constantly | Describing a scene and letting the bias win | Describe the background in concrete detail ("Background is a cluttered bookshop with tall shelves and warm lamps" or "Room with furniture and single window" etc)|
| `anime screenshot` | Screencap-style composition/look | "cinematic anime scene" in prose | Use composition tags (`wide shot`, `from below`, `dutch angle`…) instead of the word "cinematic" if you want framing control |
| `monochrome` | Black-and-white image | "monochrome color palette" meaning *muted* colors → grayscale image | `muted color`, `pastel colors` |
| `blurry`, `blurred`, `depth_of_field` | Specific defocus/bokeh looks | "soft focus" in prose | Say exactly what should be sharp vs defocused in prose, or skip |
| `censored` | Censor bars (NSFW imagery) | Casual "keep it tasteful/censored" phrasing in a prompt | Never put `censored` in a positive prompt; use the fitting safety rating. `censored` in the **negative** is how you keep explicit content uncensored |
| `cosplay` | The depicted **character is dressing up as another fictional character** — on Danbooru this is usually a character cosplaying a character from a *different franchise*. The cosplayed target is tagged `name (cosplay)` (autotags add `name` + `cosplay`), and the target's copyright should be tagged too | Using `cosplay` to mean "wearing a costume" or "a real person in cosplay" | Character in a costume: character/series tags + `costume` or the specific outfit tags. Character cosplaying another: `other character (cosplay)` + both characters' copyrights. Real people: `cosplay photo` (a photo tag — off-model anyway) |
| `1other` | One non-human character (animals, creatures, objects-as-characters) | Using it for a single person | `1girl` / `1boy`; `1other` for animals/creatures (creative misuse that works) |
| `score_N` (Pony quality anchors) | Strong quality *and style* pull, each N (1-9) a different look; on **Aesthetic** they push into slop | Sprinkling several score tags "to be safe"; using any on Aesthetic | At most one on Base (recommended negative uses `score_1, score_2, score_3`); **zero on Aesthetic** |
| artist tag without `@` (e.g. `huke` instead of `@huke`) | The `@` prefix is **mandatory** — without it the artist's effect is very weak | Writing the artist name as a bare tag or in prose ("in the style of huke") with no `@` | `@huke` in the tag area / at the start of prose; if the style isn't landing, first check the `@` |

Also know:
- **Quality tags are style too.** `masterpiece, best quality, highres, absurdres` push glossy modern high-detail anime. For flat, retro, vintage, painterly, or low-detail looks: drop them (keep the safety rating if needed). This is the most common "why does it look like generic modern anime" complaint.
- **Version matters.** On **Aesthetic**, quality tags are unnecessary and `score_*` tags must not appear in *either* prompt (slop). On **Base**, the recommended prefix is `masterpiece, best quality, score_7, safe,`.
- **Every tag is a small LoRA.** A tag's meaning is the aggregate of millions of tagged images — inspect it in the local Danbooru wiki database (`data/danbooru_wiki_prompt.jsonl`, looked up with `scripts/tagfetch.py`); its `post_count` is the Danbooru post count. High `post_count` = strong, stereotyped meaning (and strong bias); a rare tag may do almost nothing. When a generation leaks an unwanted property, find the tag whose dataset biases it and put it in the negative.
- **Fight styles with the negative — including with names.** The model card's recommended negative ends with `artist name` on purpose: put the artist (or look) you are fighting in the negative prompt, not the positive.
- **Non-anime art has its own door.** For abstract/painterly/digital-art looks, start the prompt with the dataset tag `ye-pop` or `deviantart` + newline (see the Prompt structure section) instead of fighting the anime bias.
- **Nested tags are normal, not a mistake.** Booru lists `jacket` *and* `red jacket` on the same image. Including the general and the specific is standard.
- **When in doubt about a tag's meaning, check the database** — `post_count` tells you how strongly the model was trained on that exact meaning. Never conclude a tag "doesn't exist" from a miss: the database only holds tags with a wiki page.

## Troubleshooting — when the user is not ok with the result

Check in this order, and fix the prompt, not the image:

1. **No explicit descriptions of things that should not be in the image.** Re-read the prompt for details of elements that are occluded, absent, or impossible in the requested scene — a lollipop's color while it is in the mouth, the eyes behind a visor, anatomy under a closed garment, on-image text that can't be there. The model draws what you describe even when it shouldn't be visible. Remove or rephrase.
2. **Search the tag database for conflicting or misused tags.** Use the user's findings on the image (what appears that shouldn't, what's missing, what the image "looks like") and `scripts/tagfetch.py` (including `--in-body`) to find the tag or prose phrase that is responsible — ordinary English words that match booru tags snap to the tag's meaning (the trap table above is the pre-made list of the worst offenders), and aliases/misspellings can hit the wrong concept. Rephrase the prose or swap the tag.
3. **Character not drawn properly or not drawn at all** → add specific character features: hair color, eye color, hairstyle — **search the tag database for those features, do not remember or invent them** (your memory of canon is unreliable, and invented features fight the model's priors). Add the features to **all** characters in the scene, not just the failing one.
4. **Style misbehaving** → check quality tags, `score_*` usage (forbidden on Aesthetic), sampler choice, and the trap table first; fight the style/artist you are against via the negative (`artist name` slot).
5. **A concept seems "unknown"** → probably untagged; try a pseudo-tag before blaming the model.
6. **Prose not landing** → re-read as an image caption: one visible fact per clause, character named in every clause, names capitalized, pure NL ≥2 sentences.
7. **Non-anime look collapsing to anime** → add the `ye-pop` / `deviantart` dataset-tag header.
8. **Consistent misbehavior across seeds** → a **bias**, not a seed problem: find the tag whose dataset carries it (`post_count` + wiki body) and push it into the negative, or rephrase as a different tag.
9. **Scope note**: this skill delivers **prompts**, not images. If the prompt alone cannot fix it, reaching for img2img/inpainting (the author's Part 5 article, civitai 34963 — see `references/prompting-guide.md` Sources) is the user's call — never suggest it as a prompt fix.

## References

- `references/starter-tags.txt` — the starter tag set: most common tags by group, parsed from Danbooru tag-group wiki pages (character count and hair colors are marked standard sets, added because those group pages weren't in the download). **Load it once at the start of the task** (workflow step 1); covers everyday tag vocabulary without database lookups.
- `scripts/tagfetch.py`, `scripts/transform_tags.py` — lookup and one-time setup tools (standard-library Python, no installs); `data/danbooru_wiki_prompt.jsonl` — the local Danbooru wiki database they read (created by the setup steps above).
- `references/prompting-guide.md` — full distilled prompting guide: model behavior, versions and generation settings, tag vs prose tradeoffs, "boorified language", dataset tags, background bias, multi-character/4koma/design-sheet structure, worked examples. Read it when the task is non-trivial.
- `references/model-card.md` — the complete official model card, verbatim snapshot as of bundling (authoritative source; re-fetch from HuggingFace if you need the latest upstream wording).