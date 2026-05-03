"""D1/Phase-2.5: Generate character reference candidates with the styled LoRA pipeline.

Uses fal-ai/flux-lora (text2image + manhwa LoRA stack) for consistent webtoon DNA.
Per character, produces N candidates across 3 poses (portrait, full_body, action).

Usage:
  # Default: Neon & Ash characters (Kira + Ghost)
  uv run python scripts/gen_references.py --workspace workspaces/neon-and-ash

  # Or Red vs Blue
  uv run python scripts/gen_references.py --workspace workspaces/red-vs-blue --set red-vs-blue

Cost: 2 chars × 3 poses × N candidates × $0.035/MP
      (3 candidates → 18 images ≈ $0.60 at 1024×1024)
"""
from __future__ import annotations

import argparse
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hermes_comic.flux_client import FluxClient  # noqa: E402
from hermes_comic.style import (  # noqa: E402
    build_prompt,
    get_default_lora_stack,
    image_size_for,
)

# ─── Character sets ───────────────────────────────────────────────────────

NEON_ASH_CHARACTERS = {
    "kira": {
        "base": (
            "Kira, 23-year-old female cyberpunk courier, "
            "short platinum silver undercut hair with a single vivid magenta streak over left eye, "
            "sharp grey determined eyes, angular jawline, "
            "black leather biker jacket with electric purple glowing neon trim along seams and sleeves, "
            "red-tinted mirror visor goggles pushed up on forehead, "
            "cyan-glowing cybernetic left arm with matte black armor plating and bright cyan circuit patterns "
            "running from elbow to knuckles, magenta-laced combat boots"
        ),
        "poses": {
            "portrait": (
                "head and shoulders close-up portrait, neutral intense expression, "
                "three-quarter angle, soft neon rim light from behind, "
                "simple dark atmospheric background with faint magenta and cyan glow"
            ),
            "full_body": (
                "full body standing pose, lean wiry build, hands in jacket pockets, "
                "confident stance, three-quarter view, head to toe visible, "
                "wet neon-reflective street backdrop"
            ),
            "action": (
                "mid-ride action pose leaning forward on antique motorcycle, "
                "speed lines blurring background, rain streaking past, "
                "motorcycle headlight glowing cyan, hair whipping back"
            ),
        },
    },
    "ghost": {
        "base": (
            "Ghost, androgynous young AI entity appearing as a hologram-manifest figure, "
            "late teens in apparent age, slim build, "
            "translucent pale blue body with edges dissolving into floating data particles and static snow, "
            "solid glowing cyan voids where eyes should be with no pupils, "
            "loose flowing white monastic robes, "
            "barefoot never touching surfaces, "
            "faint data particles trailing around hands and feet"
        ),
        "poses": {
            "portrait": (
                "head and shoulders portrait, serene enigmatic expression, "
                "glowing cyan eyes emitting soft light, "
                "holographic interference artifacts near edges of face, "
                "simple dark void background with drifting data particles"
            ),
            "full_body": (
                "full body standing pose floating slightly above ground, "
                "robes flowing despite no wind, arms relaxed at sides, "
                "entire body emanating soft cyan bioluminescence, "
                "head to toe visible"
            ),
            "action": (
                "dynamic pose mid-gesture, one arm outstretched, "
                "data particles streaming outward from fingertips, "
                "multiple afterimages suggesting movement, "
                "holographic glitch effects through body"
            ),
        },
    },
}

RED_BLUE_CHARACTERS = {
    "ignara": {
        "base": (
            "Ignara, 19-year-old Pyraleth princess, "
            "waist-length crimson red hair, amber eyes, "
            "ceremonial royal armor with gold accents and intricate filigree patterns, "
            "golden circlet crown on head, gold wrist gauntlet on right arm, "
            "flowing ash-red cloak"
        ),
        "poses": {
            "portrait": "head and shoulders portrait, regal expression, dramatic warm lighting",
            "full_body": "full body standing pose, three-quarter view, regal stance, full figure visible",
            "action": "mid-flight action pose, red laser glow from eyes, cape billowing, dynamic",
        },
    },
    "theros": {
        "base": (
            "Theros, 22-year-old Azura warrior, "
            "shoulder-length cobalt blue hair, indigo eyes, "
            "cobalt blue battle tunic with silver psi-armor plates on shoulders and chest, "
            "glowing cyan psi-blade held in left hand, silver harmonic circlet on brow"
        ),
        "poses": {
            "portrait": "head and shoulders portrait, calm determined expression, cool lighting",
            "full_body": "full body guard pose, psi-blade held low ready stance, serious",
            "action": "mid-leap with psi-blade raised overhead, tunic and hair flowing, dynamic",
        },
    },
}

