"""Rebuild i18n catalogs: upstream canonical + fork extras for main only."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

from merge_runtime_notifications import RUNTIME_ENTRIES
from sync_fishing_i18n import ENTRIES as FISHING_LOG_ENTRIES
from sync_i18n import FISHING_UI_ENTRIES, LOCALES

TEMP = Path("F:/Cursor/Temp")
UPSTREAM_REF = "upstream/main"
CATALOG_PATH = ROOT / "tools" / "i18n_catalog.json"
MAIN_SRC = Path("F:/Cursor/bm-ok-nte/src")
MAIN_EXTRA = Path("F:/Cursor/bm-ok-nte")
MAIN_FORK_PY = [
    MAIN_SRC / "config.py",
    MAIN_SRC / "bm_shell.py",
    MAIN_SRC / "tasks" / "FishingTask.py",
    MAIN_SRC / "tasks" / "BaseNTETask.py",
    MAIN_EXTRA / "main.py",
    MAIN_EXTRA / "bm_single_instance.py",
    MAIN_EXTRA / "bm_github_update.py",
]


def git_po_maps(ref: str) -> tuple[list[str], dict[str, dict[str, str]]]:
    import polib

    order: list[str] = []
    by_locale: dict[str, dict[str, str]] = {}
    for locale in LOCALES:
        raw = subprocess.check_output(
            ["git", "show", f"{ref}:i18n/{locale}/LC_MESSAGES/ok.po"],
            cwd=ROOT,
        )
        path = TEMP / f"_up_{locale}.po"
        path.write_bytes(raw)
        po = polib.pofile(str(path))
        loc_map: dict[str, str] = {}
        for entry in po:
            if entry.obsolete or not entry.msgid:
                continue
            if locale == "en_US" and entry.msgid not in order:
                order.append(entry.msgid)
            loc_map[entry.msgid] = entry.msgstr if entry.msgstr else entry.msgid
        by_locale[locale] = loc_map
    return order, by_locale


def load_old_catalog() -> dict[str, dict[str, str]]:
    if CATALOG_PATH.is_file():
        return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return {}


def hardcoded_fork_keys() -> set[str]:
    keys = set(FISHING_UI_ENTRIES) | set(FISHING_LOG_ENTRIES) | set(RUNTIME_ENTRIES)
    # bm_shell / tray strings live in gui patches; runtime notifications stay in ok.po
    keys.discard("RhythmTask error")
    return keys


def scan_main_src_keys() -> set[str]:
    used: set[str] = set()
    patterns = [
        re.compile(r'info_set\(\s*["\'](.+?)["\']'),
        re.compile(r'CONF_\w+\s*=\s*["\'](.+?)["\']'),
        re.compile(r'MODE_\w+\s*=\s*["\'](.+?)["\']'),
        re.compile(r'_set_stage\(\s*["\'](.+?)["\']'),
        re.compile(r'\.tr\(\s*["\'](.+?)["\']'),
        re.compile(r'_\(\s*["\'](.+?)["\']'),
        re.compile(r'logger\.\w+\(\s*_?\(\s*["\'](.+?)["\']'),
    ]
    for py in MAIN_FORK_PY:
        if not py.is_file():
            continue
        text = py.read_text(encoding="utf-8", errors="ignore")
        for pat in patterns:
            used.update(pat.findall(text))
        for m in re.finditer(r'config_description\s*=\s*\{', text):
            chunk = text[m.start() : m.start() + 4000]
            used.update(re.findall(r'["\']([^"\']{2,120})["\']\s*:', chunk))
    return used


def pick_msgstr(msgid: str, locale: str, *sources: dict[str, dict[str, str]]) -> str:
    for src in sources:
        locs = src.get(msgid, {})
        if isinstance(locs, dict):
            val = locs.get(locale, "")
            if val and val.strip():
                return val
    return msgid


def build_catalog(
    msgids: list[str],
    *,
    old: dict[str, dict[str, str]],
    upstream: dict[str, dict[str, str]],
    inline: dict[str, dict[str, str]],
) -> dict[str, dict[str, str]]:
    catalog: dict[str, dict[str, str]] = {}
    for msgid in msgids:
        bucket: dict[str, str] = {}
        for locale in LOCALES:
            bucket[locale] = pick_msgstr(msgid, locale, inline, old, upstream)
        catalog[msgid] = bucket
    return catalog


def write_po(repo: Path, catalog: dict[str, dict[str, str]], order: list[str]) -> None:
    import polib

    for locale in LOCALES:
        po = polib.POFile()
        po.metadata = {
            "Content-Type": "text/plain; charset=UTF-8",
            "Language": locale,
        }
        for msgid in order:
            locs = catalog.get(msgid, {})
            msgstr = locs.get(locale, msgid) if isinstance(locs, dict) else msgid
            po.append(polib.POEntry(msgid=msgid, msgstr=msgstr or msgid))
        po.wrapwidth = 999999
        dest = repo / "i18n" / locale / "LC_MESSAGES" / "ok.po"
        dest.parent.mkdir(parents=True, exist_ok=True)
        po.save(str(dest))


def main() -> tuple[dict, dict, list[str], list[str]]:
    import os

    os.environ.setdefault("PYTHONUTF8", "1")
    TEMP.mkdir(parents=True, exist_ok=True)

    up_order, up_maps = git_po_maps(UPSTREAM_REF)
    upstream_ids = set(up_order)
    old = load_old_catalog()

    # inline fork translation tables (authoritative for fishing/runtime extras)
    inline: dict[str, dict[str, str]] = {}
    for src in (FISHING_UI_ENTRIES, FISHING_LOG_ENTRIES, RUNTIME_ENTRIES):
        for msgid, locs in src.items():
            inline.setdefault(msgid, {}).update(locs)

    # --- i18n catalog: upstream only ---
    i18n_catalog = build_catalog(up_order, old=old, upstream=up_maps, inline=inline)

    # --- main catalog: upstream + fork extras actually used ---
    fork_keys = hardcoded_fork_keys() | scan_main_src_keys()
    main_extra = sorted(k for k in fork_keys if k and k not in upstream_ids)
    main_order = list(up_order) + [k for k in main_extra if k not in up_order]
    main_catalog = build_catalog(main_order, old=old, upstream=up_maps, inline=inline)

    report = {
        "upstream_count": len(up_order),
        "i18n_count": len(i18n_catalog),
        "main_count": len(main_catalog),
        "main_extra_count": len(main_extra),
        "main_extra_keys": main_extra,
        "removed_from_old_catalog": sorted(set(old) - set(i18n_catalog)),
        "removed_count": len(set(old) - set(i18n_catalog)),
    }
    (TEMP / "catalog_rebuild_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (TEMP / "upstream_order.json").write_text(
        json.dumps(up_order, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (TEMP / "main_order.json").write_text(
        json.dumps(main_order, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # Save i18n-branch catalog copy
    i18n_catalog_path = TEMP / "i18n_catalog_upstream.json"
    i18n_catalog_path.write_text(
        json.dumps(i18n_catalog, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    # Main catalog -> tools/i18n_catalog.json (used by sync_i18n on main)
    CATALOG_PATH.write_text(
        json.dumps(main_catalog, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(f"upstream={len(up_order)} i18n={len(i18n_catalog)} main={len(main_catalog)} (+{len(main_extra)} fork)")
    print(f"removed legacy={report['removed_count']}")
    print(f"report: {TEMP / 'catalog_rebuild_report.json'}")
    return i18n_catalog, main_catalog, up_order, main_order


def apply_catalog_to_repo(repo: Path, catalog: dict[str, dict[str, str]], order: list[str]) -> None:
    write_po(repo, catalog, order)
    subprocess.run([sys.executable, str(ROOT / "tools" / "compile_mo.py"), str(repo / "i18n")], cwd=ROOT, check=True)


if __name__ == "__main__":
    if len(sys.argv) >= 5 and sys.argv[1] == "--apply":
        repo = Path(sys.argv[2])
        catalog = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
        order = json.loads(Path(sys.argv[4]).read_text(encoding="utf-8"))
        write_po(repo, catalog, order)
        subprocess.run(
            [sys.executable, str(ROOT / "tools" / "compile_mo.py"), str(repo / "i18n")],
            cwd=ROOT,
            check=True,
        )
        raise SystemExit(0)
    i18n_cat, main_cat, up_order, main_order = main()
    if "--apply-i18n" in sys.argv:
        apply_catalog_to_repo(Path("F:/Cursor/bm-ok-nte-i18n"), i18n_cat, up_order)
    if "--apply-main" in sys.argv:
        apply_catalog_to_repo(Path("F:/Cursor/bm-ok-nte"), main_cat, main_order)
