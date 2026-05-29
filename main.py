import sys

from core.dpi_helper import enable_dpi_awareness
from core.path_utils import ensure_template_dirs
from ui.main_window import App


def main():
    enable_dpi_awareness()
    try:
        ensure_template_dirs()
    except OSError as e:
        from tkinter import messagebox
        messagebox.showerror("目录初始化失败", str(e))
        sys.exit(1)
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
