"""Full i18n repair: upstream catalog merge, zh_TW, glossary, sync po/mo, audit."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(__file__).resolve().parent
I18N_WT = Path("F:/Cursor/bm-ok-nte-i18n")
LOCALES = ["zh_TW", "zh_CN", "en_US", "ja_JP", "ko_KR", "es_ES", "pt_BR"]


def run(script: Path) -> None:
    print(f"\n>>> {script.name}")
    subprocess.run([sys.executable, str(script)], cwd=ROOT, check=True)


def copy_po_mo_to_worktree() -> None:
    import shutil

    for loc in LOCALES:
        for ext in ("po", "mo"):
            src = ROOT / "i18n" / loc / "LC_MESSAGES" / f"ok.{ext}"
            dest = I18N_WT / "i18n" / loc / "LC_MESSAGES" / f"ok.{ext}"
            shutil.copy2(src, dest)
    print(f"\n>>> copied 7 locales po+mo -> {I18N_WT}")


def main() -> int:
    run(TOOLS / "merge_upstream_i18n.py")
    run(TOOLS / "fix_zh_tw_catalog.py")
    run(TOOLS / "apply_game_glossary.py")
    copy_po_mo_to_worktree()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
