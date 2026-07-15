"""BM shell: tray menu, GitHub update check, title alternation, window at (100,100).

Tray strings use upstream Qt i18n (MainWindow context); patches in
i18n/gui/bm_shell_patches.json are applied at build time by patch_gui_i18n.py.
"""

from __future__ import annotations

import ctypes
import os
import sys
import threading
import webbrowser

import bm_github_update

SINGLE_APP_ID = "bm-ok-nte"
GITHUB_REPO = "BoringMan314/bm-ok-nte"
GITHUB_USER_AGENT = SINGLE_APP_ID
REPOSITORY_URL = "https://github.com/BoringMan314/bm-ok-nte"
DOWNLOAD_FILE_STEM = SINGLE_APP_ID
ABOUT_URL = "http://exnormal.com:81/"
WINDOW_POS_X = 100
WINDOW_POS_Y = 100
WINDOW_TITLE_PREFIX = "[B.M]"
WINDOW_TITLE_AUTHOR_SUFFIX = " By. [B.M] 圓周率 3.14"
UPDATE_TITLE_MS = 3000

_pipe_quit_once = False


def primary_screen_origin() -> tuple[int, int]:
    if sys.platform != "win32":
        return 0, 0
    try:
        MONITOR_DEFAULTTOPRIMARY = 1

        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            ]

        class MONITORINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", ctypes.c_ulong),
                ("rcMonitor", RECT),
                ("rcWork", RECT),
                ("dwFlags", ctypes.c_ulong),
            ]

        user32 = ctypes.windll.user32
        monitor = user32.MonitorFromPoint(POINT(0, 0), MONITOR_DEFAULTTOPRIMARY)
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        if monitor and user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
            return int(info.rcMonitor.left), int(info.rcMonitor.top)
    except Exception:
        pass
    return 0, 0


def default_window_xy() -> tuple[int, int]:
    ox, oy = primary_screen_origin()
    return ox + WINDOW_POS_X, oy + WINDOW_POS_Y


def schedule_pipe_quit() -> None:
    global _pipe_quit_once
    if _pipe_quit_once:
        return
    _pipe_quit_once = True

    def do_quit(retry: int = 0) -> None:
        try:
            from ok import og

            if getattr(og, "main_window", None) is not None:
                og.main_window.tray_quit()
                return
            if getattr(og, "app", None) is not None:
                og.app.quit()
                return
        except Exception:
            pass
        if retry < 50:
            from PySide6.QtCore import QTimer

            QTimer.singleShot(200, lambda: do_quit(retry + 1))

    try:
        from PySide6.QtCore import QCoreApplication, QTimer

        if QCoreApplication.instance() is not None:
            QTimer.singleShot(0, do_quit)
            return
    except Exception:
        pass
    do_quit()


def get_app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    root = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(root) == "src":
        return os.path.dirname(root)
    return root


def _patch_check_mutex() -> None:
    import ok.util.process as process

    if getattr(process, "_nte_bm_mutex_patch", False):
        return
    process._nte_bm_mutex_patch = True
    process.check_mutex = lambda: True


