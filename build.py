"""Build ok-nte portable/installer from offline PyAppify runtime in offline/data/."""

import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "tools"))
from build_progress import BuildProgress, TAURI_BUNDLE_HINTS, resolve_build_tag, run_with_progress

PROJECT_ROOT = Path(__file__).resolve().parent
BUILD_DIR = PROJECT_ROOT / "pyappify_build"
STAGE_DIR = PROJECT_ROOT / "build" / "ok-nte"
DIST_DIR = PROJECT_ROOT / "dist"
DIST_PORTABLE_DIR = PROJECT_ROOT / "dist_portable"
PROFILE = "Global"
PLATFORM = "win32"
OFFLINE_DIR = PROJECT_ROOT / "offline"
OFFLINE_DATA_DIR = OFFLINE_DIR / "data"
OFFLINE_SEED_DIR = BUILD_DIR / "src-tauri" / "data"
DIRECT_LAUNCHER_DIR = PROJECT_ROOT / "tools" / "direct_launcher"
SETUP_LAUNCHER_NAME = "_pyappify-setup.exe"
LAUNCHER_NAME = "bm-ok-nte"
RUNTIME_APP_ID = "ok-nte"  # offline/data/apps/<id>/ PyAppify tree
PYAPPIFY_RUNTIME_DIRS = ("EBWebView", "logs", "cache")
WORKING_USER_DATA_DIRS = ("configs", "logs", "screenshots")
RUNTIME_STAMP_NAME = ".bm_runtime_stamp"
WORKING_SCRUB_DIRS = ("__pycache__", ".pytest_cache", ".mypy_cache", ".git")
WORKING_SCRUB_GLOBS = ("*.pyc", "*.pyo", "*.log")
PORTABLE_LAUNCHER_MAX_BYTES = 3_000_000

_progress: BuildProgress | None = None


def verbose_logs() -> bool:
    return os.environ.get("BUILD_VERBOSE", "").strip().lower() in ("1", "true", "yes")


def build_log(message: str, *, verbose: bool = False) -> None:
    if verbose and not verbose_logs():
        return
    if _progress:
        _progress.log(message)
    else:
        print(message, flush=True)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def force_full_build() -> bool:
    return os.environ.get("BUILD_FULL", "").strip().lower() in ("1", "true", "yes")


def run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    label: str = "",
    log_cmd: bool = False,
    hints: list | None = None,
    time_tick: bool = False,
) -> None:
    run_with_progress(
        _progress,
        cmd,
        cwd=cwd or PROJECT_ROOT,
        label=label,
        log_cmd=log_cmd,
        hints=hints,
        time_tick=time_tick,
    )


def which(name: str) -> str | None:
    return shutil.which(name)


def runtime_app_id(config_name: str) -> str:
    if config_name in (LAUNCHER_NAME, RUNTIME_APP_ID):
        return RUNTIME_APP_ID
    return config_name


def launcher_exe_name() -> str:
    return f"{LAUNCHER_NAME}.exe"


