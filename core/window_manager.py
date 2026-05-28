from typing import Optional, Tuple

from .win32_api import (
    _client_to_screen,
    _enum_windows,
    _find_window,
    _get_client_rect,
    _get_cursor_pos,
    _get_window_rect,
    _get_window_text,
    _is_window,
    _is_window_visible,
)


class TargetWindow:
    def __init__(self, hwnd: int, title: str):
        self.hwnd = hwnd
        self.title = title
        self.rect = None
        self.update_rect()

    def update_rect(self) -> bool:
        try:
            if _is_window(self.hwnd):
                self.rect = _get_window_rect(self.hwnd)
                return True
            return False
        except Exception:
            return False

    def is_valid(self) -> bool:
        try:
            return _is_window(self.hwnd)
        except Exception:
            return False

    def get_client_rect(self) -> Optional[Tuple[int, int, int, int]]:
        try:
            if _is_window(self.hwnd):
                rect = _get_client_rect(self.hwnd)
                left, top = _client_to_screen(self.hwnd, (0, 0))
                return (left, top, left + rect[2], top + rect[3])
            return None
        except Exception:
            return None

    def get_rect_for_roi(self) -> Optional[Tuple[int, int, int, int]]:
        return self.get_client_rect() or self.rect


class WindowSelector:
    @staticmethod
    def get_all_windows():
        windows = []

        def enum_handler(hwnd, ctx):
            try:
                if _is_window_visible(hwnd):
                    title = _get_window_text(hwnd)
                    if title:
                        windows.append((hwnd, title))
            except Exception:
                pass

        _enum_windows(enum_handler)
        return windows

    @staticmethod
    def find_window_by_title(title: str) -> Optional[int]:
        try:
            hwnd = _find_window(None, title)
            if hwnd and _is_window(hwnd):
                return hwnd
        except Exception:
            pass
        return None

    @staticmethod
    def get_cursor_pos() -> Tuple[int, int]:
        return _get_cursor_pos()
