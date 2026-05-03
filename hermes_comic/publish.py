"""Publish a rendered comic series as a public webtoon URL.

Builds a mobile-first vertical-scroll static site at
`<workspace>/_publish/index.html` with all chapters embedded,
Twitter / Open Graph share cards, and optional surge.sh deploy.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from PIL import Image

from hermes_comic import canon

JPEG_QUALITY = 85  # visually near-identical to PNG for painted panels, ~75% smaller

# X logo SVG (2023+ rebrand, black-mode friendly)
X_ICON_SVG = (
    '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true">'
    '<path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>'
    '</svg>'
)


def _share_tweet_text(
    title: str,
    tagline: str,
    author_handle: str,
    hashtag: str,
) -> str:
    """Compose the pre-filled tweet body (URL is appended separately by Twitter Intent)."""
    lines = [f"📖 {title}"]
    if tagline:
        lines.append(tagline)
    lines.extend(
        [
            "",
            f"An AI webtoon by @{author_handle}",
            "Built with @NousResearch Hermes Agent + @Kimi_Moonshot K2.5",
            "cc @Teknium",
            "",
            f"#{hashtag}",
        ]
    )
    return "\n".join(lines)


def _share_url(tweet_text: str, share_url: str) -> str:
    """Twitter Web Intent URL — opens a pre-filled compose window on X."""
    return (
        "https://twitter.com/intent/tweet"
        f"?text={quote(tweet_text)}"
        f"&url={quote(share_url)}"
    )

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0a0a0f">
<title>{title}</title>

<meta name="description" content="{tagline}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{tagline}">
<meta name="twitter:image" content="{cover}">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{tagline}">
<meta property="og:image" content="{cover}">

<link rel="preload" as="image" href="{cover}" fetchpriority="high">
<style>
:root {{
  --bg: #0a0a0f;
  --fg: #f2f2f7;
  --muted: #8a8a95;
  --accent: #d946ef;
  --line: #1f1f28;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ background: var(--bg); color: var(--fg); }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Inter', system-ui, 'Segoe UI', Roboto, sans-serif;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}}
.container {{ max-width: 820px; margin: 0 auto; }}
header {{ text-align: center; padding: 4rem 1.25rem 3rem; }}
h1 {{
  font-size: clamp(1.85rem, 5.5vw, 3rem);
  letter-spacing: -0.02em;
  margin-bottom: 0.5rem;
  font-weight: 800;
  line-height: 1.1;
}}
.tagline {{
  color: var(--muted);
  font-style: italic;
  font-size: clamp(0.95rem, 2.5vw, 1.125rem);
  max-width: 48ch;
  margin: 0.5rem auto 0;
}}
.meta {{
  font-size: 0.75rem;
  color: var(--muted);
  margin-top: 1.25rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
}}
.chapter-header {{
  text-align: center;
  padding: 3rem 1.25rem 1.5rem;
  border-top: 1px solid var(--line);
}}
.chapter-number {{
  font-size: 0.75rem;
  color: var(--accent);
  letter-spacing: 0.3em;
  text-transform: uppercase;
  font-weight: 700;
}}
.chapter-title {{
  font-size: clamp(1.25rem, 3.5vw, 1.75rem);
  margin-top: 0.6rem;
  font-weight: 700;
  letter-spacing: -0.01em;
}}
.chapter-summary {{
  color: var(--muted);
  font-size: 0.95rem;
  margin-top: 0.75rem;
  max-width: 56ch;
  margin-left: auto;
  margin-right: auto;
}}
.chapter img {{
  width: 100%;
  height: auto;
  display: block;
}}
footer {{
  text-align: center;
  padding: 4rem 1.25rem 4rem;
  color: var(--muted);
  font-size: 0.875rem;
  border-top: 1px solid var(--line);
}}
footer a {{
  color: var(--accent);
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: border-color 120ms;
}}
footer a:hover {{ border-color: var(--accent); }}
.credit {{ margin-top: 1rem; font-size: 0.75rem; opacity: 0.7; }}

/* Share buttons */
.share-top {{
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 100;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.55rem 1.1rem;
  background: rgba(0, 0, 0, 0.82);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 999px;
  font-weight: 600;
  font-size: 0.875rem;
  text-decoration: none;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  transition: transform 150ms, background 150ms, box-shadow 150ms;
}}
.share-top:hover {{
  background: rgba(20, 20, 20, 0.95);
  transform: translateY(-1px);
  box-shadow: 0 8px 24px -8px rgba(217, 70, 239, 0.4);
}}

.share-cta {{
  text-align: center;
  padding: 4rem 1.25rem;
  border-top: 1px solid var(--line);
}}
.share-cta-title {{
  font-size: clamp(1.125rem, 3vw, 1.5rem);
  font-weight: 700;
  margin-bottom: 0.5rem;
  color: var(--fg);
}}
.share-cta-sub {{
  color: var(--muted);
  font-size: 0.95rem;
  margin-bottom: 2rem;
  max-width: 42ch;
  margin-left: auto;
  margin-right: auto;
}}
.share-btn {{
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.95rem 1.9rem;
  background: #000;
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 999px;
  font-weight: 700;
  font-size: 1rem;
  text-decoration: none;
  transition: transform 150ms, box-shadow 150ms;
}}
.share-btn:hover {{
  transform: translateY(-2px);
  box-shadow: 0 14px 40px -12px rgba(217, 70, 239, 0.45);
}}
@media (prefers-reduced-motion: no-preference) {{
  .chapter img {{
    opacity: 0;
    animation: fadeIn 600ms ease-out forwards;
  }}
}}
@keyframes fadeIn {{ to {{ opacity: 1; }} }}
</style>
</head>
<body>
<a class="share-top" href="{share_url}" target="_blank" rel="noopener" aria-label="Share on X">
{x_icon}
<span>Share</span>
</a>
<div class="container">
<header>
<h1>{title}</h1>
<p class="tagline">{tagline}</p>
<p class="meta">{chapter_count} CHAPTERS</p>
</header>
{chapters}
<section class="share-cta">
<div class="share-cta-title">Enjoyed {title}?</div>
<p class="share-cta-sub">Share this AI-generated webtoon with your friends and help the creator get seen.</p>
<a class="share-btn" href="{share_url}" target="_blank" rel="noopener">
{x_icon}
<span>Share on X</span>
</a>
</section>
<footer>
<p>End of <strong>{title}</strong></p>
<p class="credit">
Built with <a href="https://github.com/NousResearch/hermes-agent" target="_blank" rel="noopener">Hermes Agent</a>
· <a href="https://platform.moonshot.ai/" target="_blank" rel="noopener">Kimi K2.5</a>
· <a href="https://fal.ai/" target="_blank" rel="noopener">Flux LoRA</a>
</p>
</footer>
</div>
</body>
</html>
"""