def _patch_main_window() -> None:
    from PySide6.QtCore import QEvent, QSize, Qt, QTimer
    from PySide6.QtWidgets import QMenu, QSystemTrayIcon
    from ok.gui.MainWindow import MainWindow

    if getattr(MainWindow, "_nte_bm_shell_patch", False):
        return
    MainWindow._nte_bm_shell_patch = True

    _orig_init = MainWindow.__init__
    _orig_tray_quit = MainWindow.tray_quit
    _orig_event_filter = MainWindow.eventFilter
    _orig_on_tray_icon_activated = MainWindow.on_tray_icon_activated

    def __init__(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        self._bm_update_info = None
        self._bm_update_title_alt = False
        self._bm_update_title_timer = QTimer(self)
        self._bm_update_title_timer.setInterval(UPDATE_TITLE_MS)
        self._bm_update_title_timer.timeout.connect(self._bm_update_title_tick)
        self._bm_update_downloading = False
        self._bm_update_check_started = False
        self._bm_base_title = self._bm_build_base_title()
        self._bm_rebuild_tray_menu()
        self._bm_apply_displayed_title()
        self._bm_start_update_check()

    def _bm_build_base_title(self) -> str:
        ver = (self.version or "").strip()
        return f"{WINDOW_TITLE_PREFIX} {SINGLE_APP_ID} {ver}{WINDOW_TITLE_AUTHOR_SUFFIX}"

    def _bm_build_update_title(self) -> str:
        if self._bm_update_info is None:
            return self._bm_build_base_title()
        ver = bm_github_update.version_label(
            self._bm_update_info.major,
            self._bm_update_info.minor,
            self._bm_update_info.patch,
        )
        return self.tr("New version available: {version}.").format(version=ver)

    def _bm_apply_displayed_title(self) -> None:
        if self._bm_update_info is not None and self._bm_update_title_alt:
            title = self._bm_build_update_title()
        else:
            title = self._bm_build_base_title()
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is not None:
            app.setApplicationDisplayName("")
        self.setWindowTitle(title)
        self.tray.setToolTip(title)

    def _bm_stop_update_title_alternation(self) -> None:
        self._bm_update_title_timer.stop()

    def _bm_start_update_title_alternation(self) -> None:
        self._bm_stop_update_title_alternation()
        self._bm_update_title_alt = False
        self._bm_apply_displayed_title()
        if self._bm_update_info is not None:
            self._bm_update_title_timer.start()

    def _bm_update_title_tick(self) -> None:
        if self._bm_update_info is None:
            self._bm_stop_update_title_alternation()
            return
        self._bm_update_title_alt = not self._bm_update_title_alt
        self._bm_apply_displayed_title()

    def _bm_current_app_version(self):
        return bm_github_update.parse_version_tag(self.version) or (0, 0, 0)

    def _bm_start_update_check(self) -> None:
        if self._bm_update_check_started:
            return
        self._bm_update_check_started = True
        threading.Thread(target=self._bm_update_check_worker, daemon=True).start()

    def _bm_update_check_worker(self) -> None:
        try:
            info = bm_github_update.fetch_latest_update(
                GITHUB_REPO,
                GITHUB_USER_AGENT,
                self._bm_current_app_version(),
                bm_github_update.pick_ok_nte_portable_zip,
            )
            if info is not None:
                QTimer.singleShot(0, lambda: self._bm_on_update_available(info))
        except Exception:
            pass

    def _bm_on_update_available(self, info) -> None:
        self._bm_update_info = info
        self._bm_start_update_title_alternation()
        self._bm_rebuild_tray_menu()

    def _bm_rebuild_tray_menu(self) -> None:
        menu = QMenu()
        if self._bm_update_info is not None:
            download_action = menu.addAction(self.tr("Download update"))
            download_action.setEnabled(not self._bm_update_downloading)
            download_action.triggered.connect(self._bm_download_update)
        github_action = menu.addAction("GitHub")
        github_action.triggered.connect(self._bm_open_github)
        about_action = menu.addAction(self.tr("About"))
        about_action.triggered.connect(self._bm_open_about)
        exit_action = menu.addAction(self.tr("Exit"))
        exit_action.triggered.connect(self.tray_quit)
        self.tray.setContextMenu(menu)

    def _bm_open_github(self) -> None:
        try:
            webbrowser.open(REPOSITORY_URL)
        except Exception:
            pass

    def _bm_open_about(self) -> None:
        try:
            webbrowser.open(ABOUT_URL)
        except Exception:
            pass

    def _bm_download_update(self) -> None:
        if self._bm_update_downloading or self._bm_update_info is None:
            return
        info = self._bm_update_info
        dest = bm_github_update.build_save_path(
            get_app_dir(),
            DOWNLOAD_FILE_STEM,
            info.major,
            info.minor,
            info.patch,
            ".zip",
        )
        self._bm_update_downloading = True
        self._bm_rebuild_tray_menu()

        def work() -> None:
            try:
                bm_github_update.download_release(
                    info.download_url,
                    dest,
                    GITHUB_USER_AGENT,
                )
            except Exception:
                pass
            finally:
                QTimer.singleShot(0, self._bm_finish_download_update)

        threading.Thread(target=work, daemon=True).start()

    def _bm_finish_download_update(self) -> None:
        self._bm_update_downloading = False
        self._bm_rebuild_tray_menu()

    def _bm_window_size(self) -> tuple[int, int]:
        ws = self.config.get("window_size") or {}
        return ws.get("width", 850), ws.get("height", 700)

    def _bm_restore_at_100(self) -> None:
        width, height = self._bm_window_size()
        x, y = default_window_xy()
        if self.isMinimized():
            self.showNormal()
        self.show()
        self.setWindowState(Qt.WindowNoState)
        self.setGeometry(x, y, width, height)
        self.raise_()
        self.activateWindow()
        self.bring_to_front()

    def on_tray_icon_activated(self, reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self._bm_restore_at_100()
            return
        _orig_on_tray_icon_activated(self, reason)

    def set_window_size(self, width, height, min_width=None, min_height=None):
        ws = self.config.get("window_size") or {}
        width = ws.get("width", width)
        height = ws.get("height", height)
        x, y = default_window_xy()
        self.setWindowState(Qt.WindowNoState)
        self.setMinimumSize(QSize(width, height))
        self.setMaximumSize(QSize(width, height))
        self.setFixedSize(width, height)
        self.setGeometry(x, y, width, height)
        if hasattr(self, "setResizeEnabled"):
            self.setResizeEnabled(False)
        if hasattr(self, "titleBar") and hasattr(self.titleBar, "maxBtn"):
            self.titleBar.maxBtn.hide()

    def update_ok_config(self):
        pass

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Resize, QEvent.Move):
            return False
        return _orig_event_filter(self, obj, event)

    def tray_quit(self):
        self._bm_stop_update_title_alternation()
        _orig_tray_quit(self)

    MainWindow.__init__ = __init__
    MainWindow._bm_window_size = _bm_window_size
    MainWindow._bm_build_base_title = _bm_build_base_title
    MainWindow._bm_build_update_title = _bm_build_update_title
    MainWindow._bm_apply_displayed_title = _bm_apply_displayed_title
    MainWindow._bm_stop_update_title_alternation = _bm_stop_update_title_alternation
    MainWindow._bm_start_update_title_alternation = _bm_start_update_title_alternation
    MainWindow._bm_update_title_tick = _bm_update_title_tick
    MainWindow._bm_current_app_version = _bm_current_app_version
    MainWindow._bm_start_update_check = _bm_start_update_check
    MainWindow._bm_update_check_worker = _bm_update_check_worker
    MainWindow._bm_on_update_available = _bm_on_update_available
    MainWindow._bm_rebuild_tray_menu = _bm_rebuild_tray_menu
    MainWindow._bm_open_github = _bm_open_github
    MainWindow._bm_open_about = _bm_open_about
    MainWindow._bm_download_update = _bm_download_update
    MainWindow._bm_finish_download_update = _bm_finish_download_update
    MainWindow._bm_restore_at_100 = _bm_restore_at_100
    MainWindow.on_tray_icon_activated = on_tray_icon_activated
    MainWindow.set_window_size = set_window_size
    MainWindow.update_ok_config = update_ok_config
    MainWindow.eventFilter = eventFilter
    MainWindow.tray_quit = tray_quit

    def show_notification(self, message, title=None, error=False, tray=False, show_tab=None, params=None):
        from ok import og
        from ok.gui.util.app import show_info_bar

        tr = og.app.tr
        translated_message = tr(message) if message else ""
        if params and translated_message:
            translated_message = translated_message.format(**params)
        translated_title = tr(title) if title else ""
        show_info_bar(self.window(), translated_message, translated_title, error)
        if tray:
            self.tray.showMessage(
                translated_title,
                translated_message,
                QSystemTrayIcon.Critical if error else QSystemTrayIcon.Information,
                5000,
            )
        self.navigate_tab(show_tab)

    MainWindow.show_notification = show_notification


def apply_patches() -> None:
    _patch_check_mutex()
    _patch_main_window()
