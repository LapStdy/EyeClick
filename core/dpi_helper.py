import ctypes

from .win32_api import _get_dpi_for_system


def enable_dpi_awareness():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDpiAware()
        except Exception:
            pass


def get_dpi_scale() -> float:
    try:
        return _get_dpi_for_system() / 96.0
    except Exception:
        try:
            return ctypes.windll.shcore.GetDpiForSystem() / 96.0
        except Exception:
            return 1.0
