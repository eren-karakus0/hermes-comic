# Implementation Sprint — Hackathon Final Stretch

> Created: 2026-04-23
> Deadline: 2026-05-03 EOD PT (10 days)
> Approach: 2 days implementation + 3 days video + 2 days submission + 3-day buffer

## Scope — 5 tasks, ~9.5 hours total

| # | Task | Effort | Impact | Why |
|---|---|---|---|---|
| 1 | Cloudflare Pages backup deploy | 2h | Critical risk mitigation | Surge.sh free tier SLA yok. CF primary, Surge fallback |
| 2 | Chapter / series cover generator | 3h | High (Twitter card) | Current og:image = cropped chapter-01.jpg. Dedicated 1200×630 poster = profesyonel X embed |
| 3 | Progress indicators (rich bars) | 1h | Medium (video polish) | Render sırasında "donmuş mu?" hissi olmaz, post-edit hızlandırma temiz |
| 4 | One-shot `comic auto` command | 1.5h | High (demo moment) | Non-interactive full run — powerful showcase alternative to /comic-series |
| 5 | README submission writeup | 2h | Essential | Jury clone edip okur, GitHub'da ilk izlenim |

## Task breakdown

### Task 1 — Cloudflare Pages backup deploy (2h)

**Goal:** Primary deploy on Cloudflare Pages (99.99% SLA), Surge as secondary fallback.

**User-side setup (once, 5 min):**
1. https://dash.cloudflare.com — sign up (free)
2. Profile → API Tokens → Create Token → "Edit Cloudflare Pages" template
3. Copy Account ID from dashboard sidebar (under "Workers & Pages")
4. Add to `.env`:
   ```
   CLOUDFLARE_ACCOUNT_ID=<id>
   CLOUDFLARE_API_TOKEN=<token>
   ```

**Code-side:**
- `hermes_comic/publish.py` → add `deploy_cloudflare(bundle, project_name)` function using `wrangler pages deploy` (non-interactive via env vars)
- `cli.py` `series publish` → add `--provider cloudflare|surge|both` flag, default = `both` (primary CF, fallback Surge)
- Return both URLs on success; if CF fails, fall back silently to Surge only

**Acceptance:** `uv run comic series publish` returns `https://<slug>.pages.dev` as primary, Surge URL as backup.

### Task 2 — Cover generator (3h)

**Goal:** Generate a 1200×630 poster image per series, used as og:image for Twitter/Discord cards.

**Approach: Hybrid — Flux-LoRA generates art, PIL overlays title.**

1. `hermes_comic/cover.py` — new module:
   - `generate_cover_art(title, tagline, style_description)` — calls fal.ai flux-lora with landscape aspect, manhwa style
   - `compose_cover(art_bytes, title, tagline)` — PIL adds title (big, center-bottom) + tagline (smaller, under title)
   - Returns PNG bytes, saves to `<workspace>/cover.png`

2. `comic series cover` CLI command:
   - Reads canon for title + tagline
   - Optionally takes `--style` override
   - Outputs `workspaces/<slug>/cover.png`

3. Auto-invoke in `comic series publish`:
   - If `cover.png` doesn't exist, generate it first
   - Include in bundle as `cover.jpg`
   - Update og:image + twitter:image in index.html

**Acceptance:** After publish, check `<url>/cover.jpg` exists + Twitter card preview (cards-dev.twitter.com/validator) shows poster + title + tagline.

### Task 3 — Progress indicators (1h)

**Goal:** Rich progress bars during long operations — renders look professional on video.

**Where to add:**
- `panel_generator.render_all()` — replace print logs with `rich.progress.Progress` tracking N panels
- `scripts/gen_references.py` — same pattern
- `comic series publish` — 3-step progress (bundle → upload CF → upload Surge)

**Implementation:**
```python
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TextColumn("{task.completed}/{task.total}"),
    TimeElapsedColumn(),
) as progress:
    task = progress.add_task("Rendering panels...", total=len(jobs))
    for future in as_completed(futures):
        result = future.result()
        progress.advance(task)
        progress.update(task, description=f"panel {result.n} done")
```

**Acceptance:** render output shows live bar, no plain prints.

### Task 4 — One-shot `comic auto` (1.5h)

**Goal:** Single-command full-series generation. Non-interactive. Demo-ready.

**CLI:**
```bash
uv run comic auto "<premise>" \
    --title "<slug>" \
    --chapters 3 \
    --panels 8 \
    --publish
```