ZAMAN_TAMIRCISI_CHARACTERS = {
    "watchmaker": {
        "base": (
            "The Watchmaker, immortal Artisan of the First Dawn, tall emaciated build suggesting infinite fatigue, "
            "bulky armor forged from compressed star-cores fused to frame, platinum hair floating weightlessly, "
            "mohawk of ionized gas, eyes like collapsing stars with gold ring around black void, "
            "four mechanical arms ending in forge-tongs and stellar-needles, "
            "The Celestial Toolkit of seven stellar-forged instruments orbiting his hands emitting faint star-death light"
        ),
        "poses": {
            "portrait": (
                "head and shoulders close-up portrait, intense star-like eyes with gold ring, "
                "four mechanical arms visible behind shoulders, ionized gas mohawk glowing faintly, "
                "dark cosmic void background with distant dying stars"
            ),
            "full_body": (
                "full body standing pose, emaciated frame inside bulky star-core armor, "
                "four mechanical arms arranged defensively, celestial toolkit instruments orbiting hands, "
                "chronocoat fabric displaying swirling moments of history, three-quarter view"
            ),
            "action": (
                "dynamic combat pose wielding stellar-forged tools against Chronophage shadows, "
                " four mechanical arms extended with forge-tongs and needles glowing hot, "
                "star-death light erupting from tools, motion blur, intense action lighting"
            ),
        },
    },
}

TIMELY_REPAIRS_CHARACTERS = {
    "sylvie": {
        "base": (
            "Sylvie Vane, 29-year-old female temporal repairperson, haunted housewife aesthetic, "
            "1960s beehive hairdo lifted an inch off scalp by chronometric static electricity, "
            "chestnut brown hair with pencils and small gear springs stuck within the voluminous style, "
            "heavy-lidded amber eyes with tired but warm expression, cat-eye glasses cracked and taped at corners, "
            "tall lanky build with permanent tired stoop, "
            "pastel floral dress in faded pink and cream under oversized teal mechanic coveralls with grease stains, "
            "cardigan pockets bulging with leaking ballpoint pens that write yesterday's dates, "
            "oversized iron adjustable wrench with notched jaws and sticker residue held loosely, "
            "dented silver thermos of cold coffee clipped to belt"
        ),
        "poses": {
            "portrait": (
                "head and shoulders close-up portrait, exaggerated beehive hair with static lift and pencils visible, "
                "taped cat-eye glasses slightly askew, warm tired amber eyes with heavy lids, "
                "performative suburban smile that doesn't quite reach eyes, "
                "soft domestic background with subtle chronometric glitch artifacts"
            ),
            "full_body": (
                "full body standing pose, three-quarter view, tall lanky frame with characteristic stoop, "
                "beehive hair with static lift and office supplies visible, oversized teal coveralls over floral dress, "
                "wrench held loosely in one hand, thermos clipped to belt, cardigan pockets bulging, "
                "mid-century suburban cul-de-sac background with mint-green lawn"
            ),
            "action": (
                "dynamic action pose swinging oversized wrench at temporal glitch rift, "
                "beehive hair dramatically lifted by static energy, pens and springs flying loose, "
                "expression shifting from pleasant smile to resonant commanding fury, "
                "chronometric static glowing around wrench impact point, motion blur"
            ),
        },
    },
    "petra": {
        "base": (
            "Agent Petra File, 34-year-old female DTI Field Auditor, bureaucratic enforcer, "
            "jet-black hair in severe tight bun with distinctive premature gray streaks at temples, "
            "steel-gray eyes with permanent dark circles and exhausted deadpan expression, "
            "compact efficient build with rigid upright posture, "
            "standard-issue slate-gray suit with exactly three pens in breast pocket, "
            "highlighter-yellow DTI armband on left arm, monochrome gray color scheme with bureaucratic red accents, "
            "indestructible aluminum clipboard holding infinite violation forms, "
            "self-inking rubber stamp that glows crimson when issuing cease-and-desist orders"
        ),
        "poses": {
            "portrait": (
                "head and shoulders close-up portrait, severe tight bun with gray temple streaks prominent, "
                "steel-gray exhausted eyes with dark circles, monotone expression, "
                "three pens visible in suit pocket, highlighter-yellow armband visible, "
                "sterile Brutalist office park background with gray concrete walls"
            ),
            "full_body": (
                "full body standing pose, rigid efficient posture, compact build in tailored slate-gray suit, "
                "three pens exactly in breast pocket, highlighter-yellow armband, "
                "aluminum clipboard held at ready, briefcase at side, "
                "three-quarter view, DTI office void background"
            ),
            "action": (
                "dramatic action pose bringing glowing crimson stamp down onto violation form, "
                "audible impact frame effect suggested, red ink splashing, "
                "expression unchanged monotone but posture slightly deflating with sigh, "
                "paperwork swirling with gravitational mass around her"
            ),
        },
    },
}

