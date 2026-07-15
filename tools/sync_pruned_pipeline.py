"""upstream -> prune i18n -> main (i18n + fork extras). Temp: F:/Cursor/Temp."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

TEMP_DIR = Path("F:/Cursor/Temp")
I18N_WT = Path("F:/Cursor/bm-ok-nte-i18n")
MAIN_WT = Path("F:/Cursor/bm-ok-nte")
TOOLS = MAIN_WT / "tools"
UPSTREAM_REF = "upstream/main"
MAIN_FORK_REF = "cbf9eb7"
ENV = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}

MAIN_PROTECT = [
    "src/config.py",
    "src/tasks/FishingTask.py",
    "main.py",
    "main_debug.py",
    "bm_single_instance.py",
    "bm_github_update.py",
    "src/bm_shell.py",
    "pyappify.yml",
    "build.py",
    "build_win10.bat",
    "build_win10_zip.bat",
    "i18n/gui",
]
MAIN_PROTECT_REFS = {"main.py": MAIN_FORK_REF, "main_debug.py": MAIN_FORK_REF}


def run(cmd: list[str], *, cwd: Path, check: bool = True) -> None:
    print("+", " ".join(cmd), f"  (cwd={cwd.name})")
    subprocess.run(cmd, cwd=cwd, check=check, text=True, env=ENV)


def ensure_temp() -> Path:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    session = TEMP_DIR / f"bm-prune-{os.getpid()}"
    session.mkdir(parents=True, exist_ok=True)
    return session


def copy_tools_to_i18n() -> None:
    dest = I18N_WT / "tools"
    dest.mkdir(parents=True, exist_ok=True)
    for name in TOOLS.iterdir():
        if name.is_file() and not name.name.startswith("_"):
            shutil.copy2(name, dest / name.name)


def backup_main_protect(dest: Path) -> None:
    for rel in MAIN_PROTECT:
        src = MAIN_WT / rel
        out = dest / rel
        if src.is_dir():
            shutil.copytree(src, out, dirs_exist_ok=True)
        elif src.is_file():
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, out)


def restore_main_protect(backup: Path) -> None:
    for rel in MAIN_PROTECT:
        ref = MAIN_PROTECT_REFS.get(rel)
        if ref:
            dest = MAIN_WT / rel
            try:
                data = subprocess.check_output(["git", "show", f"{ref}:{rel}"], cwd=MAIN_WT)
            except subprocess.CalledProcessError:
                continue
            dest.write_bytes(data)
            continue
        src = backup / rel
        dest = MAIN_WT / rel
        if not src.exists():
            continue
        if src.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)


def apply_catalog(repo: Path, catalog_path: Path, order_path: Path) -> None:
    run(
        [
            sys.executable,
            str(TOOLS / "rebuild_catalog_from_upstream.py"),
            "--apply",
            str(repo),
            str(catalog_path),
            str(order_path),
        ],
        cwd=MAIN_WT,
    )


def audit(repo: Path, label: str) -> None:
    import polib

    counts = []
    empty = 0
    for loc in ["en_US", "zh_TW", "zh_CN", "ja_JP", "ko_KR", "es_ES", "pt_BR"]:
        po = polib.pofile(str(repo / "i18n" / loc / "LC_MESSAGES" / "ok.po"))
        ids = [e for e in po if e.msgid]
        counts.append(len(ids))
        empty += sum(1 for e in ids if not e.msgstr.strip())
    print(f"  [{label}] {counts[0]} msgids/locale, same={len(set(counts))==1}, empty={empty}")


def main() -> int:
    session = ensure_temp()
    print(f"session: {session}")

    # --- upstream code: i18n worktree ---
    print("\n=== 1. i18n <= upstream/main ===")
    run(["git", "fetch", "upstream"], cwd=I18N_WT)
    run(["git", "checkout", UPSTREAM_REF, "--", "."], cwd=I18N_WT)
    copy_tools_to_i18n()

    # --- rebuild catalogs from upstream + fork rules ---
    print("\n=== 2. rebuild catalogs (prune) ===")
    run([sys.executable, str(TOOLS / "rebuild_catalog_from_upstream.py")], cwd=MAIN_WT)
    report = json.loads((TEMP_DIR / "catalog_rebuild_report.json").read_text(encoding="utf-8"))
    shutil.copy2(TEMP_DIR / "i18n_catalog_upstream.json", session / "i18n_catalog.json")

    # --- apply i18n catalog ---
    print("\n=== 3. i18n po (upstream keys only) ===")
    shutil.copy2(session / "i18n_catalog.json", I18N_WT / "tools" / "i18n_catalog.json")
    apply_catalog(I18N_WT, session / "i18n_catalog.json", TEMP_DIR / "upstream_order.json")
    run([sys.executable, "tools/fix_zh_tw_catalog.py"], cwd=I18N_WT)
    apply_catalog(I18N_WT, I18N_WT / "tools" / "i18n_catalog.json", TEMP_DIR / "upstream_order.json")
    audit(I18N_WT, "i18n")

    # --- main code from i18n + protect fork ---
    print("\n=== 4. main <= i18n code + fork protect ===")
    protect = session / "main_protect"
    backup_main_protect(protect)
    run(["git", "fetch", "upstream"], cwd=MAIN_WT)
    run(["git", "checkout", UPSTREAM_REF, "--", "."], cwd=MAIN_WT)
    for src_path in I18N_WT.rglob("*"):
        if not src_path.is_file():
            continue
        rel = src_path.relative_to(I18N_WT)
        if any(str(rel).startswith(p.rstrip("/")) for p in MAIN_PROTECT):
            continue
        if rel.parts and rel.parts[0] in {".git", "offline", "dist_portable", "dist_zip", "_cache", "pyappify_build"}:
            continue
        dest = MAIN_WT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dest)
    restore_main_protect(protect)

    # --- main po: i18n base + fork extras ---
    print("\n=== 5. main po (i18n + fork extras) ===")
    run([sys.executable, "tools/fix_zh_tw_catalog.py"], cwd=MAIN_WT)
    apply_catalog(MAIN_WT, MAIN_WT / "tools" / "i18n_catalog.json", TEMP_DIR / "main_order.json")
    run([sys.executable, "tools/sync_fishing_i18n.py"], cwd=MAIN_WT)
    # fishing log sync must not clobber UI labels; refresh from catalog
    apply_catalog(MAIN_WT, MAIN_WT / "tools" / "i18n_catalog.json", TEMP_DIR / "main_order.json")
    run([sys.executable, str(TOOLS / "compile_mo.py")], cwd=MAIN_WT)
    audit(MAIN_WT, "main")
    i18n_n = report["i18n_count"]
    main_n = report["main_count"]
    print(f"  main - i18n = {main_n - i18n_n} fork-only keys")

    # --- offline ---
    print("\n=== 6. offline overlay ===")
    run(
        [
            sys.executable,
            "-c",
            "from pathlib import Path; import build; "
            "build.PROJECT_ROOT=Path('.').resolve(); "
            "build.overlay_local_app_sources(build.PROJECT_ROOT/'offline','ok-nte')",
        ],
        cwd=MAIN_WT,
    )

    print(f"\n=== done | removed {report['removed_count']} legacy keys ===")
    print(f"report: {TEMP_DIR / 'catalog_rebuild_report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
