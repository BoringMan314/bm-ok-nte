"""Apply GUI translation patches and recompile embedded Qt resources."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUI_PATCH_DIR = ROOT / "i18n" / "gui"
ZH_TW_PATCHES = GUI_PATCH_DIR / "zh_TW_patches.json"
CAPTURE_PATCHES = GUI_PATCH_DIR / "capture_method_patches.json"
TASKS_TAB_PATCHES = GUI_PATCH_DIR / "tasks_tab_patches.json"
BM_SHELL_PATCHES = GUI_PATCH_DIR / "bm_shell_patches.json"
NOTIFICATION_PATCHES = GUI_PATCH_DIR / "notification_patches.json"
DEFAULT_GUI = (
    ROOT
    / "pyappify_build"
    / "src-tauri"
    / "data"
    / "apps"
    / "ok-nte"
    / "working"
    / "ok"
    / "gui"
)


def load_ts_root(path: Path) -> ET.Element:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"<!DOCTYPE[^>]+>", "", text)
    return ET.fromstring(text)


def find_context(root: ET.Element, name: str) -> ET.Element | None:
    for ctx in root.findall("context"):
        name_el = ctx.find("name")
        if name_el is not None and name_el.text == name:
            return ctx
    return None


def find_message(ctx: ET.Element, source: str) -> ET.Element | None:
    for msg in ctx.findall("message"):
        src_el = msg.find("source")
        if src_el is not None and src_el.text == source:
            return msg
    return None


def add_message(ctx: ET.Element, source: str, translation: str) -> None:
    msg = ET.SubElement(ctx, "message")
    src_el = ET.SubElement(msg, "source")
    src_el.text = source
    tr_el = ET.SubElement(msg, "translation")
    tr_el.text = translation


def apply_patches_to_ts(ts_path: Path, patches: dict[str, dict[str, str]]) -> int:
    if not patches:
        return 0

    root = load_ts_root(ts_path)
    changed = 0
    for ctx_name, entries in patches.items():
        ctx = find_context(root, ctx_name)
        if ctx is None:
            ctx = ET.SubElement(root, "context")
            name_el = ET.SubElement(ctx, "name")
            name_el.text = ctx_name
        for source, translation in entries.items():
            msg = find_message(ctx, source)
            if msg is None:
                add_message(ctx, source, translation)
                changed += 1
                continue
            tr_el = msg.find("translation")
            if tr_el is None:
                tr_el = ET.SubElement(msg, "translation")
            if tr_el.text != translation:
                tr_el.text = translation
                changed += 1

    if changed:
        try:
            ET.indent(root, space="    ")
        except AttributeError:
            pass
        xml_body = ET.tostring(root, encoding="unicode")
        ts_path.write_text(
            "<?xml version='1.0' encoding='utf-8'?>\n" + xml_body + "\n",
            encoding="utf-8",
        )
    return changed


def load_json(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def find_qt_tool(name: str) -> str:
    """Resolve lrelease/rcc from the active Python's PySide6 package (not stale PATH)."""
    script_to_exe = {
        "pyside6-lrelease": "lrelease",
        "pyside6-rcc": "rcc",
        "lrelease": "lrelease",
        "rcc": "rcc",
    }
    exe_stem = script_to_exe.get(name, name.removeprefix("pyside6-"))

    try:
        import PySide6

        bundled = Path(PySide6.__file__).resolve().parent / f"{exe_stem}.exe"
        if bundled.is_file():
            return str(bundled)
    except ImportError:
        pass

    scripts_dir = Path(sys.executable).resolve().parent / "Scripts"
    for candidate in (scripts_dir / f"{name}.exe", scripts_dir / f"{exe_stem}.exe"):
        if candidate.is_file():
            return str(candidate)

    exe = shutil.which(name)
    if exe:
        return exe

    raise SystemExit(
        f"{name} not found for {sys.executable}. "
        "Install build deps: pip install -r requirements.txt"
    )


def compile_resources(gui_dir: Path) -> None:
    i18n_dir = gui_dir / "i18n"
    lrelease = find_qt_tool("pyside6-lrelease")
    rcc = find_qt_tool("pyside6-rcc")

    for ts_file in sorted(i18n_dir.glob("*.ts")):
        qm_file = ts_file.with_suffix(".qm")
        subprocess.run([lrelease, str(ts_file), "-qm", str(qm_file)], check=True)

    qrc = gui_dir / "qt.qrc"
    if not qrc.is_file():
        raise SystemExit(f"Missing {qrc} (sync ok/gui from repo before patching)")

    resources_py = gui_dir / "resources.py"
    result = subprocess.run(
        [rcc, "-g", "python", "qt.qrc", "-o", "resources.py"],
        cwd=gui_dir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise SystemExit(
            f"rcc failed for {gui_dir}\n"
            f"  command: {rcc} -g python qt.qrc -o resources.py\n"
            f"  {detail or '(no output)'}"
        )


def patch_gui_i18n(gui_dir: Path) -> None:
    gui_dir = gui_dir.resolve()
    if not gui_dir.is_dir():
        raise SystemExit(f"GUI directory not found: {gui_dir}")

    i18n_dir = gui_dir / "i18n"
    zh_tw_patches = load_json(ZH_TW_PATCHES)
    capture_patches = load_json(CAPTURE_PATCHES)

    total = 0
    zh_tw_ts = i18n_dir / "zh_TW.ts"
    if zh_tw_ts.is_file() and zh_tw_patches:
        n = apply_patches_to_ts(zh_tw_ts, zh_tw_patches)
        total += n
        print(f"[patch_gui_i18n] zh_TW: {n} entries")

    if capture_patches:
        for ts_file in sorted(i18n_dir.glob("*.ts")):
            n = apply_patches_to_ts(ts_file, capture_patches)
            if n:
                print(f"[patch_gui_i18n] {ts_file.stem}: {n} capture labels")
                total += n

    tasks_tab_patches = load_json(TASKS_TAB_PATCHES)
    if tasks_tab_patches:
        for ts_file in sorted(i18n_dir.glob("*.ts")):
            locale_patches = tasks_tab_patches.get(ts_file.stem)
            if not locale_patches:
                continue
            n = apply_patches_to_ts(ts_file, locale_patches)
            if n:
                print(f"[patch_gui_i18n] {ts_file.stem}: {n} tasks tab labels")
                total += n

    bm_shell_patches = load_json(BM_SHELL_PATCHES)
    if bm_shell_patches:
        for ts_file in sorted(i18n_dir.glob("*.ts")):
            locale_patches = bm_shell_patches.get(ts_file.stem)
            if not locale_patches:
                continue
            n = apply_patches_to_ts(ts_file, locale_patches)
            if n:
                print(f"[patch_gui_i18n] {ts_file.stem}: {n} tray/update labels")
                total += n

    notification_patches = load_json(NOTIFICATION_PATCHES)
    if notification_patches:
        for ts_file in sorted(i18n_dir.glob("*.ts")):
            locale_patches = notification_patches.get(ts_file.stem)
            if not locale_patches:
                continue
            n = apply_patches_to_ts(ts_file, locale_patches)
            if n:
                print(f"[patch_gui_i18n] {ts_file.stem}: {n} notification labels")
                total += n

    compile_resources(gui_dir)
    print(f"[patch_gui_i18n] done, {total} entries updated")


def main() -> None:
    gui_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_GUI
    patch_gui_i18n(gui_dir)


if __name__ == "__main__":
    main()
