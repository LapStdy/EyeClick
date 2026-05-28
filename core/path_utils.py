import os
import sys

_PROJECT_ROOT = None


def get_project_root():
    global _PROJECT_ROOT
    if _PROJECT_ROOT is None:
        if getattr(sys, "frozen", False):
            _PROJECT_ROOT = os.path.dirname(os.path.abspath(sys.executable))
        else:
            _PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return _PROJECT_ROOT


def resolve_path(path: str) -> str:
    if os.path.isabs(path):
        return path
    return os.path.join(get_project_root(), path)


def to_relative_path(path: str) -> str:
    root = get_project_root()
    if path.startswith(root):
        return os.path.relpath(path, root)
    return path
