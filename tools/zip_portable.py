"""Archive dist_portable/ into dist_zip/ with stage progress."""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_progress import BuildProgress  # noqa: E402

SRC_DIR = ROOT / "dist_portable"
ZIP_DIR = ROOT / "dist_zip"
VER_SRC = ROOT / "src" / "config.py"


def read_version() -> str:
    text = VER_SRC.read_text(encoding="utf-8")
    match = re.search(r'version\s*=\s*"([^"]+)"', text)
    if not match:
        raise SystemExit(f"could not read version from {VER_SRC}")
    return match.group(1)


def collect_files(src: Path) -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    for path in sorted(src.rglob("*")):
        if path.is_file():
            files.append((path, path.relative_to(src).as_posix()))
    return files


def main() -> None:
    if not SRC_DIR.is_dir():
        raise SystemExit(f"missing {SRC_DIR}")

    version = read_version()
    ZIP_DIR.mkdir(parents=True, exist_ok=True)
    zip_name = f"bm-ok-nte-win32-global-portable-{version}.zip"
    zip_path = ZIP_DIR / zip_name
    if zip_path.exists():
        zip_path.unlink()

    files = collect_files(SRC_DIR)
    total = max(len(files), 1)
    progress = BuildProgress("win10_zip", tag="build_win10_zip")
    with progress.step():
        with zipfile.ZipFile(
            zip_path,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=1,
        ) as zf:
            for idx, (path, arcname) in enumerate(files, 1):
                zf.write(path, arcname)
                if idx == 1 or idx == total or idx % 200 == 0:
                    progress.set_in_stage(int(idx * 100 / total), detail=f"({idx}/{total})")

    try:
        shown = zip_path.relative_to(ROOT)
    except ValueError:
        shown = zip_path
    progress.finish(f"[build_win10_zip] OK: {shown}")


if __name__ == "__main__":
    main()
