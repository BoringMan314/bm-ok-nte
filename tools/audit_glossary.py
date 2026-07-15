"""Audit i18n catalog against game_glossary.json (coverage + per-locale consistency)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GLOSSARY_PATH = ROOT / "tools" / "game_glossary.json"
CATALOG_PATH = ROOT / "tools" / "i18n_catalog.json"
LOCALES = ["zh_TW", "zh_CN", "en_US", "ja_JP", "ko_KR", "es_ES", "pt_BR"]
CJK = re.compile(r"[\u4e00-\u9fff]")


def main() -> int:
    glossary = json.loads(GLOSSARY_PATH.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    issues: list[dict] = []

    for msgid, expected in glossary.get("characters", {}).items():
        if msgid not in catalog:
            issues.append({"kind": "MISSING_CHARACTER", "msgid": msgid})
            continue
        for loc, val in expected.items():
            actual = catalog[msgid].get(loc, "")
            if actual != val:
                issues.append(
                    {
                        "kind": "CHARACTER_MISMATCH",
                        "msgid": msgid,
                        "locale": loc,
                        "expected": val,
                        "actual": actual,
                    }
                )

    for msgid, expected in glossary.get("entries", {}).items():
        if msgid not in catalog:
            issues.append({"kind": "MISSING_ENTRY", "msgid": msgid})
            continue
        for loc, val in expected.items():
            actual = catalog[msgid].get(loc, "")
            if actual != val:
                issues.append(
                    {
                        "kind": "ENTRY_MISMATCH",
                        "msgid": msgid,
                        "locale": loc,
                        "expected": val,
                        "actual": actual,
                    }
                )

    for loc in LOCALES:
        for msgid, tr in catalog.items():
            if not msgid:
                continue
            if loc in ("zh_CN", "zh_TW"):
                continue
            val = tr.get(loc, "")
            if not val.strip() and CJK.search(msgid):
                issues.append({"kind": "EMPTY_TRANSLATION", "locale": loc, "msgid": msgid})

    en_by = {msgid: tr.get("en_US", "") for msgid, tr in catalog.items()}
    for loc in ("ja_JP", "ko_KR", "es_ES", "pt_BR"):
        for msgid, tr in catalog.items():
            if not CJK.search(msgid):
                continue
            if msgid in glossary.get("characters", {}):
                continue
            val = tr.get(loc, "")
            en = en_by.get(msgid, "")
            entry_spec = glossary.get("entries", {}).get(msgid, {})
            if entry_spec.get(loc) == en:
                continue
            if val and en and val == en and val != msgid:
                issues.append({"kind": "EN_FALLBACK", "locale": loc, "msgid": msgid})

    out = ROOT / "tools" / "_glossary_audit.json"
    out.write_text(json.dumps(issues, ensure_ascii=False, indent=2), encoding="utf-8")
    blocking = sum(
        1
        for i in issues
        if i["kind"]
        in (
            "MISSING_CHARACTER",
            "CHARACTER_MISMATCH",
            "MISSING_ENTRY",
            "ENTRY_MISMATCH",
            "EMPTY_TRANSLATION",
            "EN_FALLBACK",
        )
    )
    print(f"glossary issues={len(issues)} blocking={blocking}")
    print(f"report: {out}")
    if issues[:5]:
        for i in issues[:5]:
            print(i)
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
