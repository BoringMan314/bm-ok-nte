"""Compile all ok.po files under i18n/ to ok.mo (required at runtime by gettext)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def compile_po_dir(i18n_root: Path) -> int:
    count = 0
    for po_path in sorted(i18n_root.rglob("ok.po")):
        mo_path = po_path.with_suffix(".mo")
        try:
            import polib

            po = polib.pofile(str(po_path))
            po.save_as_mofile(str(mo_path))
        except ImportError:
            import subprocess

            subprocess.run(
                ["msgfmt", "-o", str(mo_path), str(po_path)],
                check=True,
            )
        count += 1
        print(f"compiled {mo_path.relative_to(i18n_root.parent)}")
    return count


def main() -> None:
    i18n_root = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "i18n"
    if not i18n_root.is_dir():
        raise SystemExit(f"missing i18n dir: {i18n_root}")
    n = compile_po_dir(i18n_root)
    print(f"done: {n} ok.mo file(s)")


if __name__ == "__main__":
    main()
