"""upstream -> i18n -> main sync pipeline (no git commits). Temp files: F:/Cursor/Temp."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TEMP_DIR = Path("F:/Cursor/Temp")
I18N_WT = Path("F:/Cursor/bm-ok-nte-i18n")
MAIN_WT = Path("F:/Cursor/bm-ok-nte")
LOCALES = ["en_US", "es_ES", "ja_JP", "ko_KR", "pt_BR", "zh_CN", "zh_TW"]
UPSTREAM_REF = "upstream/main"
I18N_FORK_REF = "5cab455"
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

MAIN_PROTECT_REFS = {
    "main.py": MAIN_FORK_REF,
    "main_debug.py": MAIN_FORK_REF,
}


def run(cmd: list[str], *, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(cmd), f"  (cwd={cwd.name})")
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, env=ENV)


def ensure_temp() -> Path:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    session = TEMP_DIR / f"bm-sync-{os.getpid()}"
    session.mkdir(parents=True, exist_ok=True)
    return session


def save_i18n_snapshot(repo: Path, dest: Path) -> None:
    for locale in LOCALES:
        src = repo / "i18n" / locale / "LC_MESSAGES" / "ok.po"
        if src.is_file():
            out = dest / locale / "ok.po"
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, out)


def load_snapshot_po(snapshot: Path, locale: str) -> dict[str, str]:
    import polib

    path = snapshot / locale / "ok.po"
    if not path.is_file():
        return {}
    return {e.msgid: e.msgstr for e in polib.pofile(str(path)) if e.msgid and not e.obsolete}


def git_po(repo: Path, ref: str, locale: str, *, tmp_dir: Path) -> "polib.POFile":
    import polib

    raw = subprocess.check_output(
        ["git", "show", f"{ref}:i18n/{locale}/LC_MESSAGES/ok.po"],
        cwd=repo,
    )
    path = tmp_dir / f"git_{ref.replace('/', '_')}_{locale}.po"
    path.write_bytes(raw)
    return polib.pofile(str(path))


def po_map(po: "polib.POFile") -> dict[str, str]:
    return {e.msgid: e.msgstr for e in po if e.msgid and not e.obsolete}


def merge_po_files(
    *,
    repo: Path,
    upstream_ref: str,
    fork_ref: str | None,
    extra_fork_ref: str | None,
    fork_snapshot: Path | None,
    include_fork_only: bool,
    tmp_dir: Path,
) -> None:
    import polib

    catalog_path = MAIN_WT / "tools" / "i18n_catalog.json"
    catalog: dict[str, dict[str, str]] = {}
    if catalog_path.is_file():
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))

    for locale in LOCALES:
        up_po = git_po(repo, upstream_ref, locale, tmp_dir=tmp_dir)
        up = po_map(up_po)
        fork = load_snapshot_po(fork_snapshot, locale) if fork_snapshot else {}
        if not fork and fork_ref:
            fork = po_map(git_po(repo, fork_ref, locale, tmp_dir=tmp_dir))
        extra = (
            po_map(git_po(repo, extra_fork_ref, locale, tmp_dir=tmp_dir))
            if extra_fork_ref
            else {}
        )

        order: list[str] = []
        for entry in up_po:
            if entry.msgid and entry.msgid not in order:
                order.append(entry.msgid)

        if include_fork_only:
            for mid in sorted(set(fork) | set(extra)):
                if mid not in order:
                    order.append(mid)

        out = polib.POFile()
        out.metadata = up_po.metadata
        for msgid in order:
            msgstr = ""
            for bucket in (extra, fork, up):
                if msgid in bucket and bucket[msgid].strip():
                    msgstr = bucket[msgid]
                    break
            if not msgstr.strip() and msgid in catalog:
                msgstr = catalog[msgid].get(locale, "") or catalog[msgid].get("zh_CN", "")
            if not msgstr.strip():
                msgstr = up.get(msgid, "") or fork.get(msgid, "") or extra.get(msgid, "") or msgid
            out.append(polib.POEntry(msgid=msgid, msgstr=msgstr))

        dest = repo / "i18n" / locale / "LC_MESSAGES" / "ok.po"
        out.wrapwidth = 999999
        out.save(str(dest))
        print(f"  {locale}: {len(order)} msgids")


def copy_tools_to_i18n() -> None:
    src = MAIN_WT / "tools"
    dest = I18N_WT / "tools"
    dest.mkdir(parents=True, exist_ok=True)
    for name in src.iterdir():
        if name.is_file() and not name.name.startswith("_"):
            shutil.copy2(name, dest / name.name)


def sync_i18n_worktree(session: Path) -> None:
    print("\n=== Step 1: i18n worktree <= upstream/main ===")
    fork_snap = session / "i18n_fork_snapshot"
    save_i18n_snapshot(I18N_WT, fork_snap)

    run(["git", "fetch", "upstream"], cwd=I18N_WT)
    run(["git", "checkout", UPSTREAM_REF, "--", "."], cwd=I18N_WT)
    copy_tools_to_i18n()
    print("  merge i18n po (upstream structure + fork translations)")
    merge_po_files(
        repo=I18N_WT,
        upstream_ref=UPSTREAM_REF,
        fork_ref=I18N_FORK_REF,
        extra_fork_ref=None,
        fork_snapshot=fork_snap,
        include_fork_only=False,
        tmp_dir=session,
    )
    run([sys.executable, "tools/merge_upstream_i18n.py"], cwd=I18N_WT)
    run([sys.executable, "tools/fix_zh_tw_catalog.py"], cwd=I18N_WT)
    run([sys.executable, "tools/apply_game_glossary.py"], cwd=I18N_WT, check=False)
    run([sys.executable, "tools/sync_i18n.py"], cwd=I18N_WT)
    run([sys.executable, "tools/compile_mo.py"], cwd=I18N_WT)
    audit(I18N_WT, label="i18n")


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


def rsync_from_i18n(session: Path) -> None:
    print("\n=== Step 2: main worktree <= i18n (protect fork files) ===")
    run(["git", "fetch", "upstream"], cwd=MAIN_WT)
    protect = session / "main_protect"
    backup_main_protect(protect)
    run(["git", "checkout", UPSTREAM_REF, "--", "."], cwd=MAIN_WT)

    for src_path in I18N_WT.rglob("*"):
        if not src_path.is_file():
            continue
        rel = src_path.relative_to(I18N_WT)
        if any(str(rel).startswith(p.rstrip("/")) for p in MAIN_PROTECT):
            continue
        if rel.parts and rel.parts[0] in {
            ".git",
            "offline",
            "dist_portable",
            "dist_zip",
            "_cache",
            "pyappify_build",
        }:
            continue
        dest = MAIN_WT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dest)

    restore_main_protect(protect)


def sync_main_i18n(session: Path) -> None:
    print("\n=== Step 3: main i18n = i18n + extra fork translations ===")
    i18n_synced = session / "i18n_synced"
    save_i18n_snapshot(I18N_WT, i18n_synced)
    merge_po_files(
        repo=MAIN_WT,
        upstream_ref=UPSTREAM_REF,
        fork_ref=I18N_FORK_REF,
        extra_fork_ref=MAIN_FORK_REF,
        fork_snapshot=i18n_synced,
        include_fork_only=True,
        tmp_dir=session,
    )
    run([sys.executable, "tools/merge_upstream_i18n.py"], cwd=MAIN_WT)
    run([sys.executable, "tools/fix_zh_tw_catalog.py"], cwd=MAIN_WT)
    run([sys.executable, "tools/apply_game_glossary.py"], cwd=MAIN_WT, check=False)
    run([sys.executable, "tools/sync_fishing_i18n.py"], cwd=MAIN_WT)
    run([sys.executable, "tools/sync_i18n.py"], cwd=MAIN_WT)
    run([sys.executable, "tools/compile_mo.py"], cwd=MAIN_WT)
    audit(MAIN_WT, label="main")


def overlay_offline() -> None:
    print("\n=== Step 4: offline overlay ===")
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


def audit(repo: Path, *, label: str) -> None:
    import polib

    counts: list[int] = []
    empty = 0
    for locale in LOCALES:
        po = polib.pofile(str(repo / "i18n" / locale / "LC_MESSAGES" / "ok.po"))
        ids = [e for e in po if e.msgid]
        counts.append(len(ids))
        empty += sum(1 for e in ids if not e.msgstr.strip())
    print(f"  [{label}] entries per locale: {counts[0]} (all same: {len(set(counts)) == 1})")
    print(f"  [{label}] empty msgstr total: {empty}")
    if label == "main":
        i18n_po = polib.pofile(str(I18N_WT / "i18n" / "en_US" / "LC_MESSAGES" / "ok.po"))
        i18n_n = len([e for e in i18n_po if e.msgid])
        if counts[0] < i18n_n:
            print(f"  WARNING: main ({counts[0]}) < i18n ({i18n_n})")
        elif counts[0] == i18n_n:
            print(f"  note: main == i18n ({counts[0]}); fork extras merged into shared catalog")
        else:
            print(f"  ok: main ({counts[0]}) > i18n ({i18n_n})")


def cleanup_scattered_temp() -> None:
    print("\n=== Cleanup scattered temp files ===")
    patterns = [
        "_fishing_fork.py",
        "_lost_fishing.txt",
        "_lost_i18n.txt",
        "_main_config_fork.py",
        "_main_extra.txt",
        "_old_zhtw.po",
        "_only_fork.txt",
        "_only_upstream.txt",
        "_stage_tw.json",
        "_tw_check.json",
        "i18n_full_audit_latest.json",
        "i18n_full_audit_reliable.json",
    ]
    roots = [Path("F:/Cursor"), MAIN_WT, I18N_WT]
    for root in roots:
        for name in patterns:
            path = root / name
            if path.is_file():
                path.unlink()
                print(f"  deleted {path}")
    for repo in (MAIN_WT, I18N_WT):
        audit_json = repo / "tools" / "_glossary_audit.json"
        if audit_json.is_file():
            dest = TEMP_DIR / f"glossary_audit_{repo.name}.json"
            shutil.move(str(audit_json), str(dest))
            print(f"  moved {audit_json} -> {dest}")


def main() -> int:
    session = ensure_temp()
    print(f"temp session: {session}")
    try:
        if "--main-only" not in sys.argv:
            sync_i18n_worktree(session)
        rsync_from_i18n(session)
        sync_main_i18n(session)
        overlay_offline()
    finally:
        cleanup_scattered_temp()
    print(f"\n=== done (not committed); session temp kept at {session} ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
