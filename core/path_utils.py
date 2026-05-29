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


def ensure_template_dirs() -> list[str]:
    sub_dirs = ["long", "short"]
    base = os.path.join(get_project_root(), "templates")
    created = []

    try:
        if not os.path.isdir(base):
            os.makedirs(base, exist_ok=True)
            created.append(base)

        for name in sub_dirs:
            path = os.path.join(base, name)
            if not os.path.isdir(path):
                os.makedirs(path, exist_ok=True)
                created.append(path)

        for name in ["", *sub_dirs]:
            path = os.path.join(get_project_root(), "templates", name)
            if not os.path.isdir(path):
                raise OSError(f"目录创建后验证失败: {path}")

        return created
    except OSError as e:
        raise OSError(f"无法创建模板目录结构: {e}")
