# Demo Recording Script — Hermes Comic

> Each "Scene" is a separate OBS recording. Total raw footage ~15-20 minutes.
> Final video will be cut to 60-90 seconds in post.
> Budget estimate for a full fresh run: ~$2-3 (OpenRouter Kimi + fal.ai).

## Setup once before recording

- **OBS Studio** → Settings → Video → base 1920×1080, FPS 30
- Source: Window Capture (Windows Terminal / WSL terminal)
- Secondary source: Browser (Firefox or Chrome in new window, clean profile)
- Mic off for now — we'll add ElevenLabs voice-over in post
- Create folder `recordings/` on Desktop for clips

## Pre-flight (do NOT record — setup only)

```bash
# WSL terminal
cd /mnt/c/Users/EREN/Desktop/nous/hermes-comic
export PATH="$HOME/.local/bin:$PATH"

# Sync skill (fresh copy of latest SKILL.md)
bash scripts/install_skill.sh

# Hermes starts clean each run, so nothing to reset
```

---

## Scene 1 — Skill invocation + Stage 1 proposal (~60 sec raw)

**Goal:** Show `/comic-series` slash command invoking skill + 3 creative framings.

**OBS: Start recording**

```bash
uv run hermes
```

**Wait** for the Hermes banner to fully render (2-3s).

**Then type:**
```
/comic-series Bana gezgin bir saatçi hakkında manga yap. Saatçi zamanı tamir ediyor, gölgeler onu durdurmaya çalışıyor.
```

Hit Enter.

