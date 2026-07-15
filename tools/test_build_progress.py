"""Smoke tests for build_progress.run_with_progress (run: py -3.12 tools/test_build_progress.py)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_progress import BuildProgress, TAURI_BUNDLE_HINTS, run_with_progress


def main() -> None:
    py = sys.executable
    p = BuildProgress("win10")

    with p.step():
        # fast cmd, no time_tick — must not raise on ticker.join
        run_with_progress(p, [py, "-c", "pass"], label="fast")

    with p.step():
        run_with_progress(
            p,
            [py, "-c", "import time; time.sleep(2); print('Running makensis test')"],
            label="slow",
            hints=TAURI_BUNDLE_HINTS,
            time_tick=True,
        )

    p.finish("[test_build_progress] OK")


if __name__ == "__main__":
    main()
