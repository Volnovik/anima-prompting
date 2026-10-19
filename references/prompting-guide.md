# Anima prompting guide (distilled)

Two source layers, both authoritative:
1. **The model card** (`references/model-card.md`, bundled verbatim) — architecture, versions, spelling rules, recommended prefixes/negatives.
2. **The author's "Anima Generation Guide – Part 4: Prompting"** (civitai article 33857) — practical prompting experience: tradeoffs, "boorified language", backgrounds, layouts, debugging. This file distills both; the full article is the source of truth for nuance.

## How the model reads prompts

- Anima is a **2B-parameter text-to-image model**, derivative of `nvidia/Cosmos-Predict2-2B-Text2Image` (CircleStone Labs × Comfy Org). **Not SDXL** — but it lives in the same WebUI/Forge/ComfyUI ecosystem, and the practical prompting habits are similar.
- Text encoder: **Qwen3 LLM (0.6B base)** + an adapter that separates booru tags from prose. It genuinely *understands* natural language (unlike pre-Anima anime SDXL models), so prose gives real control — including on-image text.
- Training: several million anime images + ~800k non-anime artistic images (LAION-POP `ye-pop` + DeviantArt, photos excluded, no synthetic data). Anime knowledge cutoff: September 2025.
- **Three versions:**
  - **Anima-Base** — unrefined; max flexibility/diversity/style adherence; plain neutral default style. LoRAs (e.g. the author's Detailer, Delolifier) are trained on Base. Prompt with the recommended prefix `masterpiece, best quality, score_7, safe,` unless a flat/retro look is wanted (then drop quality tags).
  - **Anima-Aesthetic** — style- and stabilization-tuned full finetune (v1.0b is the pure-aesthetics variant); consistent high-quality default. Quality tags unnecessary (safe to leave); **no `score_*` tags in positive or negative** (slop).
  - **Anima-Turbo** — distilled; CFG 1, 8–12 steps; strong default style, less diversity; ideal for fast prompt iteration.
- Generation settings: 512²–1536² px; 30–50 steps, CFG 4–5 (Base/Aesthetic). Samplers: `er_sde` neutral default (flat colors, sharp lines); `euler_a` softer/thinner lines, CFG can go a bit higher; `dpmpp_2m_sde_gpu` wilder variety; `euler` basic, good with Turbo/Aesthetic. Painterly/realistic-ish texture: beta57 scheduler (RES4LYF pack). **Sampler choice changes the style** — factor it into debugging.
- Trained with **random tag dropout** → huge seed-to-seed variation; you don't need every relevant tag, but prompts should still be grounded and specific.
- **Everything gets mixed in training** — the model treats any structure as one mixed bag of tags. Keep the four-block convention (SKILL.md "Prompt structure") anyway: it matches training order, keeps the prompt readable, and makes formatting mistakes visible.
- **Tag spelling: lowercase, spaces instead of underscores.** `score_N` is the only underscored tag. Where a tag differs between Danbooru and Gelbooru, **prefer the Gelbooru spelling** (that's how the model was named).
- Encoder limits: a concept inside a concept works; **double-nesting usually fails** (exception: comics/4koma). Complex sentences with many relations have less leeway than on bigger models.

## Booru tags — strengths

- Specific and wiki-documented; deep coverage of poses, expressions, and **anime hairstyles** especially.
- Each tag = a small LoRA: its meaning is the bias of its dataset. You can inspect a tag's bias via the booru, or via `post_count` in the local wiki database (SKILL.md tag database section).
- King of **single-character** prompting.

## Booru tags — weaknesses

- Weird nested structure (`jacket` *and* `red jacket` both present — that's normal, not a mistake).
- **No directional/positional tags** — no "on the left" in booru. Use prose for placement.
- Some areas shallow (certain clothes, settings).
- Dataset bias leaks into the model (the "simple background" epidemic).
- The local wiki database only covers tags that **had a Danbooru wiki page** in the 2026-04-28 snapshot. Model-known tags absent from it — score tags, most human quality words, most time words (`old` is the one time word with a page; `highres`/`absurdres` are meta words) — are still valid (curated sets in SKILL.md). The four safety ratings do have pages, but they are stubs whose "Use {{is:…}}" advice is Danbooru search syntax, not a prompt tag — ignore it. Never conclude a tag "doesn't exist" because a lookup missed — it may just post-date the snapshot.

## Natural language

- Anything can be written and is mostly understood; on-image text is native (single words and short phrases are reliable; long text won't render well).
- Cons: no wiki to tell you how a captioner phrased an effect; hard to troubleshoot (your phrasing vs. the model's ignorance). Words are hard.
- **Aim for at least 2 sentences; extremely short prompts give unexpected results.** More *visible facts* is better — not more adjectives (see SKILL.md "Prose: write for a 0.6B brain").
- Follow standard English capitalization for character and series names (capitalization matters).
- LLM-written prose can be subtly bad *for this model* — re-read your sentences: would a human captioner phrase it this way?
- **Write for a 0.6B brain** (SKILL.md "Prose" section): simple words, simple sentences, one visible fact per clause, no ambiguous pronouns — in multi-character scenes tie every detail to the character **by name in the same sentence**. Repeating the name is fine.
- **Do not re-describe a canonical character's canon features by default** (hair/face/eyes) — identify as "X from Series" and describe only what the user specified (outfit, pose, action, expression). Exception: the character fix in SKILL.md Troubleshooting, where added features come from the tag database, not memory.
- **Bleed rule**: if you describe a feature of one character, describe it for every character in the scene (SKILL.md "Multi-character bleed").

## Mixing — "boorified language"

The most powerful style: prose sentences with tags embedded where booru names the thing precisely.

- Worked example (from the guide):
  `A dutch angle shot of a girl sitting in yokozuwari on the hill. She has head tilt, blue eyes and half updo medium black hair and pink hair multicolored hair. She is dressed in medium dress. Her silver dress has side cutout, short sleeves. She is looking afar with her blue eyes. She has hand on own leg, and adjusting hair. Background is scenery landscape with blue sky and cloud. light rays, shadow,`
  — tags (`dutch angle`, `yokozuwari`, `head tilt`, `half updo`, `looking afar`, `hand on own leg`, `side cutout`, `light rays`) woven into sentences, all spaced.
- Quality/artist tags can lead a prose prompt: `masterpiece, best quality, @big chungus. An anime girl with medium-length blonde hair is…`
- Separate logical chunks with a blank line / line break — helps both you and the model (the Qwen tokenizer handles it; no Gemma-style token eating).
- Avoid markdown/JSON scaffolding in prompts — bloat can confuse the encoder.
- Civitai-style sites strip newlines from pasted prompts — add them back.

## Non-anime art — dataset tags

The model was separately trained on `ye-pop` (LAION-POP) and `deviantart` art. To route into that, put a **dataset tag at the very start of the prompt, followed by a newline**; the second line optionally carries the alt-text (ye-pop) or work title (deviantart):

```
ye-pop
For Sale: Others by Arun Prem
Abstract, oil painting of three faceless, blue-skinned figures…
```

This is the supported way to get abstract/painterly/digital-art looks instead of fighting the anime prior.

## Nonexistent tags

Anima accepts **invented tag-style phrases** for things booru never tagged — better than SD1.5/Pony/Illustrious/NoobAI ever did.
- Danbooru has `twintails`, `short twintails`, `low twintails`, `braided twintails` — but no `high twintails`. If the model insists on low twintails, prompt `platinum-blonde high twintails` as a pseudo-tag — works.
- Limit: don't invent absurdly specific pseudo-tags (`85mm anime cinematic lens`).

## Backgrounds

The most common misfire: a huge share of the corpus is `simple background` → detailed scenes collapse to a blank wall.
- Fix: **describe the background in concrete, specific detail** (contents, light, depth) or tag it (`scenery`, `detailed background`). The author's Detailer LoRA helps; it works without it, with more re-rolls.

## Style control

- Quality tags + `highres` = modern glossy high-detail anime. Remove for flat/retro/vintage/painterly (Base); on Aesthetic they're mostly redundant — and `score_*` are out entirely.
- `@artist` strongly anchors style (the `@` is mandatory — see trap tags). Mixing several artists blends styles.
- Series tags anchor the franchise's art direction (e.g. `sailor_moon` meta covers the character family).
- Time tags (`newest`, `year 2025`, `mid`, `old`) steer era.
- `score_N` anchors a specific Pony-aesthetic look — pick at most one, and never on Aesthetic.
- **Built-in style tags** — "mini-LoRAs baked into the model", often the most direct style lever:
  - `(style)` family: `toon (style)`, `western comics (style)`, era styles `1980s (style)` etc. (don't confuse with time tags like `year 2024`, which steer an *artist's* style by era), plus the `visual aesthetic` tag group and many artist-`(style)` tags.
  - `(medium)` family: `oil painting (medium)`, `watercolor (medium)`, `pencil (medium)`… (mostly under Danbooru's "traditional media" group).
  - Discover them on https://animadex.net/?mode=artists or https://tags.latent.moe/en/t?category=1 (the latter previews with quality tags, so looks can be off).
  - Caveat (author): quality tags (`masterpiece, best quality, highres`) can make a flat cartoonish style "too clean and crisp" — drop them when chasing that look.

## Structure conventions (practical)

The four blocks from SKILL.md "Prompt structure" — soft (the model mixes everything), but keep them:
1. quality/meta/year/safety tags (`masterpiece, best quality, highres, safe` — or nothing for retro looks)
2. character count, character, series, artist — `1girl, hood, azur lane, @artist` (the `@` is mandatory)
3. general tags — pose, attire, hair, expression, setting, composition, lighting
4. natural language description — caveman prose, each character named in its own clause

Full tag example from the model card:
`year 2025, newest, normal quality, score_5, highres, safe, 1girl, oomuro sakurako, yuru yuri, @nnn yryr, smile, brown hair, hat, solo, …`

## Special layouts

- **Multi-character**: count tag + each character identified as "X from Series" in its own clause; placement from prose in reading order (left → right, then top → bottom); the bleed rule applies — every feature described for one character must be described for all.
- **4koma / comics**: supported — `4koma` / `comic strip` with per-panel content is the one case where deeper nesting works.
- **Character design sheets**: "character design sheet, front and side views, expression sheet, multiple views of the same character" + character tags.
- **On-image text**: natural language with quoted titles works natively.

## Small tips

- Spaces, not underscores, in all tags (`half updo`); `score_N` is the only underscored tag.
- Weighting: `(tag:1.5)` minimum, `2.0` sweet spot — far more than SDXL-era models need; works in prose phrases and negatives.
- Comma hygiene for pure tag lists: single space after commas, no double commas, no typos — the encoder doesn't fuzzy-match misspelled tags.
- Prompt for what you want to **see**, not feel.

## Worked examples (from the guide — Anima Base + author's Detailer & Delolifier LoRAs)

Simple 1girl, tag-heavy (prefix here is the author's variant — `highres` instead of `score_7`; the card's prefix from the version table is the default):
```
masterpiece, best quality, highres, safe,
1girl, solo, standing, looking afar, wheat field, sun, sky, green eyes, platinum-blonde hair, hair bun, curtained hair, blue dress, ornate, holding basket, basket, apple, adjusting hair, loose hair strand, parted lips, tareme, sunset, puffy short sleeves, white choker, white corset, gloves, x hair ornament, fantasy, dutch angle,
```

Pure natural language (with on-image text):
```
Oil painting on canvas of chandelier standing on the table in a dark room illuminated only by it's blue flames. On the left of chandelier lies a green apple. On the right of chandelier lies a red book with title "See?". Distinct brush strokes.
```

Mixed — see "boorified language" above.

## Debugging loop

1. Consistent misbehavior across seeds → a **bias**, not a seed problem. Find the tag whose dataset carries it (local wiki database, `post_count`) and push it into the negative, or rephrase as a different tag.
2. *Style* misbehaving → check quality tags, `score_*` usage (forbidden on Aesthetic), sampler choice, and the trap table in SKILL.md first.
3. A concept seems "unknown" → probably untagged; try a pseudo-tag before blaming the model.
4. Prose not landing → re-read as an image caption; one visible fact per clause; capitalize character/series names properly; pure NL needs ≥2 sentences.
5. Non-anime look collapsing to anime → add the `ye-pop` / `deviantart` dataset-tag header.
6. Character mis-drawn or missing → add DB-sourced features (hair color, eye color, hairstyle) to **all** characters — SKILL.md Troubleshooting.
7. The full ordered checklist (occluded-detail check, tag-database conflict search, character fix) lives in SKILL.md "Troubleshooting".
8. **Scope note**: this skill delivers **prompts**, not images. If the prompt alone cannot fix it, reaching for img2img/inpainting (the author's Part 5 article, civitai 34963 — see Sources below) is the user's call — never suggest it as a prompt fix.

## Sources

- Model card (authoritative, bundled as `references/model-card.md`): https://huggingface.co/circlestone-labs/Anima
- Part 4 prompting guide (author's practical layer): https://civitai.com/articles/33857
- Tag naming cross-checks: https://danbooru.donmai.us/ · https://gelbooru.com/ (preferred spelling where the two differ) · https://safebooru.org/
- Tag database source: HuggingFace dataset `kierarkia/danbooru-wiki-2026` (WTFPL) — local copy in this skill's `data/danbooru_wiki_prompt.jsonl`, looked up with `scripts/tagfetch.py` (setup steps in SKILL.md)
- Part 5 (img2img/inpainting): https://civitai.com/articles/34963