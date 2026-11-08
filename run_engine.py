#!/usr/bin/env python3
"""
run_engine.py - Master Orchestrator for the Lead Engine Pipeline

Pipeline:
    [1/2] migrate_v1_to_v2.py  ->  v2_ready_leads.csv
    [2/2] lead_scorer.py       ->  v2_prioritized_leads.csv

Design notes:
    * Each stage runs as an isolated subprocess (separate interpreter, separate failure domain).
    * Fail-fast: if a stage exits non-zero or doesn't produce its expected artifact,
      downstream stages are NOT executed and the orchestrator exits with a non-zero code.
    * Uses sys.executable so child scripts run in the same virtualenv as the orchestrator.
    * Resolves paths relative to this file, so it works from any working directory.

Usage:
    python run_engine.py
"""

import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Stage:
    label: str            # Human-friendly name shown in the terminal
    icon: str             # Emoji for the stage
    script: str           # Script filename (relative to BASE_DIR)
    output_file: str      # Artifact this stage must produce


STAGES = [
    Stage("Running Data Cleanse...", "🧹", "migrate_v1_to_v2.py", "v2_ready_leads.csv"),
    Stage("Running ICP Scoring...", "🎯", "lead_scorer.py", "v2_prioritized_leads.csv"),
]

WIDTH = 64

# Make sure emojis / box characters don't crash on Windows consoles.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Pretty-printing helpers
# ---------------------------------------------------------------------------
def banner(title: str) -> None:
    print("╔" + "═" * (WIDTH - 2) + "╗")
    print("║" + title.center(WIDTH - 2) + "║")
    print("╚" + "═" * (WIDTH - 2) + "╝")


def divider(char: str = "─") -> None:
    print(char * WIDTH)


def fmt_time(seconds: float) -> str:
    return f"{seconds:.2f}s"


def progress_bar(done: int, total: int, width: int = 30) -> str:
    filled = int(width * done / total)
    pct = int(100 * done / total)
    return f"[{'█' * filled}{'░' * (width - filled)}] {pct}%"


def file_size_kb(path: Path) -> str:
    return f"{path.stat().st_size / 1024:.1f} KB"


# ---------------------------------------------------------------------------
# Core execution
# ---------------------------------------------------------------------------
def run_stage(index: int, total: int, stage: Stage) -> Optional[float]:
    """
    Run one pipeline stage. Returns elapsed seconds on success, None on failure.
    """
    script_path = BASE_DIR / stage.script
    output_path = BASE_DIR / stage.output_file

    print()
    print(f"{stage.icon}  [{index}/{total}] {stage.label}")
    print(f"    ↳ script : {stage.script}")
    print(f"    ↳ output : {stage.output_file}")
    divider()

    # Pre-flight check: script exists
    if not script_path.is_file():
        print(f"❌  Script not found: {script_path}")
        return None

    # Force UTF-8 in the child process so its prints never break on Windows.
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"}

    start = time.perf_counter()
    try:
        # Stream child output live (no capture) so the user sees progress in real time.
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=BASE_DIR,
            env=env,
            check=False,
        )
    except OSError as exc:
        print(f"❌  Could not launch {stage.script}: {exc}")
        return None
    elapsed = time.perf_counter() - start

    divider()

    # Exit-code gate
    if result.returncode != 0:
        print(f"❌  {stage.script} failed with exit code {result.returncode} "
              f"after {fmt_time(elapsed)}")
        return None

    # Artifact gate: a zero exit code isn't enough - the expected file must exist.
    if not output_path.is_file():
        print(f"❌  {stage.script} exited cleanly but '{stage.output_file}' was not created.")
        return None

    print(f"✅  Stage {index}/{total} complete in {fmt_time(elapsed)} "
          f"({stage.output_file}, {file_size_kb(output_path)})")
    return elapsed


def main() -> int:
    total = len(STAGES)
    pipeline_start = time.perf_counter()

    print()
    banner("🚀  LEAD ENGINE  ·  PIPELINE STATUS  🚀")
    print(f"  Stages     : {total}")
    print(f"  Interpreter: {sys.executable}")
    print(f"  Workdir    : {BASE_DIR}")

    timings = []

    for i, stage in enumerate(STAGES, start=1):
        elapsed = run_stage(i, total, stage)

        if elapsed is None:
            # Fail fast - never run downstream stages on bad/missing upstream data.
            print()
            banner("💥  PIPELINE ABORTED  💥")
            print(f"  Failed at stage {i}/{total}: {stage.script}")
            skipped = [s.script for s in STAGES[i:]]
            if skipped:
                print(f"  Skipped    : {', '.join(skipped)}")
            print(f"  Progress   : {progress_bar(i - 1, total)}")
            print()
            return 1

        timings.append((stage, elapsed))
        print(f"    {progress_bar(i, total)}")

    total_elapsed = time.perf_counter() - pipeline_start

    # Final summary
    print()
    banner("🎉  PIPELINE COMPLETE!  🎉")
    for n, (stage, elapsed) in enumerate(timings, start=1):
        print(f"  ✔ [{n}/{total}] {stage.script:<24} {fmt_time(elapsed):>8}")
    divider()
    print(f"  ⏱  Total runtime : {fmt_time(total_elapsed)}")
    print(f"  📦 Final output  : {STAGES[-1].output_file}")
    print()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⚠️  Pipeline interrupted by user.")
        sys.exit(130)
