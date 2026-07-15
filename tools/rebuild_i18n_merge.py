"""Merge pre-PR bm translations with upstream PR105 po (7 locales, same msgid set)."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ["zh_TW", "zh_CN", "en_US", "ja_JP", "ko_KR", "es_ES", "pt_BR"]
CJK = re.compile(r"[\u4e00-\u9fff]")
OLD_REF = "32143c2"


def _git_po(locale: str) -> "polib.POFile":
    import polib

    raw = subprocess.check_output(
        ["git", "show", f"{OLD_REF}:i18n/{locale}/LC_MESSAGES/ok.po"],
        cwd=ROOT,
    )
    path = ROOT / "tools" / f"_old_{locale}.po"
    path.write_bytes(raw)
    return polib.pofile(str(path))


def _is_untranslated_cjk(locale: str, msgid: str, msgstr: str) -> bool:
    if locale in ("zh_CN", "zh_TW", "en_US"):
        return False
    return bool(CJK.search(msgid) and msgstr == msgid)


def merge_locale(locale: str) -> None:
    import polib

    old = {e.msgid: e.msgstr for e in _git_po(locale) if e.msgid and not e.obsolete}
    new_path = ROOT / "i18n" / locale / "LC_MESSAGES" / "ok.po"
    po = polib.pofile(str(new_path))
    new = {e.msgid: e.msgstr for e in po if e.msgid and not e.obsolete}
    union = sorted(set(old) | set(new))

    out = polib.POFile()
    out.metadata = po.metadata
    for msgid in union:
        msgstr = new.get(msgid, "") or old.get(msgid, "") or msgid
        if msgid in old and old[msgid] and not _is_untranslated_cjk(locale, msgid, old[msgid]):
            msgstr = old[msgid]
        elif _is_untranslated_cjk(locale, msgid, msgstr) and msgid in old:
            msgstr = old[msgid]
        out.append(polib.POEntry(msgid=msgid, msgstr=msgstr))
    out.wrapwidth = 999999
    out.save(str(new_path))
    print(f"{locale}: {len(union)} msgids")


def main() -> int:
    for locale in LOCALES:
        merge_locale(locale)
    subprocess.run([sys.executable, str(ROOT / "tools" / "export_i18n_catalog.py")], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "tools" / "sync_i18n.py")], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "tools" / "compile_mo.py")], cwd=ROOT, check=True)
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "audit_i18n.py")], cwd=ROOT)
    subprocess.run([sys.executable, str(ROOT / "tools" / "audit_runtime_i18n.py")], cwd=ROOT, check=True)
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
