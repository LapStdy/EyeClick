from typing import Callable, Optional, Tuple

import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

class _RECT(ctypes.Structure):
    _fields_ = [
        ('left', wintypes.LONG),
        ('top', wintypes.LONG),
        ('right', wintypes.LONG),
        ('bottom', wintypes.LONG),
    ]

class _POINT(ctypes.Structure):
    _fields_ = [
        ('x', wintypes.LONG),
        ('y', wintypes.LONG),
    ]

WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
EnumWindows = user32.EnumWindows
EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
EnumWindows.restype = wintypes.BOOL

IsWindow = user32.IsWindow
IsWindow.argtypes = [wintypes.HWND]
IsWindow.restype = wintypes.BOOL

IsWindowVisible = user32.IsWindowVisible
IsWindowVisible.argtypes = [wintypes.HWND]
IsWindowVisible.restype = wintypes.BOOL

FindWindowW = user32.FindWindowW
FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
FindWindowW.restype = wintypes.HWND

GetWindowRect = user32.GetWindowRect
GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(_RECT)]
GetWindowRect.restype = wintypes.BOOL

GetClientRect = user32.GetClientRect
GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(_RECT)]
GetClientRect.restype = wintypes.BOOL

ClientToScreen = user32.ClientToScreen
ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(_POINT)]
ClientToScreen.restype = wintypes.BOOL

GetCursorPos = user32.GetCursorPos
GetCursorPos.argtypes = [ctypes.POINTER(_POINT)]
GetCursorPos.restype = wintypes.BOOL

GetDpiForSystem = user32.GetDpiForSystem
GetDpiForSystem.argtypes = []
GetDpiForSystem.restype = wintypes.UINT

GetWindowTextLengthW = user32.GetWindowTextLengthW
GetWindowTextLengthW.argtypes = [wintypes.HWND]
GetWindowTextLengthW.restype = wintypes.INT

GetWindowTextW = user32.GetWindowTextW
GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, wintypes.INT]
GetWindowTextW.restype = wintypes.INT


def _enum_windows(callback: Callable[[int, int], bool]) -> bool:
    def wrapper(hwnd, lparam):
        callback(hwnd, lparam)
        return True
    c_callback = WNDENUMPROC(wrapper)
    return EnumWindows(c_callback, 0)


def _is_window(hwnd: int) -> bool:
    return bool(IsWindow(hwnd))


def _is_window_visible(hwnd: int) -> bool:
    return bool(IsWindowVisible(hwnd))


def _find_window(class_name: Optional[str], title: Optional[str]) -> Optional[int]:
    hwnd = FindWindowW(class_name, title)
    return hwnd if hwnd else None


def _get_window_text(hwnd: int) -> str:
    length = GetWindowTextLengthW(hwnd) + 1
    buffer = ctypes.create_unicode_buffer(length)
    GetWindowTextW(hwnd, buffer, length)
    return buffer.value


def _get_window_rect(hwnd: int) -> Tuple[int, int, int, int]:
    rect = _RECT()
    GetWindowRect(hwnd, ctypes.byref(rect))
    return (rect.left, rect.top, rect.right, rect.bottom)


def _get_client_rect(hwnd: int) -> Tuple[int, int, int, int]:
    rect = _RECT()
    GetClientRect(hwnd, ctypes.byref(rect))
    return (rect.left, rect.top, rect.right, rect.bottom)


def _client_to_screen(hwnd: int, point: Tuple[int, int]) -> Tuple[int, int]:
    pt = _POINT(point[0], point[1])
    ClientToScreen(hwnd, ctypes.byref(pt))
    return (pt.x, pt.y)


def _get_cursor_pos() -> Tuple[int, int]:
    pt = _POINT()
    GetCursorPos(ctypes.byref(pt))
    return (pt.x, pt.y)


def _get_dpi_for_system() -> int:
    return GetDpiForSystem()
