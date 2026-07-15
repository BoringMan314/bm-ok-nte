import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable, Optional, Tuple


@dataclass
class ReleaseUpdate:
    major: int
    minor: int
    patch: int
    download_url: str


def parse_version_tag(tag: str) -> Optional[Tuple[int, int, int]]:
    t = (tag or "").strip()
    if t.lower().startswith("v"):
        t = t[1:]
    parts = t.split(".")
    if len(parts) < 2:
        return None
    try:
        major = int(parts[0])
        minor = int(parts[1])
        patch = int(parts[2]) if len(parts) >= 3 else 0
        return major, minor, patch
    except ValueError:
        return None


def parse_title_version(suffix: str) -> Tuple[int, int, int]:
    m = re.search(r"V(\d+)\.(\d+)(?:\.(\d+))?", suffix or "", re.IGNORECASE)
    if not m:
        return 1, 0, 0
    patch = int(m.group(3)) if m.group(3) else 0
    return int(m.group(1)), int(m.group(2)), patch


def is_newer(remote: Tuple[int, int, int], current: Tuple[int, int, int]) -> bool:
    return remote > current


def version_label(major: int, minor: int, patch: int) -> str:
    return f"V{major}.{minor}.{patch}"


def fetch_latest_update(
    repo: str,
    user_agent: str,
    current: Tuple[int, int, int],
    pick_asset: Callable[[str], bool],
    timeout: float = 15,
) -> Optional[ReleaseUpdate]:
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, json.JSONDecodeError, ValueError):
        return None

    tag = data.get("tag_name")
    parsed = parse_version_tag(tag) if isinstance(tag, str) else None
    if parsed is None or not is_newer(parsed, current):
        return None

    assets = data.get("assets")
    if not isinstance(assets, list):
        return None

    download_url = None
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        name = asset.get("name")
        if not isinstance(name, str) or not pick_asset(name):
            continue
        browser_url = asset.get("browser_download_url")
        if isinstance(browser_url, str) and browser_url:
            download_url = browser_url
            break

    if not download_url:
        return None

    return ReleaseUpdate(
        major=parsed[0],
        minor=parsed[1],
        patch=parsed[2],
        download_url=download_url,
    )


def build_save_path(
    app_dir: str,
    file_stem: str,
    major: int,
    minor: int,
    patch: int,
    extension: str,
) -> str:
    label = version_label(major, minor, patch)
    return os.path.join(app_dir, f"{file_stem}-{label}{extension}")


def download_release(url: str, dest_path: str, user_agent: str, timeout: float = 600) -> bool:
    if os.path.isfile(dest_path):
        return True

    temp_path = dest_path + ".download"
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            with open(temp_path, "wb") as out:
                while True:
                    chunk = resp.read(1024 * 256)
                    if not chunk:
                        break
                    out.write(chunk)
        if os.path.isfile(dest_path):
            os.remove(dest_path)
        os.replace(temp_path, dest_path)
        return True
    except (urllib.error.URLError, OSError):
        try:
            if os.path.isfile(temp_path):
                os.remove(temp_path)
        except OSError:
            pass
        return False


def make_pick_win10_exe(stem: str):
    needle = stem.lower()

    def pick(name: str) -> bool:
        lower = name.lower()
        return needle in lower and lower.endswith(".exe") and "_win7" not in lower

    return pick


def pick_ok_nte_portable_zip(name: str) -> bool:
    lower = name.lower()
    if not lower.endswith(".zip"):
        return False
    if "bm-ok-nte" not in lower:
        return False
    return "portable" in lower or "global" in lower


pick_mouse_click_win10_exe = make_pick_win10_exe("bm-mouse-click")