**Flow:**
1. Call `propose_series_variants` → pick alt[0] automatically (or `--pick N` to override)
2. Call `series new` with alt[0].framing
3. For each chapter 1..N:
   - `propose_chapter_beats` → pick alt[0]
   - `chapter new` with alt[0].beat
   - `chapter render` (no reference images — pure text2image + LoRA stack; character DNA from prompt)
4. `series export`
5. If `--publish`: `series publish`

**Note:** No character references (skips gen_references for speed). Character consistency from prompt + seed + LoRA.

**Acceptance:** `comic auto "test premise" --chapters 2 --panels 6` produces a rendered 2-chapter series in ~5-8 min with single command.

### Task 5 — README submission writeup (2h)

**Goal:** Jury-ready README.md at repo root. Replaces current placeholder.

**Structure:**
1. **Hero** — project name, tagline, live demo URL, cover image
2. **What it does** (3 sentences)
3. **Why (differentiation)** — Hermes integration, Kimi multimodal, live publish, self-improving style
4. **Demo video** — embedded (link to MP4 + YouTube backup)
5. **Architecture** — 6-stage pipeline diagram (ASCII or Mermaid)
6. **Quickstart** — 10-step run (WSL + env setup + hermes start)
7. **Tech stack** — list of dependencies with versions
8. **Credits** — Hermes, Kimi K2.5, fal.ai, Manhwa Style LoRA author, Surge, Cloudflare, Inter font
9. **License** — MIT

**Acceptance:** Standalone README.md that someone fresh can clone, follow, and end up with a published webtoon.

## Execution order

### Day 1 (today, 2026-04-23)

| Block | Task | ETA |
|---|---|---|
| Morning | User Cloudflare account setup (5 min) + I code deploy_cloudflare (1.5h) | 1.5h |
| Morning | Cover generator module + CLI (3h) | 3h |
| Afternoon | Progress indicators (1h) | 1h |
| Afternoon | One-shot `comic auto` (1.5h) | 1.5h |

**Day 1 total: 7h code** (user setup 5 min at the start)

### Day 2 (2026-04-24)

| Block | Task | ETA |
|---|---|---|
| Morning | README submission writeup (2h) | 2h |
| Midday | End-to-end test: `comic auto` full run + publish both providers | 30 min |
| Afternoon | Post-edit pending items — video hook plan, OBS setup verification | as needed |

**Day 2 total: 2.5h code + prep**

### Days 3-7 (2026-04-25 → 2026-04-29)

- Video recording (multiple takes per DEMO_RECORDING_SCRIPT.md)
- Post-production: hook edit, voice-over (ElevenLabs), music bed, captions
- Submission deliverables: tweet draft, Discord post message, GitHub public push

### Days 8-10 (2026-04-30 → 2026-05-03)

- Buffer — if anything goes wrong, re-do
- Final: submit on 2026-05-03 before EOD PT

## Task tracker

| # | Task | Status | ETA | Done |
|---|---|---|---|---|
| 1 | Cloudflare Pages deploy | ✅ done | 2h | 2026-04-23 |
| 2 | Cover generator | ✅ done | 3h | 2026-04-23 |
| 3 | Progress indicators (rich) | ✅ done | 1h | 2026-04-23 |
| 4 | One-shot `comic auto` | ✅ done | 1.5h | 2026-04-23 |
| 5 | README writeup + LICENSE | ✅ done | 2h | 2026-04-23 |

## Artifacts produced

- `hermes_comic/cover.py` (new, 190 lines) — fal-lora poster gen + PIL title overlay
- `hermes_comic/publish.py` — added `deploy_cloudflare()` function, cover.jpg integration
- `hermes_comic/panel_generator.py` — added `no_references` param + rich progress bar
- `hermes_comic/cli.py` — new `auto`, `series cover` commands, `--provider` flag on publish
- `scripts/gen_references.py` — rich progress bar
- `README.md` — full submission writeup
- `LICENSE` — MIT
- `IMPLEMENTATION_SPRINT.md` — this file (plan + tracker)
- `DEMO_RECORDING_SCRIPT.md` — video recording instructions (from earlier)

## Live URLs after sprint

- Cloudflare primary: https://hermes-comic-neon-and-ash.pages.dev  (0.4s load)
- Surge fallback: https://hermes-comic-neon-and-ash.surge.sh  (2.9s load, kept for redundancy)
- Cover Twitter preview: https://hermes-comic-neon-and-ash.pages.dev/cover.jpg

Status markers: ⏳ pending, 🔄 in progress, ✅ done, ⚠ blocked
