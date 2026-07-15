import atexit
import sys

import bm_single_instance
from src.bm_shell import SINGLE_APP_ID, schedule_pipe_quit

_app_mutex_handle = None


def _release_app_mutex() -> None:
    global _app_mutex_handle
    bm_single_instance.release_mutex(_app_mutex_handle)
    _app_mutex_handle = None


def main() -> int:
    global _app_mutex_handle

    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    _app_mutex_handle = bm_single_instance.acquire_or_handshake(SINGLE_APP_ID)
    if not _app_mutex_handle:
        return 0

    atexit.register(_release_app_mutex)
    bm_single_instance.start_pipe_server(SINGLE_APP_ID, schedule_pipe_quit)

    import ok

    from src.config import config

    ok_app = ok.OK(config)
    ok_app.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