CHAPTER_HTML = """<section class="chapter">
<div class="chapter-header">
<div class="chapter-number">Chapter {num:02d}</div>
<h2 class="chapter-title">{title}</h2>
<p class="chapter-summary">{summary}</p>
</div>
<img src="{img}" alt="Chapter {num}: {title}" loading="lazy" decoding="async">
</section>
"""


def _escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_bundle(
    workspace: Optional[Path] = None,
    tagline: str = "",
    author_handle: str = "Knkchn0",
    hashtag: str = "HermesComic",
    public_url: Optional[str] = None,
) -> tuple[Path, dict]:
    """Generate static HTML bundle. Returns (bundle_path, stats dict).

    Share button pre-fills a tweet tagging @{author_handle} + @NousResearch
    + @Kimi_Moonshot + @Teknium with hashtag #{hashtag}.
    """
    ws = Path(workspace) if workspace else canon.get_workspace()
    series_slug = ws.name
    series_title = series_slug.replace("-", " ").title()

    chapters_dir = ws / "chapters"
    if not chapters_dir.exists():
        raise FileNotFoundError(f"no chapters directory at {chapters_dir}")

    bundle = ws / "_publish"
    if bundle.exists():
        shutil.rmtree(bundle)
    bundle.mkdir(parents=True)

    chapter_fragments: list[str] = []
    cover_image: str = ""

    # Prefer a dedicated series cover if the user generated one
    for cover_src_name in ("cover.jpg", "cover.jpeg", "cover.png"):
        cover_src = ws / cover_src_name
        if cover_src.exists():
            dest = bundle / "cover.jpg"
            # Always output JPEG for card compatibility
            if cover_src.suffix.lower() == ".png":
                with Image.open(cover_src) as img:
                    img.convert("RGB").save(dest, "JPEG", quality=90, optimize=True)
            else:
                shutil.copy2(cover_src, dest)
            cover_image = "cover.jpg"
            break

    for cd in sorted(chapters_dir.iterdir()):
        if not cd.is_dir():
            continue
        try:
            num = int(cd.name)
        except ValueError:
            continue
        chapter_png = cd / "chapter.png"
        if not chapter_png.exists():
            continue

        # Convert PNG → JPEG (quality 85) — ~75% smaller, visually near-identical
        dest_name = f"chapter-{num:02d}.jpg"
        with Image.open(chapter_png) as img:
            rgb = img.convert("RGB")
            rgb.save(
                bundle / dest_name,
                "JPEG",
                quality=JPEG_QUALITY,
                optimize=True,
                progressive=True,
            )
        if not cover_image:
            cover_image = dest_name

        title = f"Chapter {num}"
        summary = ""
        spec_path = cd / "spec.json"
        if spec_path.exists():
            try:
                spec = json.loads(spec_path.read_text(encoding="utf-8"))
                title = spec.get("title") or title
                summary = spec.get("summary") or ""
            except Exception:
                pass

        chapter_fragments.append(
            CHAPTER_HTML.format(
                num=num,
                title=_escape(title),
                summary=_escape(summary),
                img=dest_name,
            )
        )

    if not chapter_fragments:
        raise ValueError("no rendered chapter.png files found")

    if not tagline:
        # derive from world-bible first paragraph if present
        world = canon.read_canon("world-bible")
        for line in world.split("\n"):
            line = line.strip()
            if line and not line.startswith(("#", "-", "---", "series:", "kind:", "version:")):
                tagline = line[:140]
                break
        if not tagline:
            tagline = f"A {len(chapter_fragments)}-chapter webtoon series"

    # Build the Twitter share URL. public_url is where the page will live
    # (we don't know the real surge.sh URL yet — callers pass it in, or we
    # fall back to a guess based on slug).
    effective_url = public_url or f"https://hermes-comic-{series_slug}.surge.sh"
    tweet_text = _share_tweet_text(
        series_title, tagline, author_handle=author_handle, hashtag=hashtag
    )
    share_url = _share_url(tweet_text, effective_url)

    index_html = INDEX_HTML.format(
        title=_escape(series_title),
        tagline=_escape(tagline),
        cover=cover_image,
        chapter_count=len(chapter_fragments),
        chapters="".join(chapter_fragments),
        share_url=_escape(share_url),
        x_icon=X_ICON_SVG,
    )
    (bundle / "index.html").write_text(index_html, encoding="utf-8")

    total_size = sum(p.stat().st_size for p in bundle.rglob("*") if p.is_file())
    stats = {
        "bundle": str(bundle),
        "chapter_count": len(chapter_fragments),
        "size_bytes": total_size,
        "size_mb": total_size / 1_000_000,
        "cover_image": cover_image,
        "series_title": series_title,
    }
    return bundle, stats


