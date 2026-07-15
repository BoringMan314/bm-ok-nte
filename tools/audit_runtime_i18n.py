"""Check ok-script runtime notification strings against catalog + upstream TS."""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ["zh_TW", "zh_CN", "en_US", "ja_JP", "ko_KR", "es_ES", "pt_BR"]

# Hardcoded strings passed to notification.emit / alert_info in ok-script (PC capture path).
RUNTIME_STRINGS = [
    "Game Exited",
    "Paused because game window is minimized or out of screen!",
    "Auto exit because game exited",
    "Paused because game exited",
    "Stopped",
    "Paused because browser exited",
]

UPSTREAM_TS_URL = (
    "https://raw.githubusercontent.com/ok-oldking/ok-script/master/ok/gui/i18n/en_US.ts"
)
PATCHES = ROOT / "i18n" / "gui" / "notification_patches.json"


def load_catalog() -> dict[str, dict[str, str]]:
    return json.loads((ROOT / "tools" / "i18n_catalog.json").read_text(encoding="utf-8"))


def load_po(locale: str) -> dict[str, str]:
    import polib

    po_path = ROOT / "i18n" / locale / "LC_MESSAGES" / "ok.po"
    return {
        e.msgid: e.msgstr
        for e in polib.pofile(str(po_path))
        if e.msgid and not e.obsolete
    }


def fetch_upstream_ts() -> str:
    with urllib.request.urlopen(UPSTREAM_TS_URL, timeout=30) as resp:
        return resp.read().decode("utf-8")


def in_upstream_ts(ts: str, source: str) -> bool:
    return bool(re.search(rf"<source>{re.escape(source)}</source>", ts))


def patch_covers(source: str) -> list[str]:
    if not PATCHES.is_file():
        return []
    data = json.loads(PATCHES.read_text(encoding="utf-8"))
    covered = []
    for locale, ctx_map in data.items():
        app = ctx_map.get("app", {})
        if source in app and app[source].strip():
            covered.append(locale)
    return covered


def po_ok(msgid: str, msgstr: str, locale: str) -> bool:
    if not msgstr.strip():
        return False
    if locale == "en_US":
        return True
    if locale == "zh_CN" and msgid == msgstr and re.search(r"[\u4e00-\u9fff]", msgid):
        return True
    return msgstr != msgid


def covered(source: str, catalog: dict, upstream_ts: str) -> tuple[bool, str]:
    if source in catalog and all(
        catalog[source].get(loc, "").strip() for loc in LOCALES
    ):
        patched = patch_covers(source)
        if len(patched) == 7:
            return True, "catalog+patch"
        return True, "catalog"
    if in_upstream_ts(upstream_ts, source):
        return True, "upstream TS"
    patched = patch_covers(source)
    if len(patched) == 7:
        return True, "patch only"
    return False, "uncovered"


def main() -> int:
    catalog = load_catalog()
    upstream_ts = fetch_upstream_ts()
    patch_data = json.loads(PATCHES.read_text(encoding="utf-8")) if PATCHES.is_file() else {}

    issues: list[str] = []
    print("Runtime notification string audit\n")
    print(f"{'string':<58} {'coverage':<14} {'po 7/7':<8} {'patch'}")
    print("-" * 95)

    for source in RUNTIME_STRINGS:
        ok, via = covered(source, catalog, upstream_ts)
        po_missing = []
        for loc in LOCALES:
            po = load_po(loc)
            if source not in po or not po_ok(source, po[source], loc):
                po_missing.append(loc)
        patched = patch_covers(source)
        patch_mark = f"{len(patched)}/7" if patched else "-"
        po_mark = "ok" if not po_missing else f"miss:{','.join(po_missing)}"

        print(f"{source[:58]:<58} {via if ok else 'MISSING':<14} {po_mark:<8} {patch_mark}")

        if not ok:
            issues.append(f"Uncovered: {source!r}")
        elif po_missing:
            issues.append(f"po incomplete for {source!r}: {po_missing}")

    print()
    if patch_data:
        keys = sorted(next(iter(patch_data.values())).get("app", {}))
        print(f"notification_patches.json: {len(patch_data)} locales, {len(keys)} strings")
    print(f"\ncatalog entries: {len(catalog)}")
    print(f"issues: {len(issues)}")
    for item in issues:
        print(f"  - {item}")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