CHARACTER_SETS = {
    "neon-and-ash": NEON_ASH_CHARACTERS,
    "red-vs-blue": RED_BLUE_CHARACTERS,
    "zaman-tamircisi": ZAMAN_TAMIRCISI_CHARACTERS,
    "timely-repairs": TIMELY_REPAIRS_CHARACTERS,
}

POSE_TO_FRAMING = {
    "portrait": "close_up",
    "full_body": "full_body",
    "action": "action",
}


@dataclass
class RefJob:
    character: str
    pose: str
    n: int
    description: str
    framing: str
    out_path: Path


def build_jobs(workspace: Path, characters: dict, n_candidates: int) -> list[RefJob]:
    jobs: list[RefJob] = []
    for name, spec in characters.items():
        for pose_name, pose_desc in spec["poses"].items():
            for n in range(1, n_candidates + 1):
                desc = f"{spec['base']}. {pose_desc}"
                out = workspace / "characters" / name / "_candidates" / f"{pose_name}_{n}.png"
                jobs.append(
                    RefJob(
                        character=name,
                        pose=pose_name,
                        n=n,
                        description=desc,
                        framing=POSE_TO_FRAMING[pose_name],
                        out_path=out,
                    )
                )
    return jobs


def _render_one(
    client: FluxClient,
    job: RefJob,
    base_seed: int,
) -> tuple[RefJob, bool, str]:
    if job.out_path.exists() and job.out_path.stat().st_size > 100_000:
        return job, True, f"[skip] exists ({job.out_path.stat().st_size:,})"
    try:
        prompt = build_prompt(job.description, camera_framing=job.framing)
        size = image_size_for(job.framing)
        loras = get_default_lora_stack()
        img = client.render_styled_text2image(
            prompt=prompt,
            loras=loras,
            image_size=size,
            seed=base_seed + hash((job.character, job.pose, job.n)) % 10_000,
            guidance_scale=3.5,
        )
        job.out_path.parent.mkdir(parents=True, exist_ok=True)
        job.out_path.write_bytes(img)
        return job, True, f"saved {len(img):,}"
    except Exception as e:
        return job, False, f"error: {type(e).__name__}: {str(e)[:160]}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--workspace",
        type=Path,
        default=Path("workspaces/neon-and-ash"),
        help="Workspace directory (will create characters/<name>/_candidates/)",
    )
    ap.add_argument(
        "--set",
        choices=list(CHARACTER_SETS.keys()),
        default="neon-and-ash",
        help="Character set to generate",
    )
    ap.add_argument("--candidates", type=int, default=3)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--concurrency", type=int, default=5,
                    help="Parallel workers (5 default; drop to 3 if fal rate-limits)")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    workspace = args.workspace.resolve()
    characters = CHARACTER_SETS[args.set]
    jobs = build_jobs(workspace, characters, args.candidates)
    print(f"[gen] workspace: {workspace}")
    print(f"[gen] set: {args.set}  |  {len(jobs)} candidates  (~${len(jobs) * 0.035:.2f})")

    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TextColumn,
        TimeElapsedColumn,
    )

    client = FluxClient()
    failed: list[tuple[RefJob, str]] = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total} refs"),
        TextColumn("·"),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task(
            f"generating refs ({args.concurrency} parallel)",
            total=len(jobs),
        )
        with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
            futures = {ex.submit(_render_one, client, j, args.seed): j for j in jobs}
            for f in as_completed(futures):
                job, ok, msg = f.result()
                status = "ok" if ok else "fail"
                progress.update(
                    task,
                    advance=1,
                    description=f"{job.character}/{job.pose}#{job.n} {status}",
                )
                if not ok:
                    failed.append((job, msg))

    if failed:
        print(f"\n[WARN] {len(failed)} failures")
        return 1

    print(f"\n[done] candidates at {workspace}/characters/<name>/_candidates/")
    print("Next: review in Windows Explorer, then pick best per pose:")
    print("  bash scripts/pick_ref.sh <character> <pose> <N>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