def deploy_cloudflare(
    bundle_dir: Path,
    project_name: Optional[str] = None,
) -> str:
    """Deploy bundle to Cloudflare Pages via wrangler CLI. Returns public URL.

    Requires env vars:
      CLOUDFLARE_ACCOUNT_ID
      CLOUDFLARE_API_TOKEN  (scope: Pages → Edit)

    Installs wrangler on first run via `npx --yes wrangler` (no global install).
    """
    import os

    if not os.environ.get("CLOUDFLARE_API_TOKEN"):
        raise RuntimeError("CLOUDFLARE_API_TOKEN missing in env")
    if not os.environ.get("CLOUDFLARE_ACCOUNT_ID"):
        raise RuntimeError("CLOUDFLARE_ACCOUNT_ID missing in env")

    if project_name is None:
        project_name = f"hermes-comic-{bundle_dir.parent.name}"

    # Project names: lowercase, alphanumeric + hyphens, start with letter, ≤58 chars
    project_name = project_name.lower().replace("_", "-")[:58]

    # Strip CNAME from bundle (surge-specific, wrangler ignores but it's cleaner)
    cname = bundle_dir / "CNAME"
    if cname.exists():
        cname.unlink()

    if shutil.which("wrangler") is not None:
        base_cmd = ["wrangler"]
    elif shutil.which("npx") is not None:
        base_cmd = ["npx", "--yes", "wrangler"]
    else:
        raise RuntimeError(
            "Neither `wrangler` nor `npx` is installed.\n"
            "Setup:  sudo apt install -y nodejs npm"
        )

    # Step 1: ensure the Pages project exists (idempotent — ignore "already exists" errors)
    create_cmd = base_cmd + [
        "pages",
        "project",
        "create",
        project_name,
        "--production-branch=main",
    ]
    create_result = subprocess.run(
        create_cmd,
        capture_output=True,
        text=True,
        timeout=120,
        env=os.environ.copy(),
    )
    create_output = (create_result.stdout or "") + (create_result.stderr or "")
    if create_result.returncode != 0 and "already exists" not in create_output.lower():
        # Non-idempotent error — real problem
        if "unauthorized" in create_output.lower() or "authentication" in create_output.lower():
            raise RuntimeError(f"cloudflare auth failed:\n{create_output[-1000:]}")
        # Otherwise log and keep going — project might exist under different pagination
        pass

    # Step 2: deploy
    cmd = base_cmd + [
        "pages",
        "deploy",
        str(bundle_dir),
        f"--project-name={project_name}",
        "--branch=main",
        "--commit-dirty=true",
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=600,
        env=os.environ.copy(),
    )
    output = (result.stdout or "") + "\n" + (result.stderr or "")
    if result.returncode != 0:
        raise RuntimeError(
            f"cloudflare pages deploy failed (exit {result.returncode}):\n{output[-1500:]}"
        )

    # Parse the deployed URL from stdout
    deployed_url = None
    for line in output.splitlines():
        line = line.strip()
        if "https://" in line and ".pages.dev" in line:
            # Extract first https://...pages.dev token from the line
            for tok in line.split():
                if tok.startswith("https://") and ".pages.dev" in tok:
                    deployed_url = tok.rstrip(".,)")
                    break
            if deployed_url:
                break

    # Fallback to the canonical project URL (always works once the project exists)
    return deployed_url or f"https://{project_name}.pages.dev"


