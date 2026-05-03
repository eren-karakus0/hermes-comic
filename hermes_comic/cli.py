"""Hermes Comic CLI — `comic series new`, `comic chapter new`, etc."""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import click

from hermes_comic import canon
from hermes_comic.kimi_client import KimiClient
from hermes_comic import prompts


def _slug(s: str) -> str:
    s = re.sub(r"[^\w\s-]", "", s.lower()).strip()
    s = re.sub(r"[\s_-]+", "-", s)
    return s[:40] or "series"


@click.group()
@click.option(
    "--workspace",
    type=click.Path(path_type=Path),
    default=None,
    help="Workspace dir (defaults to HERMES_COMIC_WORKSPACE or ./workspaces/red-vs-blue)",
)
@click.pass_context
def cli(ctx: click.Context, workspace: Path | None) -> None:
    """Hermes Comic — AI comic series companion."""
    if workspace:
        os.environ["HERMES_COMIC_WORKSPACE"] = str(workspace.resolve())
    ctx.ensure_object(dict)
    ctx.obj["workspace"] = canon.get_workspace()


# ─── series ───────────────────────────────────────────────────────────────

@cli.group("series")
def series_grp() -> None:
    """Series-level commands."""


@series_grp.command("propose")
@click.argument("premise", nargs=-1, required=True)
def series_propose(premise: tuple[str, ...]) -> None:
    """Propose 3 creative framings from a rough premise (before `series new`)."""
    from hermes_comic.propose import propose_series_variants

    premise_str = " ".join(premise).strip()
    click.echo(f"[propose series] Kimi K2.5 drafting 3 framings...\n  for: {premise_str[:160]}")
    alts = propose_series_variants(premise_str)
    click.echo(f"\n{len(alts)} framings:\n")
    for i, alt in enumerate(alts, 1):
        click.echo(f"  [{i}] {alt.get('title', 'untitled')}")
        click.echo(f"      tagline: {alt.get('tagline', '')}")
        click.echo(f"      {alt.get('framing', '')}\n")
    click.echo("Pick one (1/2/3, or mix) — then `comic series new \"<framing>\"`")


@series_grp.command("new")
@click.argument("premise", nargs=-1, required=True)
@click.option("--title", default=None, help="Short series title (used for slug)")
def series_new(premise: tuple[str, ...], title: str | None) -> None:
    """Initialize a new series canon from a premise."""
    premise_str = " ".join(premise).strip()
    series_slug = _slug(title or premise_str[:40])

    click.echo(f"[series new] slug={series_slug}")
    click.echo(f"[series new] premise: {premise_str[:200]}")

    client = KimiClient()
    messages = [
        {"role": "system", "content": prompts.SERIES_SYSTEM},
        {
            "role": "user",
            "content": prompts.SERIES_USER_TEMPLATE.format(
                premise=premise_str, series_slug=series_slug
            ),
        },
    ]
    click.echo("[series new] Kimi K2.5 generating canon...")
    result = client.complete_json(messages, temperature=0.6, max_tokens=10000)

    keymap = {
        "world_bible": "world-bible",
        "character_bible": "character-bible",
        "style_card": "style-card",
        "continuity_log": "continuity-log",
    }
    for jkey, fname in keymap.items():
        if jkey not in result:
            raise click.ClickException(f"Kimi response missing key: {jkey!r}")
        path = canon.write_canon(fname, result[jkey])
        click.echo(f"  wrote {path}")

    click.echo(
        f"\n[series new] done. {client.total_input_tokens}→{client.total_output_tokens} tokens."
    )


@series_grp.command("status")
def series_status() -> None:
    """Print current canon state summary."""
    if not canon.canon_is_initialized():
        click.echo("[status] canon NOT initialized — run `comic series new` first")
        return

    click.echo(f"workspace: {canon.get_workspace()}")
    click.echo(f"next chapter: {canon.next_chapter_number():02d}")
    click.echo("\ncanon sizes:")
    for n in canon.CANON_FILES:
        content = canon.read_canon(n)
        click.echo(f"  {n}: {len(content)} chars")

    chapters_dir = canon.get_workspace() / "chapters"
    if chapters_dir.exists():
        chapters = sorted(p.name for p in chapters_dir.iterdir() if p.is_dir())
        click.echo(f"\nchapters: {chapters or '(none)'}")


