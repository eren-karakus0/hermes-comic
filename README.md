# Hermes Comic

> **An AI comic series companion that remembers your world, your characters, and your style — chapter by chapter.**
>
> Built for the [Nous Research × Kimi (Moonshot AI) Creative Hackathon](https://x.com/NousResearch/status/2045225469088326039), May 2026.

<p align="center">
  <a href="https://hermes-comic-neon-and-ash.pages.dev">
    <img src="workspaces/neon-and-ash/cover.jpg" alt="Neon & Ash — live webtoon sample" width="720">
  </a>
  <br>
  <em>↑ click the cover to read the live sample webtoon</em>
</p>

## Live demo

- **Sample webtoon (Neon & Ash):** https://hermes-comic-neon-and-ash.pages.dev (primary, Cloudflare Pages)
- **Fallback mirror:** https://hermes-comic-neon-and-ash.surge.sh
- **Previous series (Red vs Blue):** `workspaces/red-vs-blue/series.png` (older pipeline, pre-art-upgrade)

## What it is

Hermes Comic is a **Hermes Agent skill** (`/comic-series`) that orchestrates a full creative pipeline for AI webtoon production:

1. **Proposes 3 creative framings** before committing to any premise
2. **Generates canonical series bible** (world, characters, style, continuity)
3. **Designs 3 character archetypes** per character, user picks
4. **Renders mobile-first vertical webtoons** with character DNA locked across chapters
5. **Publishes to a public URL** with one command (Cloudflare Pages + Surge fallback)
6. **Shares to X with a pre-filled tweet** — tagging the tools it used

The unique part: Hermes always **proposes alternatives before executing**, so every creative decision is a collaboration, not a one-shot LLM hallucination.

## Why Hermes + Kimi matters

Three features depend on the full Nous + Kimi stack — remove either and it breaks:

### 1. Multimodal continuity guardian (Kimi K2.5 flagship)
Before rendering each new chapter, Kimi K2.5 receives:
- full series canon (world-bible + character-bible + continuity-log)
- **previous chapter's rendered panels as images**
- the new chapter spec

It flags real visual inconsistencies across text AND images. Example from the live session:

> *"Chapter 1 images depict the motorcycle's headlamp emitting bright pink/magenta light, while Chapter 2 specifies a 'cyan headlamp'. This contradicts the established visual reference."*

This isn't possible without Kimi's 256k multimodal context. GPT-4 at 128k can't fit the canon + multiple panels + spec.

### 2. Self-improving skill (Hermes signature)
User feedback like *"less dialogue, more action"* is translated by Kimi into a concrete patch to `style-card.md` (auto version bump + history snapshot). The **next chapter** inherits the evolved style. The skill file literally changes. This is the promise of Hermes — tools that grow with you.

### 3. Plot twist proposer (Kimi K2-Thinking)
When the user hits a creative wall, `kimi-k2-thinking` takes 200-300 reasoning steps through the entire series arc and returns 3 alternative plot directions with 3-chapter outlines each. The "thinking" model earns its keep here.

## Pipeline architecture

```
/comic-series <premise>
       │
       ├─▶ Stage 1: propose 3 framings  (Kimi K2.5)
       │     user picks one
       │
       ├─▶ Stage 2: generate canon       (Kimi K2.5 → 4 markdown files)
       │     world-bible, character-bible, style-card, continuity-log
       │
       ├─▶ Stage 3: character design     (Kimi propose → fal.ai gen_references)
       │     3 archetypes per character, user picks
       │     18 reference images via flux-lora + Civitai Manhwa LoRA
       │
       ├─▶ Stage 4: chapter loop (×N)
       │     ├─ propose 3 beats         (Kimi)
       │     ├─ generate panel spec     (Kimi, ~10 panels)
       │     ├─ render panels           (fal.ai Flux Kontext LoRA, 5 parallel)
       │     ├─ multimodal continuity   (Kimi K2.5 sees previous panels)
       │     ├─ style feedback          (Kimi patches style-card.md)
       │     └─ plot twist (optional)   (Kimi K2-Thinking)
       │
       ├─▶ Stage 5: export              (PIL vertical stitch)
       │     series.png (25MB PNG composite) + cover.jpg (Twitter card)
       │
       └─▶ Stage 6: publish
             ├─ Cloudflare Pages (primary, 99.99% SLA)
             └─ surge.sh (fallback mirror)
                 URL + share-on-X button (pre-filled tweet)
```

## Quickstart

### Prerequisites

- WSL2 Ubuntu 22.04 (Windows) or Linux / macOS
- Python 3.11+
- `uv` (https://astral.sh/uv)
- npm + Node (for Cloudflare Pages + Surge deploys)

### Install

```bash
git clone https://github.com/<you>/hermes-comic
cd hermes-comic
bash scripts/bootstrap_env.sh   # Python 3.11, fonts, system deps
uv sync                         # installs hermes-agent + deps
cp .env.example .env            # fill in API keys (see below)
```

### API keys needed (`.env`)

| Key | What | Where to get |
|---|---|---|
| `OPENROUTER_API_KEY` | Kimi K2.5 + K2-Thinking | https://openrouter.ai |
| `FAL_KEY` | Flux Kontext + Flux LoRA | https://fal.ai |
| `MANHWA_LORA_URL` | Civitai Manhwa-Webtoon LoRA (HF mirror) | Upload `.safetensors` to HuggingFace |
| `CLOUDFLARE_ACCOUNT_ID` + `CLOUDFLARE_API_TOKEN` | Primary deploy target | https://dash.cloudflare.com |
| `SURGE_LOGIN` + `SURGE_TOKEN` | Fallback deploy target | `npx surge login && npx surge token` |

### Hermes skill install (one-time)

```bash
bash scripts/install_skill.sh
# real-copies `skills/comic-series/` to `~/.hermes/skills/` (Python rglob doesn't follow symlinks)
```

### Run it

**Interactive — recommended for authoring:**

```bash
uv run hermes
# inside hermes:
/comic-series I want a manga about a wandering clockmaker pursued by shadows
```

**One-shot — for demo / batch:**

```bash
uv run comic auto "A wandering clockmaker who mends time while shadows chase him" \
    --chapters 3 --panels 8
# generates + publishes in ~10 minutes, ~$2
```

**Per-stage CLI (power users):**

```bash
uv run comic series propose "<premise>"                      # 3 framings
uv run comic series new "<framing>" --title <slug>           # canon
uv run comic character propose "<name>" --role "<role>"      # 3 archetypes
uv run python scripts/gen_references.py --set <slug>         # 18 ref images
uv run comic chapter propose "<idea>"                        # 3 beats
uv run comic chapter new "<beat>" --panels 10                # spec
uv run comic chapter render 1 --seed 42 --concurrency 5      # render panels
uv run comic chapter continuity 2 --multimodal               # flagship
uv run comic chapter feedback "less dialogue, more action"   # style evolve
uv run comic chapter twist 3                                 # plot alternatives
uv run comic series cover --tagline "<one-liner>"            # poster
uv run comic series export                                   # series.png
uv run comic series publish --provider both                  # live URL + share
```

## Tech stack

- **Hermes Agent** (Python, `run_agent.AIAgent`) — skill orchestration, `openrouter` provider
- **Kimi K2.5** (via OpenRouter) — story gen, canon, multimodal continuity, style evolve
- **Kimi K2-Thinking** — plot twist proposer (long-horizon reasoning)
- **fal.ai Flux Kontext + Flux LoRA** — panel rendering with Civitai Manhwa/Webtoon LoRA
- **PIL / Pillow** — webtoon composition, speech bubbles, cover overlay
- **Cloudflare Pages** (primary) + **surge.sh** (fallback) — public deploy
- **Click + Rich** — CLI + progress indicators

## Budget (Neon & Ash sample series)

| Stage | Cost |
|---|---|
| Propose (series + characters + chapters) | ~$0.05 |
| Canon generation | ~$0.02 |
| Character references (18 images) | ~$0.60 |
| Chapter specs (3 chapters) | ~$0.09 |
| Chapter renders (28 panels × $0.035) | ~$0.98 |
| Multimodal continuity checks | ~$0.05 |
| Style feedback + plot twist | ~$0.05 |
| Cover generation | ~$0.04 |
| **Total** | **~$1.90** |

Publish (CF + Surge): free. Static hosting has no bandwidth cost.

## Credits

- **[Hermes Agent](https://github.com/NousResearch/hermes-agent)** — Nous Research
- **[Kimi K2.5 / K2-Thinking](https://platform.moonshot.ai/)** — Moonshot AI
- **[fal.ai Flux Kontext / Flux LoRA](https://fal.ai/)** — fal.ai
- **[Manhwa / Webtoon Style Flux LoRA](https://civitai.com/models/716348)** — Civitai community
- **[Inter font](https://rsms.me/inter/)**, **[Noto Sans](https://fonts.google.com/noto)** — Google / rsms
- **[Cloudflare Pages](https://pages.cloudflare.com/)** + **[Surge.sh](https://surge.sh)** — static hosting

## License

MIT — see `LICENSE` file.

## Contact

- **X:** [@Knkchn0](https://x.com/Knkchn0)
- **GitHub:** [eren-karakus0](https://github.com/eren-karakus0)