**Watch** for:
- `⚡ Loading skill: comic-series`
- `[SYSTEM: The user has invoked...]` activation note
- Hermes types a short intro ("Manga Üretimine Hoş Geldin!")
- Environment setup command runs
- `uv run comic series propose ...` runs (~50s wait — you can let it record, we'll speed up in post)
- 3 framings with taglines appear
- Pick prompt at bottom

**Stop recording** once the 3 framings + pick prompt is visible.
Save as `scene_01_propose.mkv`

---

## Scene 2 — Pick + Stage 2 canon generation (~3 min raw)

**Goal:** Show user picking, Kimi generating canon, Hermes summarizing.

**OBS: Start recording** (hermes still open from Scene 1)

**Type:**
```
2
```

Hit Enter.

**Watch** for:
- Hermes responds "Mükemmel seçim!"
- Long `uv run comic series new "..." --title "..."` command runs (~2-3 min wait due to Kimi K2.5 reasoning)
- 4 canon files written (log lines visible)
- Hermes reads them back with `read_file`
- Canon summary in nice bullet format
- "Kabul ediyor musun?" prompt at bottom

**Stop recording** when summary + onay prompt is visible.
Save as `scene_02_canon.mkv`

---

## Scene 3 — Stage 3 character propose (~2 min raw)

**Goal:** Show 3 character archetypes appearing.

**OBS: Start recording**

**Type:**
```
kabul ediyorum devam et
```

Hit Enter.

**Watch** for:
- `uv run comic character propose "..."` runs (~50s)
- 3 archetypes appear (Kronos-Sakristan / Nötron-Gladyatör / Çağ-Kanama)
- Pick prompt

**Stop recording**.
Save as `scene_03_character_propose.mkv`

---

## Scene 4 — Reference generation + script self-patch (~3 min raw)

**Goal:** Flagship moment — Hermes auto-patches the gen_references script when it encounters an unknown character set. This is the "AI debugs its own tooling" demo gem.

**OBS: Start recording**

**Type:**
```
2
```

Hit Enter.

**Watch** for:
- `uv run python scripts/gen_references.py --character ...` fails (quick)
- Hermes reads `gen_references.py`
- `patch` tool modifies the file to add `ZAMAN_TAMIRCISI_CHARACTERS`
- Diff appears on screen (nice visual)
- Retry with `--set zaman-tamircisi` runs (~100s for 9 images)
- Candidate file paths listed
- Pick prompt

**Stop recording**.
Save as `scene_04_refgen_autopatch.mkv`

---

## Scene 5 — Reference pick + first chapter (~5 min raw)

**Goal:** Pick references, generate Chapter 1, render panels.

**OBS: Start recording**

**Type (pick any combination you like — 2,1,3 is good for demo):**
```
Portre: 2, Tam vücut: 1, Aksiyon: 3
```

Hit Enter.

**Watch** Hermes:
- Runs 3 `pick_ref.sh` commands
- Asks if you want the next character OR jump straight to chapter. Skip the next characters for brevity:

**Type:**
```
bu karakterle ilk bölümü yapalım, chapter 1 için bir beat öner
```

**Watch:**
- Hermes runs `uv run comic chapter propose "..."` (~50s)
- 3 chapter beats appear

**Type:**
```
1
```

**Watch:**
- `uv run comic chapter new "..."` runs (~1-2 min, Kimi)
- Panel spec summary appears
- Hermes asks if you want to render

**Type:**
```
evet render et
```

**Watch:**
- `uv run comic chapter render 1 --seed 42` runs (~3-5 min)
- Each panel completion logged
- Chapter composition summary
- Windows path to chapter.png

**Stop recording**.
Save as `scene_05_chapter_render.mkv`

---

## Scene 6 — Series export + publish (~1.5 min raw)

> **Shortcut for demo:** instead of generating all 3 chapters, we'll copy
> existing Neon & Ash chapter PNGs into the zaman-tamircisi workspace so
> `series export` + `series publish` work immediately. Pure demo theater.
>
> Do this BEFORE starting Scene 6 recording:
> ```bash
> # In a SEPARATE WSL terminal (not the hermes one):
> cd /mnt/c/Users/EREN/Desktop/nous/hermes-comic/workspaces/zaman-tamircisi
> mkdir -p chapters/02 chapters/03
> cp ../neon-and-ash/chapters/02/chapter.png chapters/02/
> cp ../neon-and-ash/chapters/02/spec.json   chapters/02/
> cp ../neon-and-ash/chapters/03/chapter.png chapters/03/
> cp ../neon-and-ash/chapters/03/spec.json   chapters/03/
> ```
> (You can keep the real flow if you have time — this is optional.)

**OBS: Start recording**

Back in the hermes terminal.

**Type:**
```
seriyi export et ve sonra publish et
```

**Watch:**
- `uv run comic series export` runs (~5s, PIL stitching)
- `workspaces/zaman-tamircisi/series.png` path printed
- Hermes: "publish istiyor musun?"

**Type:**
```
evet publish et
```

**Watch:**
- `uv run comic series publish --tagline "..." --domain hermes-zaman-tamircisi` runs (~20s)
- Deploy log
- **`✅ Published! URL: https://hermes-zaman-tamircisi.surge.sh`**

**Stop recording**.
Save as `scene_06_publish.mkv`

---

## Scene 7 — Browser + mobile view + share button (~30 sec raw)

**Goal:** The finale — click the URL, show real webtoon page live, tap share button, show pre-filled tweet.

**OBS: Start recording (browser window)**

1. Open **new Chrome/Firefox window** (clean, no extensions if possible)
2. Navigate to **https://hermes-zaman-tamircisi.surge.sh** (or reuse existing `hermes-neon-and-ash.surge.sh`)
3. **Show the header** — title, tagline, chapter count
4. **Scroll slowly** through Chapter 1 — show character consistency
5. **Scroll to bottom** — show the "Enjoyed it?" + big Share button
6. **Click Share on X** — X compose window opens with pre-filled tweet
7. **Show the tweet preview** — all 4 @mentions + hashtag + URL visible

**Stop recording**.
Save as `scene_07_live_share.mkv`

---

## Scene 8 — Mobile view (optional but great for demo)

**Goal:** Show responsive mobile view.

**Option A (simplest):** Chrome DevTools → Toggle Device Toolbar → iPhone 14 Pro → reload → record that.

**Option B (real mobile):** Phone record screen while scrolling the URL.

Save as `scene_08_mobile.mkv` (or `.mp4`).

---

## Files to send me after recording

1. All `scene_0N_*.mkv` files (OBS outputs)
2. Any retakes or bloopers
3. Optional: any scenes you want to redo (tell me which)

I'll cut them into a 60-90s submission video with:
- Hook opening (3s)
- Stages compressed with speed ramps where long
- Multimodal continuity + style evolve moments highlighted
- Finale: URL → share button → tweet

## Post-production additions (I'll do after you send clips)

- ElevenLabs English voice-over (60-75s narration script)
- Music bed (Pixabay/Epidemic royalty-free)
- Caption overlays (key moments + quotes from Hermes)
- Logo sting at start (Hermes + Kimi)
- End card: URL + GitHub link + tags

## Important cost/timing warnings

- **Total API spend for full fresh run (Scenes 1-7 recorded once):** ~$2-3
- **Budget remaining:** $20+ — plenty of headroom for 2-3 full retakes
- **Scene 5 alone takes ~10 min wall-clock** — most of it API waits that we'll speed up in post
- **Don't kill hermes between Scenes 1-6** — same session, context continues

## If something goes wrong

- Hermes stops responding / shows "max turns reached" → `/quit`, restart, continue from last completed Scene
- `comic` command errors → paste error to me, I'll fix and you re-record that scene
- Render fails on specific panel → skip that scene, we'll use existing chapter.png artifacts from neon-and-ash as demo footage
- Surge deploy fails → use existing `hermes-neon-and-ash.surge.sh` in Scene 7 instead

## TL;DR recording order

1. Pre-flight sync (no recording)
2. Scene 1: `/comic-series ...`
3. Scene 2: `2` → canon
4. Scene 3: `kabul ediyorum devam et` → character propose
5. Scene 4: `2` → refgen + self-patch
6. Scene 5: pick refs → chapter 1 flow
7. (Optional shortcut: copy chapter PNGs from neon-and-ash)
8. Scene 6: export + publish
9. Scene 7: browser tour + share button
10. Scene 8: mobile view

Send me the clips + I'll build the final 60-90s video.