# ─── character ────────────────────────────────────────────────────────────

@cli.group("character")
def character_grp() -> None:
    """Character design commands."""


@character_grp.command("propose")
@click.argument("name")
@click.option("--role", default="main character", help="Role in the story")
def character_propose(name: str, role: str) -> None:
    """Propose 3 character design archetypes before generating references."""
    from hermes_comic.propose import (
        current_canon_context,
        propose_character_designs,
    )

    click.echo(f"[propose character] Kimi K2.5 drafting 3 designs for {name}...")
    alts = propose_character_designs(
        name, role=role, context=current_canon_context(max_chars=2000)
    )
    click.echo(f"\n{len(alts)} designs for {name}:\n")
    for i, alt in enumerate(alts, 1):
        click.echo(f"  [{i}] {alt.get('archetype', 'untitled')}")
        click.echo(f"      visual:      {alt.get('visual', '')}")
        click.echo(f"      personality: {alt.get('personality', '')}")
        click.echo(f"      voice:       {alt.get('voice', '')}\n")
    click.echo(f"Pick one — confirm to user, then generate references with the chosen visual.")


# ─── chapter ──────────────────────────────────────────────────────────────

@cli.group("chapter")
def chapter_grp() -> None:
    """Chapter-level commands."""


@chapter_grp.command("propose")
@click.argument("idea", nargs=-1, required=True)
@click.option("--chapter", type=int, default=None,
              help="Chapter number (default: next unrendered chapter)")
def chapter_propose(idea: tuple[str, ...], chapter: int | None) -> None:
    """Propose 3 chapter beat alternatives before generating the spec."""
    from hermes_comic.propose import (
        current_canon_context,
        propose_chapter_beats,
    )

    idea_str = " ".join(idea).strip()
    if chapter is None:
        chapter = canon.next_chapter_number()
    click.echo(f"[propose chapter {chapter}] Kimi K2.5 drafting 3 beats for: {idea_str[:160]}")
    alts = propose_chapter_beats(
        idea_str, chapter_num=chapter, canon_context=current_canon_context(max_chars=3500)
    )
    click.echo(f"\n{len(alts)} beats:\n")
    for i, alt in enumerate(alts, 1):
        click.echo(f"  [{i}] {alt.get('title', 'untitled')}")
        click.echo(f"      hook: {alt.get('hook', '')}")
        click.echo(f"      {alt.get('beat', '')}\n")
    click.echo(f"Pick one (1/2/3) — then `comic chapter new \"<beat>\"`")


@chapter_grp.command("new")
@click.argument("beat", nargs=-1, required=True)
@click.option("--panels", type=int, default=10, show_default=True,
              help="Target panel count for this chapter (6-20 typical)")
