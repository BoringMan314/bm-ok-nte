"""Apply official game glossary to i18n_catalog.json and sync po/mo."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GLOSSARY_PATH = ROOT / "tools" / "game_glossary.json"
CATALOG_PATH = ROOT / "tools" / "i18n_catalog.json"


def _apply_replacements(text: str, mapping: dict[str, str]) -> str:
    out = text
    for old, new in sorted(mapping.items(), key=lambda x: -len(x[0])):
        if old in out:
            out = out.replace(old, new)
    return out


def main() -> int:
    glossary = json.loads(GLOSSARY_PATH.read_text(encoding="utf-8"))
    catalog: dict[str, dict[str, str]] = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    patched = 0

    for msgid, loc_map in glossary.get("characters", {}).items():
        if msgid not in catalog:
            catalog[msgid] = {}
        for loc, val in loc_map.items():
            if catalog[msgid].get(loc) != val:
                catalog[msgid][loc] = val
                patched += 1

    for msgid, loc_map in glossary.get("entries", {}).items():
        if msgid not in catalog:
            catalog[msgid] = {}
        for loc, val in loc_map.items():
            if catalog[msgid].get(loc) != val:
                catalog[msgid][loc] = val
                patched += 1

    replace_map: dict[str, dict[str, str]] = glossary.get("replace_in_translation", {})
    for msgid, loc_map in catalog.items():
        for loc, repl in replace_map.items():
            if loc not in loc_map:
                continue
            val = loc_map.get(loc, "")
            if not val:
                continue
            new_val = _apply_replacements(val, repl)
            if new_val != val:
                loc_map[loc] = new_val
                patched += 1

    CATALOG_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"glossary patched {patched} locale values")

    subprocess.run([sys.executable, str(ROOT / "tools" / "sync_i18n.py")], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "tools" / "compile_mo.py")], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "tools" / "audit_glossary.py")], cwd=ROOT, check=True)
    audit2 = subprocess.run([sys.executable, str(ROOT / "tools" / "audit_i18n.py")], cwd=ROOT)
    subprocess.run([sys.executable, str(ROOT / "tools" / "audit_runtime_i18n.py")], cwd=ROOT, check=True)
    return audit2.returncode


if __name__ == "__main__":
    raise SystemExit(main())
