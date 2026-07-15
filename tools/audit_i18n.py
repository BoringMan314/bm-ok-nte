"""Audit ok.po catalogs against the full i18n catalog."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import polib
from sync_fishing_i18n import LOCALES
from sync_i18n import _load_entries

CJK = re.compile(r"[\u4e00-\u9fff]")
ASCII = re.compile(r"^[\x00-\x7f]+$")
# Internal / non-UI msgids (function keys, debug logger prefix)
IGNORE_MSGIDS = frozenset({"F9", "F10", "F11", "F12", "info_set"})
# Romanized character names (en/es/pt share same spelling).
PROPER_NAME_MSGIDS = frozenset({"九原", "娜娜莉", "小吱", "早雾", "浔", "薄荷", "零"})
NON_ZH_LOCALES = ("ja_JP", "ko_KR", "es_ES", "pt_BR")


def main() -> int:
    canonical = _load_entries()
    issues: list[dict] = []

    glossary_path = ROOT / "tools" / "game_glossary.json"
    glossary_data = (
        json.loads(glossary_path.read_text(encoding="utf-8")) if glossary_path.is_file() else {}
    )
    glossary_chars = glossary_data.get("characters", {})
    glossary_entries = glossary_data.get("entries", {})

    for msgid, translations in sorted(canonical.items()):
        for locale in LOCALES:
            po_path = ROOT / "i18n" / locale / "LC_MESSAGES" / "ok.po"
            by_id = {
                e.msgid: e.msgstr
                for e in polib.pofile(str(po_path))
                if e.msgid and not e.obsolete
            }
            expected = translations.get(locale, msgid)
            if msgid not in by_id:
                issues.append({"kind": "MISSING", "locale": locale, "msgid": msgid})
            elif by_id[msgid] != expected:
                issues.append(
                    {
                        "kind": "MISMATCH",
                        "locale": locale,
                        "msgid": msgid,
                        "actual": by_id[msgid],
                        "expected": expected,
                    }
                )

    po_sets = {}
    for locale in LOCALES:
        po_path = ROOT / "i18n" / locale / "LC_MESSAGES" / "ok.po"
        po_sets[locale] = {
            e.msgid for e in polib.pofile(str(po_path)) if e.msgid and not e.obsolete
        }
    union = set().union(*po_sets.values())
    for locale in LOCALES:
        missing = sorted(union - po_sets[locale])
        if missing:
            issues.append(
                {
                    "kind": "LOCALE_GAP",
                    "locale": locale,
                    "count": len(missing),
                    "sample": missing[:5],
                }
            )

    for locale in LOCALES:
        po_path = ROOT / "i18n" / locale / "LC_MESSAGES" / "ok.po"
        for entry in polib.pofile(str(po_path)):
            if entry.obsolete or not entry.msgid:
                continue
            eff = entry.msgstr if entry.msgstr else entry.msgid
            if not entry.msgstr.strip():
                if locale == "zh_CN" and CJK.search(entry.msgid):
                    continue
                if locale == "en_US" and not CJK.search(entry.msgid):
                    continue
                issues.append({"kind": "EMPTY", "locale": locale, "msgid": entry.msgid})
            elif locale not in ("zh_CN", "zh_TW") and CJK.search(entry.msgid) and eff == entry.msgid:
                expected = glossary_chars.get(entry.msgid, {}).get(locale)
                if expected and eff == expected:
                    pass
                else:
                    issues.append(
                        {"kind": "UNTRANSLATED_CJK", "locale": locale, "msgid": entry.msgid}
                    )
            elif locale in ("zh_TW", "zh_CN") and ASCII.match(entry.msgid) and eff == entry.msgid:
                if entry.msgid not in IGNORE_MSGIDS:
                    issues.append(
                        {"kind": "UNTRANSLATED_ASCII", "locale": locale, "msgid": entry.msgid}
                    )

    en_strings = {msgid: translations.get("en_US", "") for msgid, translations in canonical.items()}
    for msgid, translations in sorted(canonical.items()):
        if not CJK.search(msgid):
            continue
        en = en_strings.get(msgid, "")
        if not en or en == msgid:
            continue
        for locale in NON_ZH_LOCALES:
            val = translations.get(locale, "")
            if val != en:
                continue
            if locale in ("es_ES", "pt_BR") and msgid in PROPER_NAME_MSGIDS:
                continue
            entry_spec = glossary_entries.get(msgid, {})
            if entry_spec.get(locale) == en:
                continue
            issues.append(
                {"kind": "EN_FALLBACK", "locale": locale, "msgid": msgid, "value": val}
            )

    out = ROOT / "tools" / "_i18n_audit.json"
    out.write_text(json.dumps(issues, ensure_ascii=False, indent=2), encoding="utf-8")

    managed = sum(1 for i in issues if i["kind"] in ("MISSING", "MISMATCH"))
    blocking = sum(
        1
        for i in issues
        if i["kind"]
        in ("MISSING", "MISMATCH", "EMPTY", "UNTRANSLATED_CJK", "UNTRANSLATED_ASCII", "EN_FALLBACK")
    )
    print(f"catalog={len(canonical)} issues={len(issues)} blocking={blocking} managed={managed}")
    print(f"report: {out}")
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
