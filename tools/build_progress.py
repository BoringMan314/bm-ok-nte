"""Simple stage progress for build.py (reliable on Windows cmd)."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path

BAR_WIDTH = 20

PROFILES: dict[str, list[tuple[str, int]]] = {
    "seed_offline": [
        ("複製 seed → offline/data", 92),
        ("完成", 8),
    ],
    "win10_portable": [
        ("安裝 Python 依賴", 3),
        ("檢查 Python 與工具", 5),
        ("準備 runtime 基底", 38),
        ("覆寫本地 src / i18n", 34),
        ("清理打包排除項", 4),
        ("編譯 launcher (Go)", 7),
        ("驗證 launcher", 9),
    ],
    "win10": [
        ("安裝 Python 依賴", 3),
        ("檢查 Python 與工具", 5),
        ("同步 PyAppify 設定", 3),
        ("準備 runtime 與 overlay", 38),
        ("編譯 launcher (Go)", 6),
        ("pnpm tauri bundle", 36),
        ("輸出安裝包", 9),
    ],
    "win10_zip": [
        ("壓縮 portable zip", 100),
    ],
}

MODE_TAGS: dict[str, str] = {
    "win10_portable": "build_win10_portable",
    "win10": "build_win10",
    "seed_offline": "seed_offline",
    "win10_zip": "build_win10_zip",
}


def resolve_build_tag(mode: str) -> str:
    explicit = os.environ.get("BUILD_TAG", "").strip()
    if explicit:
        return explicit
    return MODE_TAGS.get(mode, "build.py")


TAURI_BUNDLE_HINTS: list[tuple[re.Pattern[str], int, str]] = [
    (re.compile(r"^\s*Info\s+Target:", re.I), 5, "target"),
    (re.compile(r"Compiling", re.I), 20, "compiling"),
    (re.compile(r"Finished `release` profile", re.I), 45, "release built"),
    (re.compile(r"Built application at:", re.I), 52, "app built"),
    (re.compile(r"Bundling", re.I), 62, "bundling"),
    (re.compile(r"Running makensis", re.I), 78, "makensis"),
    (re.compile(r"Signing", re.I), 90, "signing"),
    (re.compile(r"Finished.*bundle", re.I), 98, "done"),
]


def is_quiet() -> bool:
    return os.environ.get("BUILD_QUIET", "").strip().lower() in ("1", "true", "yes")


def verbose_logs() -> bool:
    return os.environ.get("BUILD_VERBOSE", "").strip().lower() in ("1", "true", "yes")


def enable_vt_mode() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


LINE_WIDTH = 78


class BuildProgress:
    def __init__(self, profile: str | None = None, *, tag: str = "build.py") -> None:
        enable_vt_mode()
        self.tag = tag
        self.quiet = is_quiet()
        self._tty = (not self.quiet) and sys.stdout.isatty()
        self._stages: list[tuple[str, int]] = list(PROFILES.get(profile or "", []))
        self._total_weight = sum(weight for _, weight in self._stages) or 100
        self._stage_index = -1
        self._done_weight = 0
        self._in_stage_pct = 0
        self._detail = ""
        self._lock = threading.Lock()
        self._on_progress_line = False

    def log(self, message: str) -> None:
        with self._lock:
            self._clear_progress_line()
            print(message, flush=True)

    def _bar(self, pct: int) -> str:
        pct = max(0, min(100, pct))
        filled = int(BAR_WIDTH * pct / 100)
        return "*" * filled + "-" * (BAR_WIDTH - filled)

    def _overall_pct(self) -> int:
        if not self._stages or self._stage_index < 0:
            return max(0, min(100, self._in_stage_pct))
        _, weight = self._stages[self._stage_index]
        done = self._done_weight + weight * self._in_stage_pct / 100.0
        return max(0, min(100, int(done * 100 / self._total_weight)))

    def _stage_label(self) -> str:
        if 0 <= self._stage_index < len(self._stages):
            return self._stages[self._stage_index][0]
        return ""

    def _progress_text(self) -> str:
        parts = [
            f"*** {self._overall_pct():3d}%",
            f"[{self._bar(self._overall_pct())}]",
            self._stage_label(),
        ]
        if self._detail:
            parts.append(self._detail)
        text = " ".join(parts)
        return text if len(text) <= LINE_WIDTH else text[: LINE_WIDTH - 3] + "..."

    def _clear_progress_line(self) -> None:
        if not self._tty or not self._on_progress_line:
            return
        sys.stdout.write("\r" + " " * LINE_WIDTH + "\r")
        sys.stdout.flush()
        self._on_progress_line = False

    def _show_progress(self) -> None:
        if self.quiet:
            return
        if self._tty:
            line = self._progress_text().ljust(LINE_WIDTH)[:LINE_WIDTH]
            sys.stdout.write("\r" + line)
            sys.stdout.flush()
            self._on_progress_line = True
        elif verbose_logs():
            print(self._progress_text(), flush=True)

    def set_in_stage(self, pct: int, *, detail: str = "") -> None:
        with self._lock:
            self._in_stage_pct = max(self._in_stage_pct, max(0, min(100, pct)))
            if detail:
                self._detail = detail
            self._show_progress()

    @contextmanager
    def step(self, name: str | None = None):
        with self._lock:
            self._clear_progress_line()
            self._stage_index += 1
            if name and 0 <= self._stage_index < len(self._stages):
                _, weight = self._stages[self._stage_index]
                self._stages[self._stage_index] = (name, weight)
            self._in_stage_pct = 0
            self._detail = ""
            if not self.quiet and not self._tty:
                print(f"[{self.tag}] → {self._stage_label()}", flush=True)
            self._show_progress()
        try:
            yield self
        finally:
            with self._lock:
                label = self._stage_label()
                self._in_stage_pct = 100
                if 0 <= self._stage_index < len(self._stages):
                    _, weight = self._stages[self._stage_index]
                    pct = int((self._done_weight + weight) * 100 / self._total_weight)
                    self._done_weight += weight
                else:
                    pct = self._overall_pct()
                self._clear_progress_line()
                if not self.quiet:
                    print(f"[{self.tag}] {label} ({pct}%)", flush=True)

    def copy_tree(self, src: Path, dst: Path) -> None:
        src = src.resolve()
        if not src.exists():
            raise FileNotFoundError(src)
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            return
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

    def finish(self, message: str) -> None:
        with self._lock:
            self._clear_progress_line()
            if self.quiet:
                print(message, flush=True)
            elif message.rstrip().endswith("%)"):
                print(message, flush=True)
            else:
                print(f"{message} (100%)", flush=True)


def _format_cmd(resolved: list[str]) -> str:
    exe = resolved[0]
    name = Path(exe).name if exe else resolved[0]
    rest = " ".join(resolved[1:])
    return f"{name} {rest}".strip()


def _apply_hints(progress: BuildProgress, line: str, hints: list[tuple[re.Pattern[str], int, str]]) -> None:
    stripped = line.strip()
    if not stripped:
        return
    for pattern, pct, hint_detail in hints:
        if pattern.search(stripped):
            progress.set_in_stage(pct, detail=hint_detail)
            return


def run_with_progress(
    progress: BuildProgress | None,
    cmd: list[str],
    *,
    cwd: Path | None = None,
    label: str = "",
    log_cmd: bool = False,
    hints: list[tuple[re.Pattern[str], int, str]] | None = None,
    time_tick: bool = False,
) -> None:
    resolved = cmd.copy()
    exe = shutil.which(resolved[0])
    if exe:
        resolved[0] = exe
    cmd_line = _format_cmd(resolved)
    detail = label or Path(resolved[0]).name

    if progress is not None and not progress.quiet:
        progress.set_in_stage(0)

    if progress is None or progress.quiet:
        if progress is None or log_cmd or verbose_logs():
            print(f"[build.py] {cmd_line}", flush=True)
        subprocess.run(resolved, cwd=cwd, check=True)
        return

    if log_cmd or verbose_logs():
        progress.log(f"[build.py] {cmd_line}")

    inherit = verbose_logs()
    track = (hints or time_tick) and not inherit

    if not track:
        try:
            subprocess.run(
                resolved,
                cwd=cwd,
                check=True,
                stdout=None if inherit else subprocess.DEVNULL,
                stderr=None if inherit else subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as exc:
            progress.log(f"[build.py] failed ({exc.returncode}): {cmd_line}")
            raise
        progress.set_in_stage(100)
        return

    proc = subprocess.Popen(
        resolved,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    output_lines: list[str] = []
    stop_ticker = threading.Event()

    def read_stdout() -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            output_lines.append(line)
            if hints:
                _apply_hints(progress, line, hints)

    def tick_elapsed() -> None:
        start = time.monotonic()
        while not stop_ticker.wait(2.0):
            if proc.poll() is not None:
                break
            elapsed = int(time.monotonic() - start)
            creep = min(94, max(progress._in_stage_pct, 5 + elapsed // 4))
            progress.set_in_stage(creep, detail=f"{elapsed}s")

    reader = threading.Thread(target=read_stdout, daemon=True)
    ticker: threading.Thread | None = None
    reader.start()
    if time_tick:
        ticker = threading.Thread(target=tick_elapsed, daemon=True)
        ticker.start()

    code = proc.wait()
    stop_ticker.set()
    reader.join(timeout=5)
    if ticker is not None:
        ticker.join(timeout=2)

    if code != 0:
        progress.log(f"[build.py] failed ({code}): {cmd_line}")
        tail = "".join(output_lines[-20:]).strip()
        if tail:
            for log_line in tail.splitlines():
                progress.log(log_line)
        raise subprocess.CalledProcessError(code, resolved)

    progress.set_in_stage(100)
