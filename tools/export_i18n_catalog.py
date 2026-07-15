"""Export all ok.po msgids into tools/i18n_catalog.json (232 entries × 7 locales)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ["zh_TW", "zh_CN", "en_US", "ja_JP", "ko_KR", "es_ES", "pt_BR"]
OUT = ROOT / "tools" / "i18n_catalog.json"


def build_catalog() -> dict[str, dict[str, str]]:
    import polib

    catalog: dict[str, dict[str, str]] = {}
    for locale in LOCALES:
        po_path = ROOT / "i18n" / locale / "LC_MESSAGES" / "ok.po"
        for entry in polib.pofile(str(po_path)):
            if entry.obsolete or not entry.msgid:
                continue
            catalog.setdefault(entry.msgid, {})[locale] = (
                entry.msgstr if entry.msgstr else entry.msgid
            )
    return catalog


def main() -> None:
    catalog = build_catalog()
    OUT.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(f"exported {len(catalog)} msgids -> {OUT}")


if __name__ == "__main__":
    main()
