from core.dpi_helper import enable_dpi_awareness
from ui.main_window import App


def main():
    enable_dpi_awareness()
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