def chapter_new(beat: tuple[str, ...], panels: int) -> None:
    """Generate next chapter spec from a beat string."""
    if not canon.canon_is_initialized():
        raise click.ClickException("canon empty — run `comic series new` first")

    if not 4 <= panels <= 24:
        raise click.ClickException(f"--panels must be 4-24 (got {panels})")

    beat_str = " ".join(beat).strip()
    chapter_num = canon.next_chapter_number()
    click.echo(f"[chapter new {chapter_num:02d}] target {panels} panels")
    click.echo(f"[chapter new {chapter_num:02d}] beat: {beat_str[:200]}")

    snap = canon.snapshot_before(chapter_num)
    click.echo(f"  snapshot → {snap}")

    cfiles = canon.read_all_canon()
    client = KimiClient()

    messages = [
        {"role": "system", "content": prompts.CHAPTER_SYSTEM},
        {
            "role": "user",
            "content": prompts.CHAPTER_USER_TEMPLATE.format(
                chapter_num=chapter_num,
                beat=beat_str,
                target_panels=panels,
                world_bible=cfiles["world-bible"],
                character_bible=cfiles["character-bible"],
                style_card=cfiles["style-card"],
                continuity_log=cfiles["continuity-log"],
            ),
        },
    ]
    click.echo(f"[chapter new {chapter_num:02d}] Kimi K2.5 generating panel spec...")
    # 12000 token budget — scales with panel count; more panels = more reasoning + output
    spec = client.complete_json(messages, temperature=0.7, max_tokens=12000)

    # persist spec
    cdir = canon.chapter_dir(chapter_num)
    cdir.mkdir(parents=True, exist_ok=True)
    spec_path = cdir / "spec.json"
    spec_path.write_text(
        json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    click.echo(f"  wrote {spec_path}")

    # append continuity update to continuity-log.md
    if spec.get("continuity_updates"):
        existing = canon.read_canon("continuity-log")
        new_log = existing.rstrip() + "\n\n" + spec["continuity_updates"].strip() + "\n"
        canon.write_canon("continuity-log", new_log)
        click.echo("  appended to continuity-log.md")

    # preview
    click.echo()
    click.echo(f"  title:   {spec.get('title')}")
    click.echo(f"  summary: {spec.get('summary')}")
    click.echo(f"  panels:  {len(spec.get('panels', []))}")
    for p in spec.get("panels", []):
        desc = p.get("description", "")
        dlg = p.get("dialogue") or []
        dialogue_line = " | ".join(
            f"{d.get('speaker', '?')}: {d.get('text', '')[:40]}" for d in dlg
        )
        click.echo(f"    [{p.get('n', '?')}] {desc[:90]}")
        if dialogue_line:
            click.echo(f"         💬 {dialogue_line}")

    click.echo(
        f"\n[chapter new {chapter_num:02d}] done. {client.total_input_tokens}→{client.total_output_tokens} tokens."
    )


@chapter_grp.command("feedback")
@click.argument("feedback", nargs=-1, required=True)
def chapter_feedback(feedback: tuple[str, ...]) -> None:
    """Patch canon/style-card.md from user feedback (auto version bump + history snapshot)."""
    from hermes_comic.style_evolve import run as run_style

    text = " ".join(feedback).strip()
    click.echo(f"[feedback] {text[:160]}")
    out = run_style(feedback=text)
    click.echo(f"  snapshot → {out['snapshot']}")
    click.echo(f"  summary:  {out['change_summary']}")
    click.echo(f"  tokens:   in={out['tokens_in']} out={out['tokens_out']}")


@chapter_grp.command("continuity")
@click.argument("chapter_num", type=int)
@click.option("--multimodal/--text-only", default=False,
              help="Feed previous chapter panel images to Kimi")
def chapter_continuity(chapter_num: int, multimodal: bool) -> None:
    """Run continuity check on a chapter spec."""
    from hermes_comic.continuity import check as run_check

    mode = "MULTIMODAL" if multimodal else "text-only"
    click.echo(f"[continuity {chapter_num:02d}] Kimi K2.5 check ({mode})...")
    try:
        result = run_check(chapter_num=chapter_num, multimodal=multimodal)
    except FileNotFoundError as e:
        raise click.ClickException(str(e))

    click.echo(f"  report → {result['report_path']}")
    click.echo(f"  images used: {result['images_used']}")
    report = result["report"]
    if report.get("clean"):
        click.echo("  [OK] no issues")
        return
    warnings = report.get("warnings", [])
    click.echo(f"  [WARN] {len(warnings)} issue(s):")
    for w in warnings:
        panel = w.get("panel")
        prefix = f"panel {panel}" if panel else "global"
        click.echo(f"    - {prefix}: {w.get('issue')}")
        if w.get("fix"):
            click.echo(f"      fix: {w['fix']}")


@chapter_grp.command("twist")
@click.argument("starting_chapter", type=int)
def chapter_twist(starting_chapter: int) -> None:
    """Propose 3 plot twist alternatives via Kimi K2-Thinking."""
    from hermes_comic.plot_twist import run as run_twist

    click.echo(f"[twist] Kimi K2-Thinking proposing alternatives from chapter {starting_chapter}...")
    result = run_twist(starting_chapter=starting_chapter)
    alts = result.get("alternatives", [])
    click.echo(f"  {len(alts)} alternatives:")
    for i, alt in enumerate(alts, 1):
        if isinstance(alt, dict):
            click.echo(f"\n  ── [{i}] {alt.get('title', 'untitled')} ──")
            if alt.get("twist"):
                click.echo(f"    twist: {alt.get('twist')}")
            for co in alt.get("chapter_outlines", []) or []:
                if isinstance(co, dict):
                    click.echo(f"      Ch {co.get('n')}: {str(co.get('beat', ''))[:120]}")
                else:
                    click.echo(f"      {str(co)[:140]}")
        else:
            click.echo(f"\n  ── [{i}] (raw string) ──")
            click.echo(f"    {str(alt)[:320]}")
    click.echo(f"\n  saved → {result.get('_persisted_to')}")
    click.echo(f"  tokens: in={result.get('_tokens_in')} out={result.get('_tokens_out')}")


@chapter_grp.command("render")
@click.argument("chapter_num", type=int)
@click.option("--seed", type=int, default=None, help="Fixed seed for deterministic output")
@click.option("--concurrency", type=int, default=5, show_default=True,
              help="Parallel render workers (5 balances speed vs fal.ai rate limits; drop to 3 if errors)")
def chapter_render(chapter_num: int, seed: int | None, concurrency: int) -> None:
    """Render panels + compose webtoon page for a generated chapter."""
    from hermes_comic.composer import compose_chapter
    from hermes_comic.panel_generator import build_jobs, render_all

    spec_path = canon.chapter_dir(chapter_num) / "spec.json"
    if not spec_path.exists():
        raise click.ClickException(f"spec missing: {spec_path}")

    click.echo(f"[render {chapter_num:02d}] building job plan...")
    jobs = build_jobs(chapter_num)
    click.echo(f"  {len(jobs)} panels")
    for j in jobs:
        click.echo(
            f"    panel {j.n}: {j.primary_character or 'none'}/{j.reference_pose or '-'} "
            f"[refs: {j.refs_label}]"
        )

    click.echo(f"\n[render {chapter_num:02d}] rendering (concurrency={concurrency})...")
    results = render_all(jobs, concurrency=concurrency, seed=seed)
    ok_count = 0
    for job, ok, msg in results:
        status = "OK" if ok else "FAIL"
        if ok:
            ok_count += 1
        click.echo(f"    [{job.n}] {status} — {msg}")

    if ok_count < len(results):
        raise click.ClickException(f"only {ok_count}/{len(results)} panels succeeded")

    click.echo(f"\n[render {chapter_num:02d}] composing webtoon...")
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    dialogues_by_n = {p["n"]: (p.get("dialogue") or []) for p in spec["panels"]}
    panel_paths = [j.out_path for j in jobs]
    dialogues = [dialogues_by_n.get(j.n, []) for j in jobs]

    out = canon.chapter_dir(chapter_num) / "chapter.png"
    compose_chapter(panel_paths, dialogues, out)
    click.echo(f"  wrote {out}")
    click.echo(f"\n[render {chapter_num:02d}] done")


@series_grp.command("cover")
@click.option("--hero-visual", default=None,
              help="Override the hero character visual (default: auto-extract from character-bible)")
@click.option("--tagline", default=None,
              help="Tagline overlaid under the title (default: auto-extract from world-bible)")
@click.option("--style", default=None,
              help="Extra style directive (default: use style.ART_DIRECTION_CORE)")
@click.option("--seed", type=int, default=None,
              help="Seed for reproducible cover regen")
def series_cover(
    hero_visual: str | None,
    tagline: str | None,
    style: str | None,
    seed: int | None,
) -> None:
    """Generate a 1200×630 series poster cover (og:image for X / Discord cards)."""
    from hermes_comic.cover import (
        compose_cover,
        extract_hero_visual,
        extract_tagline,
        generate_cover_art,
    )

    if not canon.canon_is_initialized():
        raise click.ClickException("canon empty — run `comic series new` first")

    cfiles = canon.read_all_canon()
    ws = canon.get_workspace()
    series_title = ws.name.replace("-", " ").title()

    hero_visual = hero_visual or extract_hero_visual(cfiles["character-bible"])
    tagline = tagline if tagline is not None else extract_tagline(cfiles["world-bible"])

    click.echo(f"[cover] series:      {series_title}")
    click.echo(f"[cover] hero visual: {(hero_visual[:120] + '…') if len(hero_visual) > 120 else hero_visual or '(none extracted)'}")
    click.echo(f"[cover] tagline:     {tagline[:120] if tagline else '(none)'}")
    click.echo("[cover] generating art via fal.ai flux-lora (1200×640)...")

    art = generate_cover_art(
        series_title=series_title,
        hero_visual=hero_visual,
        style_override=style or "",
        seed=seed,
    )
    click.echo(f"  art bytes: {len(art):,}")

    click.echo("[cover] compositing title + tagline + gradient...")
    final = compose_cover(art, series_title, tagline or "")

    out = ws / "cover.jpg"
    out.write_bytes(final)
    click.echo(f"[cover] saved {out}")
    click.echo(f"  size:      {len(final) / 1000:.1f} KB")
    click.echo(f"  dimension: 1200×630 (Twitter card ready)")


@series_grp.command("publish")
@click.option("--tagline", default="", help="Tagline shown on the published page + Twitter card")
@click.option("--domain", default=None,
              help="Custom surge.sh subdomain (default: hermes-comic-<slug>.surge.sh)")
@click.option("--provider",
              type=click.Choice(["both", "cloudflare", "surge"], case_sensitive=False),
              default="both", show_default=True,
              help="Where to deploy. `both` = CF primary + Surge backup (recommended)")
@click.option("--author-handle", default="Knkchn0",
              help="Your X/Twitter handle without @ (used in share button tweet)")
@click.option("--hashtag", default="HermesComic",
              help="Hashtag used in the share button tweet (without #)")
@click.option("--no-deploy", is_flag=True,
              help="Only build bundle, skip deploy (useful for preview)")
def series_publish(
    tagline: str,
    domain: str | None,
    provider: str,
    author_handle: str,
    hashtag: str,
    no_deploy: bool,
) -> None:
    """Build static webtoon site + deploy it publicly.

    Deploys to Cloudflare Pages (primary, 99.99% SLA) and/or surge.sh (fallback).
    The published page includes a share-on-X button pre-filled with a tweet
    that tags @NousResearch, @Teknium, @Kimi_Moonshot, and your handle.
    """
    from hermes_comic.publish import build_bundle, deploy_cloudflare, deploy_surge

    slug = canon.get_workspace().name
    cf_project = f"hermes-comic-{slug}".lower().replace("_", "-")[:58]
    # Cloudflare URL is predictable; use it as share-button anchor if CF deploy planned
    cf_url = f"https://{cf_project}.pages.dev"
    surge_domain = domain if domain else f"hermes-comic-{slug}"
    if not surge_domain.endswith(".surge.sh"):
        surge_domain += ".surge.sh"
    surge_url = f"https://{surge_domain}"

    # Share button URL points to the PRIMARY deploy target
    if provider in ("both", "cloudflare"):
        public_url = cf_url
    else:
        public_url = surge_url

    click.echo("[publish] building static bundle...")
    try:
        bundle, stats = build_bundle(
            tagline=tagline,
            author_handle=author_handle,
            hashtag=hashtag,
            public_url=public_url,
        )
    except FileNotFoundError as e:
        raise click.ClickException(str(e))
    except ValueError as e:
        raise click.ClickException(str(e))

    click.echo(f"  series:   {stats['series_title']}")
    click.echo(f"  chapters: {stats['chapter_count']}")
    click.echo(f"  bundle:   {stats['bundle']}")
    click.echo(f"  size:     {stats['size_mb']:.1f} MB")
    click.echo(f"  share:    tweet tags @NousResearch @Teknium @Kimi_Moonshot @{author_handle}")

    if no_deploy:
        click.echo("\n[publish] --no-deploy set; bundle ready but not deployed")
        return

    results: dict[str, str | Exception] = {}
    if provider in ("both", "cloudflare"):
        click.echo(f"\n[publish] deploying to Cloudflare Pages ({cf_project})...")
        try:
            results["cloudflare"] = deploy_cloudflare(bundle, project_name=cf_project)
        except Exception as e:
            results["cloudflare"] = e
            click.echo(f"  ⚠ Cloudflare deploy failed: {str(e)[:300]}")
    if provider in ("both", "surge"):
        click.echo(f"\n[publish] deploying to surge.sh ({surge_domain})...")
        try:
            results["surge"] = deploy_surge(bundle, domain=domain)
        except Exception as e:
            results["surge"] = e
            click.echo(f"  ⚠ Surge deploy failed: {str(e)[:300]}")

    ok = {k: v for k, v in results.items() if not isinstance(v, Exception)}
    if not ok:
        raise click.ClickException("All deploy targets failed")

    click.echo(f"\n✅ Published!")
    for target, url in ok.items():
        label = "primary " if target == "cloudflare" else "fallback"
        click.echo(f"   [{label}] {url}")
    click.echo(f"   Size: {stats['size_mb']:.1f} MB, {stats['chapter_count']} chapters")
    click.echo("   Share button on page pre-fills a tweet with @ tags + hashtag\n")


@series_grp.command("export")
@click.option("--output", type=click.Path(path_type=Path), default=None,
              help="Output PNG path (default: <workspace>/series.png)")
def series_export(output: Path | None) -> None:
    """Stitch all rendered chapter.png files into a single series PNG."""
    from hermes_comic.composer import compose_series

    chapters_dir = canon.get_workspace() / "chapters"
    if not chapters_dir.exists():
        raise click.ClickException(f"no chapters directory: {chapters_dir}")

    chapter_pngs: list[Path] = []
    for cd in sorted(chapters_dir.iterdir()):
        if cd.is_dir():
            cp = cd / "chapter.png"
            if cp.exists():
                chapter_pngs.append(cp)

    if not chapter_pngs:
        raise click.ClickException("no chapter.png files found — render chapters first")

    out = output or (canon.get_workspace() / "series.png")
    click.echo(f"[export] stitching {len(chapter_pngs)} chapters → {out}")
    compose_series(chapter_pngs, out)
    click.echo(f"  wrote {out}")


# ─── entry point ──────────────────────────────────────────────────────────


@cli.command("auto")
@click.argument("premise", nargs=-1, required=True)
@click.option("--title", default=None,
              help="Series slug (default: auto-derive from premise)")
@click.option("--chapters", type=int, default=3, show_default=True)
@click.option("--panels", type=int, default=8, show_default=True)
@click.option("--pick", type=int, default=1, show_default=True,
              help="Which proposal to auto-pick (1-3)")
@click.option("--seed", type=int, default=42, show_default=True)
@click.option("--no-publish", is_flag=True, help="Skip Stage 6 publish")
@click.option("--no-cover", is_flag=True, help="Skip cover generation")
def auto(
    premise: tuple[str, ...],
    title: str | None,
    chapters: int,
    panels: int,
    pick: int,
    seed: int,
    no_publish: bool,
    no_cover: bool,
) -> None:
    """One-shot non-interactive full series generation.

    Runs the entire pipeline end-to-end: series propose → new → chapter propose
    → new → render loop → export → cover → publish. Auto-picks alternatives via
    --pick. Skips reference image generation (uses text2image + LoRA only — still
    produces the manhwa look, trades some character consistency for speed).

    Example:
      uv run comic auto "A wandering clockmaker mends time while shadows chase him"
    """
    import json as _json
    import os as _os

    from hermes_comic.composer import compose_chapter, compose_series
    from hermes_comic.cover import (
        compose_cover,
        extract_hero_visual,
        extract_tagline,
        generate_cover_art,
    )
    from hermes_comic.panel_generator import build_jobs, render_all
    from hermes_comic.propose import (
        current_canon_context,
        propose_chapter_beats,
        propose_series_variants,
    )
    from hermes_comic.publish import (
        build_bundle,
        deploy_cloudflare,
        deploy_surge,
    )

    premise_str = " ".join(premise).strip()
    slug = _slug(title or premise_str[:40])

    # Set workspace BEFORE any canon read/write (absolute path throughout)
    workspace = (Path("workspaces") / slug).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    _os.environ["HERMES_COMIC_WORKSPACE"] = str(workspace)

    pick_idx = max(0, min(pick - 1, 2))  # clamp 1-3 → 0-2

    click.echo(f"[auto] slug: {slug}")
    click.echo(f"[auto] workspace: {workspace}")
    click.echo(f"[auto] config: {chapters} chapters × {panels} panels, seed={seed}, pick=[{pick}]")

    # ─── Stage 1: series propose ──────────────────────────────────────────
    click.echo(f"\n[auto] ┌─ STAGE 1 ─ series propose")
    alts = propose_series_variants(premise_str)
    if not alts:
        raise click.ClickException("series propose returned no alternatives")
    chosen = alts[min(pick_idx, len(alts) - 1)]
    click.echo(f"[auto] │  [1] {alts[0].get('title', '?')}")
    if len(alts) > 1:
        click.echo(f"[auto] │  [2] {alts[1].get('title', '?')}")
    if len(alts) > 2:
        click.echo(f"[auto] │  [3] {alts[2].get('title', '?')}")
    click.echo(f"[auto] └─ picked: [{pick}] {chosen.get('title', '?')}")

    # ─── Stage 2: series new ──────────────────────────────────────────────
    click.echo(f"\n[auto] ┌─ STAGE 2 ─ series new (Kimi K2.5)")
    framing_text = chosen.get("framing", premise_str)
    client = KimiClient()
    result = client.complete_json(
        messages=[
            {"role": "system", "content": prompts.SERIES_SYSTEM},
            {"role": "user", "content": prompts.SERIES_USER_TEMPLATE.format(
                premise=framing_text, series_slug=slug,
            )},
        ],
        temperature=0.6,
        max_tokens=10000,
    )
    for jkey, fname in [
        ("world_bible", "world-bible"),
        ("character_bible", "character-bible"),
        ("style_card", "style-card"),
        ("continuity_log", "continuity-log"),
    ]:
        if jkey not in result:
            raise click.ClickException(f"Kimi missing '{jkey}'")
        canon.write_canon(fname, result[jkey])
    click.echo(f"[auto] └─ canon: 4 files written")

    # ─── Stage 3/4: chapter loop ──────────────────────────────────────────
    for ch in range(1, chapters + 1):
        click.echo(f"\n[auto] ┌─ STAGE 3 ─ chapter {ch} propose")
        canon_ctx = current_canon_context(max_chars=3500)
        beat_alts = propose_chapter_beats(
            idea=f"Chapter {ch} — advance the series arc with fresh dramatic direction",
            chapter_num=ch,
            canon_context=canon_ctx,
        )
        if not beat_alts:
            click.echo(f"[auto] │  propose returned empty; using premise as beat")
            beat_text = f"Chapter {ch} continues the story"
            beat_title = f"Chapter {ch}"
        else:
            beat_choice = beat_alts[min(pick_idx, len(beat_alts) - 1)]
            beat_text = beat_choice.get("beat", "")
            beat_title = beat_choice.get("title", f"Chapter {ch}")
        click.echo(f"[auto] └─ picked: {beat_title}")

        click.echo(f"\n[auto] ┌─ STAGE 4 ─ chapter {ch} new ({panels} panels)")
        canon.snapshot_before(ch)
        cfiles = canon.read_all_canon()
        chapter_result = client.complete_json(
            messages=[
                {"role": "system", "content": prompts.CHAPTER_SYSTEM},
                {"role": "user", "content": prompts.CHAPTER_USER_TEMPLATE.format(
                    chapter_num=ch,
                    beat=beat_text,
                    target_panels=panels,
                    world_bible=cfiles["world-bible"],
                    character_bible=cfiles["character-bible"],
                    style_card=cfiles["style-card"],
                    continuity_log=cfiles["continuity-log"],
                )},
            ],
            temperature=0.7,
            max_tokens=12000,
        )
        cdir = canon.chapter_dir(ch)
        cdir.mkdir(parents=True, exist_ok=True)
        (cdir / "spec.json").write_text(
            _json.dumps(chapter_result, indent=2, ensure_ascii=False), encoding="utf-8",
        )
        if chapter_result.get("continuity_updates"):
            existing = canon.read_canon("continuity-log")
            canon.write_canon(
                "continuity-log",
                existing.rstrip() + "\n\n" + chapter_result["continuity_updates"].strip() + "\n",
            )
        click.echo(f"[auto] │  title: {chapter_result.get('title', '?')}")
        click.echo(f"[auto] │  panels: {len(chapter_result.get('panels', []))}")

        click.echo(f"\n[auto] ┌─ STAGE 4 ─ chapter {ch} render (no refs, text2image + LoRA)")
        jobs = build_jobs(ch)
        results = render_all(
            jobs, concurrency=5, seed=seed + ch * 1000, no_references=True,
        )
        ok_count = sum(1 for _, ok, _ in results if ok)
        if ok_count < len(results):
            click.echo(f"[auto] │  ⚠ {len(results) - ok_count} panels failed")

        dialogues_by_n = {p["n"]: (p.get("dialogue") or []) for p in chapter_result["panels"]}
        panel_paths = [j.out_path for j in jobs]
        dialogues = [dialogues_by_n.get(j.n, []) for j in jobs]
        compose_chapter(panel_paths, dialogues, cdir / "chapter.png")
        click.echo(f"[auto] └─ chapter {ch} saved: {(cdir / 'chapter.png')}")

    # ─── Stage 5: export ──────────────────────────────────────────────────
    click.echo(f"\n[auto] ┌─ STAGE 5 ─ series export")
    chapter_pngs = [
        workspace / "chapters" / f"{n:02d}" / "chapter.png"
        for n in range(1, chapters + 1)
    ]
    chapter_pngs = [p for p in chapter_pngs if p.exists()]
    compose_series(chapter_pngs, workspace / "series.png")
    click.echo(f"[auto] └─ series.png: {(workspace / 'series.png')}")

    # ─── Stage 5b: cover ──────────────────────────────────────────────────
    cfiles = canon.read_all_canon()
    tagline_auto = extract_tagline(cfiles["world-bible"])
    if not no_cover:
        click.echo(f"\n[auto] ┌─ STAGE 5b ─ cover generation")
        hero = extract_hero_visual(cfiles["character-bible"])
        title_display = slug.replace("-", " ").title()
        art = generate_cover_art(
            series_title=title_display, hero_visual=hero, seed=seed,
        )
        final = compose_cover(art, title_display, tagline_auto)
        (workspace / "cover.jpg").write_bytes(final)
        click.echo(f"[auto] └─ cover.jpg saved ({len(final) / 1000:.1f} KB)")

    # ─── Stage 6: publish ─────────────────────────────────────────────────
    if not no_publish:
        click.echo(f"\n[auto] ┌─ STAGE 6 ─ publish (Cloudflare + Surge)")
        cf_project = f"hermes-comic-{slug}".lower().replace("_", "-")[:58]
        bundle, stats = build_bundle(
            workspace=workspace,
            tagline=tagline_auto,
            author_handle="Knkchn0",
            hashtag="HermesComic",
            public_url=f"https://{cf_project}.pages.dev",
        )
        try:
            cf_url = deploy_cloudflare(bundle, project_name=cf_project)
            click.echo(f"[auto] │  ✅ CF:    {cf_url}")
        except Exception as e:
            click.echo(f"[auto] │  ⚠ CF fail: {str(e)[:200]}")
        try:
            surge_url = deploy_surge(bundle, domain=f"hermes-comic-{slug}")
            click.echo(f"[auto] │  ✅ Surge: {surge_url}")
        except Exception as e:
            click.echo(f"[auto] │  ⚠ Surge fail: {str(e)[:200]}")
        click.echo(f"[auto] └─ share button tweet tags @NousResearch @Teknium @Kimi_Moonshot @Knkchn0")

    click.echo(f"\n[auto] 🎬 COMPLETE — {chapters} chapters, slug={slug}")


def main() -> None:
    cli(obj={})


if __name__ == "__main__":
    main()
