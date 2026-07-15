"""Merge upstream/main ok.po translations into bm fork catalog and sync po/mo."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ["zh_TW", "zh_CN", "en_US", "ja_JP", "ko_KR", "es_ES", "pt_BR"]
CATALOG_PATH = ROOT / "tools" / "i18n_catalog.json"
UPSTREAM_REF = "upstream/main"


def _load_git_po(rev: str, locale: str) -> "polib.POFile":
    import polib

    raw = subprocess.check_output(
        ["git", "show", f"{rev}:i18n/{locale}/LC_MESSAGES/ok.po"],
        cwd=ROOT,
    )
    with tempfile.NamedTemporaryFile(suffix=".po", delete=False) as tmp:
        tmp.write(raw)
        path = tmp.name
    return polib.pofile(path)


def merge_upstream_into_catalog() -> tuple[int, int]:
    catalog: dict[str, dict[str, str]] = {}
    if CATALOG_PATH.is_file():
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))

    before = len(catalog)
    added = 0
    updated = 0
    for locale in LOCALES:
        po = _load_git_po(UPSTREAM_REF, locale)
        for entry in po:
            if entry.obsolete or not entry.msgid:
                continue
            msgstr = entry.msgstr if entry.msgstr else entry.msgid
            is_new = entry.msgid not in catalog
            bucket = catalog.setdefault(entry.msgid, {})
            if is_new:
                added += 1
            elif locale not in bucket or bucket[locale] != msgstr:
                updated += 1
            bucket[locale] = msgstr

    CATALOG_PATH.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"catalog: {before} -> {len(catalog)} msgids "
        f"(+{added} new, ~{updated} locale updates from {UPSTREAM_REF})"
    )
    return added, updated


def main() -> int:
    subprocess.run(["git", "fetch", "upstream"], cwd=ROOT, check=True)
    merge_upstream_into_catalog()
    subprocess.run([sys.executable, str(ROOT / "tools" / "sync_i18n.py")], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "tools" / "compile_mo.py")], cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