def kill_app_processes(app_name: str | None = None, *, quiet: bool = False) -> None:
    if sys.platform != "win32":
        return
    runtime_id = app_name or RUNTIME_APP_ID
    marker = rf"{runtime_id}[\\/]working[\\/]main\.py"
    exe_names = {launcher_exe_name(), f"{runtime_id}.exe", "ok-nte.exe"}
    if not quiet:
        build_log(f"[build.py] stopping {', '.join(sorted(exe_names))} if running...")
    for image in sorted(exe_names):
        subprocess.run(
            ["taskkill", "/F", "/IM", image, "/T"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    for image in (f"{runtime_id}-manager.exe", f"{LAUNCHER_NAME}-manager.exe"):
        subprocess.run(
            ["taskkill", "/F", "/IM", image, "/T"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-CimInstance Win32_Process | "
            "Where-Object { ($_.Name -eq 'pythonw.exe' -or $_.Name -eq 'python.exe') "
            f"-and $_.CommandLine -match '{marker}' }} | "
            "Stop-Process -Force -ErrorAction SilentlyContinue",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1)


def check_python() -> None:
    v = sys.version_info
    if not (v.major == 3 and v.minor == 12):
        raise SystemExit("Win10 build requires Python 3.12.x.")


def install_python_deps() -> None:
    run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-q",
            "-r",
            str(PROJECT_ROOT / "requirements.txt"),
            "polib",
        ],
        label="pip install",
    )


def verify_portable_launcher(exe: Path) -> int:
    if not exe.is_file():
        raise SystemExit(f"Missing output: {exe}")
    size = exe.stat().st_size
    if size > PORTABLE_LAUNCHER_MAX_BYTES:
        raise SystemExit(
            f"{exe.name} is {size:,} bytes (PyAppify launcher); "
            f"expected direct launcher under {PORTABLE_LAUNCHER_MAX_BYTES // 1_000_000} MB"
        )
    return size


def cargo_bin_dir() -> Path:
    return Path.home() / ".cargo" / "bin"


def go_bin_dirs() -> list[str]:
    dirs: list[str] = []
    for candidate in (
        os.environ.get("GOROOT", ""),
        r"C:\Program Files\Go",
        r"C:\Program Files (x86)\Go",
    ):
        if candidate:
            go_bin = str(Path(candidate) / "bin")
            if Path(go_bin).exists():
                dirs.append(go_bin)
    return dirs


def ensure_build_path() -> None:
    extra: list[str] = []
    cargo_dir = str(cargo_bin_dir())
    npm_dir = str(Path(os.environ.get("APPDATA", "")) / "npm")
    node_dir = r"C:\Program Files\nodejs"
    for part in (*go_bin_dirs(), cargo_dir, npm_dir, node_dir):
        if part and Path(part).exists():
            extra.append(part)
    if extra:
        current = os.environ.get("PATH", "")
        missing = [
            part
            for part in extra
            if part.casefold() not in {p.casefold() for p in current.split(os.pathsep) if p}
        ]
        if missing:
            os.environ["PATH"] = os.pathsep.join(missing + [current])


def run_checked(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    resolved = cmd.copy()
    exe = shutil.which(resolved[0])
    if exe:
        resolved[0] = exe
    return subprocess.run(
        resolved,
        cwd=cwd or PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def cargo_works() -> bool:
    ensure_build_path()
    try:
        run_checked(["cargo", "--version"])
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def setup_rust() -> None:
    ensure_build_path()

    rustup = shutil.which("rustup") or str(cargo_bin_dir() / "rustup.exe")
    if not Path(rustup).exists() and not shutil.which("rustup"):
        if sys.platform != "win32":
            raise SystemExit("Local build script supports Windows only.")
        build_log("[build.py] rustup not found, installing Rust...")
        rustup_url = "https://win.rustup.rs/x86_64"
        with tempfile.TemporaryDirectory() as tmp:
            rustup_exe = Path(tmp) / "rustup-init.exe"
            urllib.request.urlretrieve(rustup_url, rustup_exe)
            subprocess.run(
                [str(rustup_exe), "-y", "--no-modify-path", "--default-toolchain", "stable"],
                cwd=PROJECT_ROOT,
                check=True,
            )
        ensure_build_path()
        rustup = shutil.which("rustup") or str(cargo_bin_dir() / "rustup.exe")

    if not Path(rustup).exists() and not shutil.which("rustup"):
        raise SystemExit("Rust setup failed: rustup not found after install.")

    build_log("[build.py] ensuring Rust stable toolchain...", verbose=True)
    run([rustup, "toolchain", "install", "stable"], label="rustup")
    run([rustup, "default", "stable"], label="rustup")

    if not cargo_works():
        raise SystemExit(
            "Rust setup failed: cargo is unavailable. "
            "Try opening a new terminal and run: rustup default stable"
        )
    build_log(f"[build.py] {run_checked(['cargo', '--version']).stdout.strip()}", verbose=True)


def nsis_bin_dirs() -> list[str]:
    dirs: list[str] = []
    for candidate in (
        Path(r"C:\Program Files (x86)\NSIS"),
        Path(r"C:\Program Files (x86)\NSIS\Bin"),
        Path(r"C:\Program Files\NSIS"),
        Path(r"C:\Program Files\NSIS\Bin"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "tauri" / "NSIS",
        Path(os.environ.get("LOCALAPPDATA", "")) / "tauri" / "NSIS" / "Bin",
    ):
        if (candidate / "makensis.exe").is_file():
            dirs.append(str(candidate))
    return dirs


def setup_nsis() -> None:
    ensure_build_path()
    for nsis_dir in nsis_bin_dirs():
        path = os.environ.get("PATH", "")
        if nsis_dir.casefold() not in {p.casefold() for p in path.split(os.pathsep) if p}:
            os.environ["PATH"] = nsis_dir + os.pathsep + path
    if shutil.which("makensis"):
        return

    build_log("[build.py] makensis not found, trying winget install NSIS...")
    winget = shutil.which("winget")
    if winget:
        subprocess.run(
            [
                winget,
                "install",
                "--id",
                "NSIS.NSIS",
                "-e",
                "--accept-package-agreements",
                "--accept-source-agreements",
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        for nsis_dir in nsis_bin_dirs():
            path = os.environ.get("PATH", "")
            if nsis_dir.casefold() not in {p.casefold() for p in path.split(os.pathsep) if p}:
                os.environ["PATH"] = nsis_dir + os.pathsep + path
        if shutil.which("makensis"):
            return

    raise SystemExit(
        "Missing NSIS (makensis). Install from https://nsis.sourceforge.io/ "
        "or run: winget install NSIS.NSIS"
    )


def setup_pnpm() -> None:
    ensure_build_path()
    if which("pnpm"):
        return
    if not which("npm"):
        raise SystemExit(
            "Missing build tools in PATH: pnpm, npm. "
            "Install Node.js from https://nodejs.org/, then rerun build_win10.bat"
        )
    build_log("[build.py] pnpm not found, installing via npm...")
    run(["npm", "install", "-g", "pnpm"], label="npm")
    ensure_build_path()
    if not which("pnpm"):
        raise SystemExit("pnpm install finished but pnpm is still not in PATH.")
    build_log(f"[build.py] pnpm {run_checked(['pnpm', '--version']).stdout.strip()}", verbose=True)


def check_tools(*, portable: bool = False) -> None:
    ensure_build_path()
    if not which("git"):
        raise SystemExit("Missing build tool in PATH: git")
    if not which("npm"):
        raise SystemExit(
            "Missing Node.js/npm in PATH. Install from https://nodejs.org/ "
            "then rerun build_win10.bat"
        )
    if not which("go"):
        raise SystemExit(
            "Missing Go in PATH (required for direct ok-nte.exe launcher). "
            "Install from https://go.dev/dl/"
        )
    setup_pnpm()
    if not portable:
        setup_rust()
        setup_nsis()
    build_log("[build.py] build tools ready", verbose=True)


def _rmtree_onexc(func, path, exc):
    if func in (os.rmdir, os.remove, os.unlink) and not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
        return
    raise exc


def remove_tree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, onexc=_rmtree_onexc)


def clear_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for child in path.iterdir():
        if child.is_dir():
            remove_tree(child)
        else:
            child.unlink()


def read_pyappify_config() -> dict:
    text = (PROJECT_ROOT / "pyappify.yml").read_text(encoding="utf-8")
    name_match = re.search(r'^name:\s*"?([^"\n]+)"?\s*$', text, re.MULTILINE)
    if not name_match:
        raise SystemExit("name not found in pyappify.yml")
    return {
        "name": name_match.group(1).strip(),
        "uac": re.search(r"^uac:\s*true\s*$", text, re.MULTILINE) is not None,
    }


def git_latest_tag(repo_dir: Path) -> str:
    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    tag = result.stdout.strip()
    if not tag:
        raise SystemExit("Could not determine latest git tag.")
    return tag


def read_config_version() -> str:
    config_text = (PROJECT_ROOT / "src" / "config.py").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"', config_text, re.MULTILINE)
    if match:
        version = match.group(1).strip()
        return version if version.startswith("v") else f"v{version}"
    return "v0.0.0"


def release_version_tag() -> str:
    try:
        return git_latest_tag(PROJECT_ROOT)
    except (SystemExit, subprocess.CalledProcessError):
        pass
    return read_config_version()


def sync_pyappify_project_files(config: dict, tag: str) -> None:
    app_name = LAUNCHER_NAME
    version = tag.lstrip("v")

    assets_dir = BUILD_DIR / "src-tauri" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PROJECT_ROOT / "pyappify.yml", assets_dir / "pyappify.yml")

    icons_src = PROJECT_ROOT / "icons"
    icons_dst = BUILD_DIR / "src-tauri" / "icons"
    if icons_src.is_dir():
        if icons_dst.exists():
            remove_tree(icons_dst)
        shutil.copytree(icons_src, icons_dst)

    tauri_conf = BUILD_DIR / "src-tauri" / "tauri.conf.json"
    tauri_text = tauri_conf.read_text(encoding="utf-8")
    tauri_text = tauri_text.replace('"pyappify"', json.dumps(app_name))
    tauri_text = tauri_text.replace('"0.0.1"', json.dumps(version))
    tauri_conf.write_text(tauri_text, encoding="utf-8")

    cargo_toml = BUILD_DIR / "src-tauri" / "Cargo.toml"
    cargo_text = cargo_toml.read_text(encoding="utf-8")
    cargo_toml.write_text(
        cargo_text.replace('name = "pyappify"', f'name = "{app_name}"'),
        encoding="utf-8",
    )

    if config["uac"]:
        build_rs = BUILD_DIR / "src-tauri" / "build.rs"
        build_rs.write_text(
            build_rs.read_text(encoding="utf-8").replace(
                "const UAC: bool = false;", "const UAC: bool = true;"
            ),
            encoding="utf-8",
        )


def configure_launcher_data(data_dir: Path) -> None:
    config_path = data_dir / "config" / "app_config.json"
    if not config_path.is_file():
        return
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    cfg["Update Method"] = "IGNORE_UPDATE"
    config_path.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


DIRECT_LAUNCHER_MAX_BYTES = 3_000_000


def verify_direct_launcher(dest_exe: Path) -> None:
    if not dest_exe.is_file():
        raise SystemExit(f"Missing direct launcher: {dest_exe}")
    size = dest_exe.stat().st_size
    if size > DIRECT_LAUNCHER_MAX_BYTES:
        raise SystemExit(
            f"{dest_exe.name} is {size:,} bytes (~PyAppify launcher). "
            f"Expected direct launcher (< {DIRECT_LAUNCHER_MAX_BYTES:,} bytes)."
        )
    build_log(
        f"[build.py] verified direct launcher: {display_path(dest_exe)} ({size:,} bytes)",
        verbose=True,
    )


def ensure_rsrc() -> None:
    ensure_build_path()
    if which("rsrc"):
        return
    build_log("[build.py] installing rsrc for exe icon embedding...")
    run(["go", "install", "github.com/akavel/rsrc@latest"])
    ensure_build_path()
    if not which("rsrc"):
        raise SystemExit("Failed to install rsrc (required for ok-nte.exe icon)")


def embed_launcher_icon() -> None:
    icon_ico = PROJECT_ROOT / "icons" / "icon.ico"
    syso = DIRECT_LAUNCHER_DIR / "rsrc.syso"
    if syso.is_file():
        syso.unlink()
    if not icon_ico.is_file():
        build_log("[build.py] warning: icons/icon.ico missing, ok-nte.exe will use default icon")
        return
    ensure_rsrc()
    run(["rsrc", "-ico", str(icon_ico), "-o", str(syso)], cwd=DIRECT_LAUNCHER_DIR)
    build_log(f"[build.py] embedded icon: {icon_ico.name}", verbose=True)


def build_direct_launcher(dest_exe: Path) -> None:
    if not which("go"):
        raise SystemExit(
            "Go is required to build direct ok-nte.exe launcher. "
            "Install from https://go.dev/dl/"
        )
    ensure_build_path()
    dest_exe.parent.mkdir(parents=True, exist_ok=True)
    if dest_exe.is_file():
        dest_exe.unlink()
    embed_launcher_icon()
    run(
        [
            "go",
            "build",
            "-ldflags=-s -w -H windowsgui",
            "-o",
            str(dest_exe.resolve()),
            ".",
        ],
        cwd=DIRECT_LAUNCHER_DIR,
        label="go build",
    )
    verify_direct_launcher(dest_exe)


def cleanup_pyappify_setup_artifacts(work_dir: Path, app_name: str) -> None:
    removed: list[str] = []
    for name in (SETUP_LAUNCHER_NAME, f"{app_name}-manager.exe"):
        path = work_dir / name
        if path.is_file():
            path.unlink()
            removed.append(path.name)
    for name in PYAPPIFY_RUNTIME_DIRS:
        path = work_dir / name
        if path.exists():
            remove_tree(path)
            removed.append(f"{name}/")
    working_dir = work_dir / "data" / "apps" / app_name / "working"
    for name in WORKING_USER_DATA_DIRS:
        path = working_dir / name
        if path.exists():
            remove_tree(path)
            removed.append(f"working/{name}/")
    if removed:
        build_log(f"[build.py] removed packaging artifacts: {', '.join(removed)}", verbose=True)


def scrub_working_test_artifacts(work_dir: Path, app_name: str) -> None:
    """Drop local dev/test cruft so it never ships in portable/installer."""
    working_dir = work_dir / "data" / "apps" / app_name / "working"
    if not working_dir.is_dir():
        return
    n = 0
    for dirname in WORKING_SCRUB_DIRS:
        for path in list(working_dir.rglob(dirname)):
            if path.is_dir():
                remove_tree(path)
                n += 1
    for pattern in WORKING_SCRUB_GLOBS:
        for path in list(working_dir.rglob(pattern)):
            if path.is_file():
                path.unlink(missing_ok=True)
                n += 1
    if n:
        build_log(f"[build.py] scrubbed {n} local test/cache path(s) under working/", verbose=True)


def runtime_stamp_for(app_name: str, data_dir: Path) -> str:
    py_exe = embedded_python_dir(app_name, data_dir) / "python.exe"
    if not py_exe.is_file():
        py_exe = embedded_python_dir(app_name, data_dir) / "pythonw.exe"
    if py_exe.is_file():
        st = py_exe.stat()
        return f"{st.st_size}:{int(st.st_mtime_ns)}"
    return ""


def read_runtime_stamp(data_dir: Path) -> str | None:
    stamp_path = data_dir / RUNTIME_STAMP_NAME
    if not stamp_path.is_file():
        return None
    text = stamp_path.read_text(encoding="utf-8").strip()
    return text or None


def write_runtime_stamp(data_dir: Path, stamp: str) -> None:
    (data_dir / RUNTIME_STAMP_NAME).write_text(stamp + "\n", encoding="utf-8")


def needs_full_runtime_copy(work_dir: Path, app_name: str) -> bool:
    if force_full_build():
        return True
    data_dir = work_dir / "data"
    if not runtime_data_is_valid(app_name, data_dir):
        return True
    expected = runtime_stamp_for(app_name, OFFLINE_DATA_DIR)
    if not expected:
        return True
    if read_runtime_stamp(data_dir) != expected:
        return True
    if not (work_dir / "pyappify.yml").is_file():
        return True
    return False


def embedded_python_dir(app_name: str, data_dir: Path) -> Path:
    return data_dir / "apps" / app_name / "python"


def runtime_data_is_valid(app_name: str, data_dir: Path) -> bool:
    python_dir = embedded_python_dir(app_name, data_dir)
    return (python_dir / "python.exe").is_file() or (python_dir / "pythonw.exe").is_file()


def find_cached_runtime_data(app_name: str) -> Path | None:
    if runtime_data_is_valid(app_name, OFFLINE_DATA_DIR):
        return OFFLINE_DATA_DIR
    return None


def seed_offline_runtime(app_name: str) -> None:
    if runtime_data_is_valid(app_name, OFFLINE_DATA_DIR):
        stamp = runtime_stamp_for(app_name, OFFLINE_DATA_DIR)
        if stamp and not read_runtime_stamp(OFFLINE_DATA_DIR):
            write_runtime_stamp(OFFLINE_DATA_DIR, stamp)
        if _progress:
            _progress.set_in_stage(100, detail="(已存在，略過)")
        else:
            build_log(f"[build.py] offline runtime already present: {display_path(OFFLINE_DATA_DIR)}")
        return
    if not runtime_data_is_valid(app_name, OFFLINE_SEED_DIR):
        raise SystemExit(
            "Offline runtime missing.\n"
            f"  expected: {OFFLINE_DATA_DIR}\n"
            f"  one-time seed source not found: {OFFLINE_SEED_DIR}\n"
            "Copy a complete PyAppify data/ tree into offline/data/ "
            "(apps/ok-nte/python/...)."
        )
    if not _progress:
        build_log(
            f"[build.py] seeding {display_path(OFFLINE_DATA_DIR)} "
            f"from {display_path(OFFLINE_SEED_DIR)} ..."
        )
    OFFLINE_DIR.mkdir(parents=True, exist_ok=True)
    if OFFLINE_DATA_DIR.exists():
        remove_tree(OFFLINE_DATA_DIR)
    if _progress:
        _progress.copy_tree(OFFLINE_SEED_DIR, OFFLINE_DATA_DIR)
    else:
        shutil.copytree(OFFLINE_SEED_DIR, OFFLINE_DATA_DIR)
    stamp = runtime_stamp_for(app_name, OFFLINE_DATA_DIR)
    if stamp:
        write_runtime_stamp(OFFLINE_DATA_DIR, stamp)
    if not _progress:
        build_log(f"[build.py] offline runtime ready: {display_path(OFFLINE_DATA_DIR)}")


def ensure_offline_runtime(app_name: str) -> Path:
    seed_offline_runtime(app_name)
    data_dir = find_cached_runtime_data(app_name)
    if data_dir is None:
        raise SystemExit(f"Offline runtime invalid: {OFFLINE_DATA_DIR}")
    if not read_runtime_stamp(data_dir):
        stamp = runtime_stamp_for(app_name, data_dir)
        if stamp:
            write_runtime_stamp(data_dir, stamp)
    return data_dir


def copy_runtime_data(src_data: Path, dest_work_dir: Path) -> None:
    dest_data = dest_work_dir / "data"
    if dest_data.exists():
        remove_tree(dest_data)
    if _progress:
        _progress.copy_tree(src_data, dest_data)
    else:
        shutil.copytree(src_data, dest_data)


def materialize_runtime_base(work_dir: Path, app_name: str) -> None:
    data_src = ensure_offline_runtime(app_name)
    work_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PROJECT_ROOT / "pyappify.yml", work_dir / "pyappify.yml")
    copy_runtime_data(data_src, work_dir)
    configure_launcher_data(work_dir / "data")
    stamp = runtime_stamp_for(app_name, data_src)
    if stamp:
        write_runtime_stamp(work_dir / "data", stamp)


def ensure_runtime_base(work_dir: Path, app_name: str) -> None:
    full = needs_full_runtime_copy(work_dir, app_name)
    if _progress:
        _progress.set_in_stage(0, detail="全量 runtime" if full else "增量")
    else:
        if full:
            build_log("[build.py] full runtime copy from offline/data", verbose=True)
        else:
            build_log("[build.py] incremental: reuse existing runtime base", verbose=True)
    if full:
        materialize_runtime_base(work_dir, app_name)
    else:
        shutil.copy2(PROJECT_ROOT / "pyappify.yml", work_dir / "pyappify.yml")
        configure_launcher_data(work_dir / "data")


def prepare_offline_workdir(app_name: str, work_dir: Path, *, overlay: bool = True) -> None:
    ensure_runtime_base(work_dir, app_name)
    if overlay:
        overlay_local_app_sources(work_dir, app_name)


def ensure_pyappify_source(config: dict) -> str:
    package_json = BUILD_DIR / "package.json"
    if not package_json.is_file():
        raise SystemExit(
            f"Offline installer build requires local pyappify at {BUILD_DIR}."
        )
    tag = release_version_tag()
    sync_pyappify_project_files(config, tag)
    return tag


def repo_ok_gui_dir(work_dir: Path, app_name: str) -> Path:
    return work_dir / "data" / "apps" / app_name / "repo" / "ok" / "gui"


def working_ok_gui_dir(work_dir: Path, app_name: str) -> Path:
    return work_dir / "data" / "apps" / app_name / "working" / "ok" / "gui"


def ok_gui_is_complete(gui_dir: Path) -> bool:
    return (
        (gui_dir / "qt.qrc").is_file()
        and (gui_dir / "qss" / "dark" / "stop.svg").is_file()
        and (gui_dir / "i18n" / "zh_TW.ts").is_file()
    )


def sync_working_ok_gui(work_dir: Path, app_name: str) -> Path:
    """PyAppify keeps full GUI under repo/; refresh working/ok/gui before BM patches."""
    src = repo_ok_gui_dir(work_dir, app_name)
    dest = working_ok_gui_dir(work_dir, app_name)
    if not src.is_dir() or not ok_gui_is_complete(src):
        raise SystemExit(f"Missing upstream GUI tree: {display_path(src)}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        remove_tree(dest)
    if _progress:
        _progress.set_in_stage(55, detail="sync ok/gui")
        _progress.copy_tree(src, dest)
    else:
        shutil.copytree(src, dest)
    return dest


def overlay_local_app_sources(
    work_dir: Path, app_name: str, *, kill_processes: bool = False
) -> None:
    """Replace working tree with local src/i18n (always runs on every build)."""
    if kill_processes:
        kill_app_processes(app_name, quiet=True)
    working_dir = work_dir / "data" / "apps" / app_name / "working"
    if not working_dir.is_dir():
        raise SystemExit(f"Working directory not found: {working_dir}")

    local_src = PROJECT_ROOT / "src"
    if not local_src.is_dir():
        raise SystemExit(f"Local source not found: {local_src}")

    dest_src = working_dir / "src"
    if dest_src.exists():
        remove_tree(dest_src)
    if _progress:
        _progress.set_in_stage(5, detail="src")
        _progress.copy_tree(local_src, dest_src)
    else:
        shutil.copytree(local_src, dest_src)

    for name in ("main.py", "requirements.txt", "bm_single_instance.py", "bm_github_update.py"):
        src_file = PROJECT_ROOT / name
        if src_file.is_file():
            shutil.copy2(src_file, working_dir / name)
    if _progress:
        _progress.set_in_stage(20, detail="驗證 config")

    config_path = working_dir / "src" / "config.py"
    config_text = config_path.read_text(encoding="utf-8")
    if "CharHubTab" in config_text:
        raise SystemExit(
            f"Local overlay failed: {config_path} still references CharHubTab"
        )
    if '"custom_tasks": False' not in config_text:
        raise SystemExit(
            f"Local overlay failed: {config_path} missing custom_tasks: False"
        )
    if '["src.tasks.FishingTask", "FishingTask"]' not in config_text:
        raise SystemExit(
            f"Local overlay failed: {config_path} missing FishingTask in onetime_tasks"
        )
    if '"trigger_tasks":[]' not in config_text.replace(" ", ""):
        raise SystemExit(
            f"Local overlay failed: {config_path} trigger_tasks must be empty"
        )

    local_i18n = PROJECT_ROOT / "i18n"
    if local_i18n.is_dir():
        dest_i18n = working_dir / "i18n"
        if dest_i18n.exists():
            remove_tree(dest_i18n)
        if _progress:
            _progress.set_in_stage(40, detail="i18n")
            _progress.copy_tree(local_i18n, dest_i18n)
        else:
            shutil.copytree(local_i18n, dest_i18n)
        run(
            [sys.executable, str(PROJECT_ROOT / "tools" / "compile_mo.py"), str(dest_i18n)],
            label="compile_mo",
            time_tick=True,
        )

    gui_dir = sync_working_ok_gui(work_dir, app_name)
    if _progress:
        _progress.set_in_stage(70, detail="patch gui")
    run(
        [sys.executable, str(PROJECT_ROOT / "tools" / "patch_gui_i18n.py"), str(gui_dir)],
        label="patch_gui",
        time_tick=True,
    )

    if _progress:
        _progress.set_in_stage(100)
    else:
        build_log(f"[build.py] overlaid local sources → {display_path(working_dir)}")


def finalize_package_tree(work_dir: Path, app_name: str) -> None:
    cleanup_pyappify_setup_artifacts(work_dir, app_name)
    scrub_working_test_artifacts(work_dir, app_name)


def package_global_portable(runtime_id: str) -> Path:
    exe_name = launcher_exe_name()
    output_exe = DIST_PORTABLE_DIR / exe_name
    DIST_PORTABLE_DIR.mkdir(parents=True, exist_ok=True)

    if _progress:
        with _progress.step():
            ensure_runtime_base(DIST_PORTABLE_DIR, runtime_id)
        with _progress.step():
            overlay_local_app_sources(DIST_PORTABLE_DIR, runtime_id)
        with _progress.step():
            finalize_package_tree(DIST_PORTABLE_DIR, runtime_id)
        with _progress.step():
            build_direct_launcher(output_exe)
    else:
        ensure_runtime_base(DIST_PORTABLE_DIR, runtime_id)
        overlay_local_app_sources(DIST_PORTABLE_DIR, runtime_id)
        finalize_package_tree(DIST_PORTABLE_DIR, runtime_id)
        build_direct_launcher(output_exe)
        build_log(f"[build.py] portable ready: {display_path(output_exe)}")

    return output_exe


def package_global_setup(runtime_id: str) -> Path:
    exe_name = launcher_exe_name()
    launcher_src = BUILD_DIR / "src-tauri" / "target" / "release" / exe_name
    launcher_src.parent.mkdir(parents=True, exist_ok=True)
    output_name = f"bm-ok-nte-win32-global-setup-{read_config_version()}.exe"
    output_path = DIST_DIR / output_name
    tauri_root = BUILD_DIR / "src-tauri"

    def prepare_tauri_payload() -> None:
        ensure_runtime_base(tauri_root, runtime_id)
        overlay_local_app_sources(tauri_root, runtime_id)
        finalize_package_tree(tauri_root, runtime_id)

    if _progress:
        with _progress.step():
            prepare_tauri_payload()
        with _progress.step():
            build_direct_launcher(launcher_src)
        with _progress.step():
            run(
                ["pnpm", "tauri", "bundle"],
                cwd=BUILD_DIR,
                label="tauri bundle",
                hints=TAURI_BUNDLE_HINTS,
                time_tick=True,
            )
            verify_direct_launcher(launcher_src)
        with _progress.step():
            nsis_dir = BUILD_DIR / "src-tauri" / "target" / "release" / "bundle" / "nsis"
            installers = sorted(nsis_dir.glob("*.exe"))
            if not installers:
                raise SystemExit(f"No NSIS installer found in {nsis_dir}")
            shutil.copy2(installers[0], output_path)
    else:
        prepare_tauri_payload()
        build_direct_launcher(launcher_src)
        run(["pnpm", "tauri", "bundle"], cwd=BUILD_DIR)
        verify_direct_launcher(launcher_src)
        nsis_dir = BUILD_DIR / "src-tauri" / "target" / "release" / "bundle" / "nsis"
        installers = sorted(nsis_dir.glob("*.exe"))
        if not installers:
            raise SystemExit(f"No NSIS installer found in {nsis_dir}")
        shutil.copy2(installers[0], output_path)

    return output_path


def build_installer() -> None:
    global _progress
    tag = resolve_build_tag("win10")
    _progress = BuildProgress("win10", tag=tag)
    try:
        with _progress.step():
            install_python_deps()
        with _progress.step():
            check_python()
            check_tools()
            config = read_pyappify_config()
            runtime_id = runtime_app_id(config["name"])
            kill_app_processes(runtime_id, quiet=True)
            clear_dir(DIST_DIR)
        with _progress.step():
            ensure_pyappify_source(config)
        output_path = package_global_setup(runtime_id)
        if not output_path.is_file():
            raise SystemExit(f"Missing output: {output_path}")
        _progress.finish(f"[{tag}] OK: {display_path(output_path)}")
    finally:
        _progress = None


def build_portable() -> None:
    global _progress
    tag = resolve_build_tag("win10_portable")
    _progress = BuildProgress("win10_portable", tag=tag)
    try:
        with _progress.step():
            install_python_deps()
        with _progress.step():
            check_python()
            check_tools(portable=True)
            config = read_pyappify_config()
            runtime_id = runtime_app_id(config["name"])
            kill_app_processes(runtime_id, quiet=True)
        output_path = package_global_portable(runtime_id)
        with _progress.step():
            size = verify_portable_launcher(output_path)
            _progress.set_in_stage(100, detail=f"{size:,} bytes")
        _progress.finish(f"[{tag}] OK: {display_path(DIST_PORTABLE_DIR)}")
    finally:
        _progress = None


def build(mode: str) -> None:
    if mode == "win10":
        build_installer()
    elif mode == "win10_portable":
        build_portable()
    elif mode == "seed_offline":
        global _progress
        tag = resolve_build_tag("seed_offline")
        _progress = BuildProgress("seed_offline", tag=tag)
        try:
            config = read_pyappify_config()
            with _progress.step():
                seed_offline_runtime(runtime_app_id(config["name"]))
            with _progress.step():
                _progress.set_in_stage(100)
            _progress.finish(f"[{tag}] OK: {display_path(OFFLINE_DATA_DIR)}")
        finally:
            _progress = None
    else:
        raise SystemExit(f"Unsupported build mode: {mode}")


def main() -> None:
    args = sys.argv[1:]
    quiet = False
    mode = "win10"
    for arg in args:
        if arg in ("--quiet", "-q"):
            quiet = True
        elif not arg.startswith("-"):
            mode = arg
    if quiet:
        os.environ["BUILD_QUIET"] = "1"
    build(mode)


if __name__ == "__main__":
    main()
