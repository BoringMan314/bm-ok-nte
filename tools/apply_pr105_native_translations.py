"""Apply pr105_native_translations.json to i18n_catalog and sync po/mo files."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH_PATH = ROOT / "tools" / "pr105_native_translations.json"
CATALOG_PATH = ROOT / "tools" / "i18n_catalog.json"
NEED_PATH = ROOT / "tools" / "_need_native.json"
PATCH_LOCALES = ["ja_JP", "ko_KR", "es_ES", "pt_BR"]
CJK = re.compile(r"[\u4e00-\u9fff]")
# Romanized character names legitimately match en_US in es/pt.
PROPER_NAME_MSGIDS = frozenset({"九原", "娜娜莉", "小吱", "早雾", "浔", "薄荷", "零"})


def validate_no_en_echo(catalog: dict[str, dict[str, str]]) -> list[dict]:
    issues: list[dict] = []
    for msgid, translations in catalog.items():
        if not CJK.search(msgid):
            continue
        en = translations.get("en_US", "")
        for locale in PATCH_LOCALES:
            val = translations.get(locale, "")
            if not val or val != en or locale == "en_US":
                continue
            if msgid in PROPER_NAME_MSGIDS and locale in ("es_ES", "pt_BR"):
                continue
            issues.append({"msgid": msgid, "locale": locale, "value": val})
    return issues


def main() -> int:
    patches = json.loads(PATCH_PATH.read_text(encoding="utf-8"))
    need = json.loads(NEED_PATH.read_text(encoding="utf-8"))
    need_ids = {x["msgid"] for x in need}

    missing_need = sorted(need_ids - set(patches))
    if missing_need:
        print(f"ERROR: patch file missing {len(missing_need)} required msgids", file=sys.stderr)
        return 1

    catalog: dict[str, dict[str, str]] = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    patched = 0
    for msgid, locale_map in patches.items():
        if msgid not in catalog:
            catalog[msgid] = {}
        entry = catalog[msgid]
        for locale, value in locale_map.items():
            if entry.get(locale) != value:
                entry[locale] = value
                patched += 1

    echo_issues = validate_no_en_echo(catalog)
    if echo_issues:
        print(f"ERROR: {len(echo_issues)} ja/ko/es/pt entries still equal en_US for CJK msgids", file=sys.stderr)
        for item in echo_issues[:10]:
            print(f"  {item['locale']}: {item['msgid'][:60]!r}", file=sys.stderr)
        return 1

    CATALOG_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"patched {patched} locale values across {len(patches)} msgids")

    subprocess.run([sys.executable, str(ROOT / "tools" / "sync_i18n.py")], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "tools" / "compile_mo.py")], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "tools" / "export_i18n_catalog.py")], cwd=ROOT, check=True)

    audit = subprocess.run([sys.executable, str(ROOT / "tools" / "audit_i18n.py")], cwd=ROOT)
    return audit.returncode


if __name__ == "__main__":
    raise SystemExit(main())