def deploy_surge(bundle_dir: Path, domain: Optional[str] = None) -> str:
    """Deploy bundle via `surge` CLI (or `npx surge` fallback). Returns public URL.

    Non-interactive deploys need these env vars (put in .env):
      SURGE_LOGIN  = your surge account email
      SURGE_TOKEN  = token from `surge token`

    One-time setup on this machine:
      npx surge login           # creates free account, asks for email + password
      npx surge token           # prints token → copy to SURGE_TOKEN in .env
    """
    import os

    if domain is None:
        slug = bundle_dir.parent.name
        domain = f"hermes-comic-{slug}.surge.sh"
    elif not domain.endswith(".surge.sh"):
        domain = f"{domain}.surge.sh"

    # CNAME makes surge skip the domain prompt even if surge itself is ready
    (bundle_dir / "CNAME").write_text(domain + "\n", encoding="utf-8")

    # Prefer installed surge; fall back to npx
    if shutil.which("surge") is not None:
        cmd = ["surge", str(bundle_dir), domain]
    elif shutil.which("npx") is not None:
        cmd = ["npx", "--yes", "surge", str(bundle_dir), domain]
    else:
        raise RuntimeError(
            "Neither `surge` nor `npx` is installed.\n"
            "Setup:\n"
            "  sudo apt install -y nodejs npm     # if npm missing\n"
            "  npm install -g surge               # global surge\n"
            "  surge login                        # free account\n"
            "  surge token                        # copy to SURGE_TOKEN in .env\n"
        )

    env = os.environ.copy()
    # Keep TERM so surge detects non-TTY
    env.setdefault("SURGE_LOGIN", os.environ.get("SURGE_LOGIN", ""))
    env.setdefault("SURGE_TOKEN", os.environ.get("SURGE_TOKEN", ""))

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=600,
        env=env,
        input="",  # force non-interactive
    )
    output = (result.stdout or "") + "\n" + (result.stderr or "")
    if result.returncode != 0:
        hint = ""
        if "surge: login" in output.lower() or "no token" in output.lower():
            hint = (
                "\n\nSurge needs authentication. Run once:\n"
                "  npx surge login    # creates account\n"
                "  npx surge token    # copy token to SURGE_TOKEN in .env\n"
                "  add SURGE_LOGIN=<your-email> to .env too"
            )
        raise RuntimeError(f"surge deploy failed (exit {result.returncode}):\n{output}{hint}")
    return f"https://{domain}"
