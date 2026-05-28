import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

from core.screen_capture import ScreenCapture


class RegionSelectDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.result = None
        self._capture = ScreenCapture()
        self._full_screenshot = None
        self._full_photo = None
        self._rect = None
        self._start_x = None
        self._start_y = None
        self._canvas_image = None
        self._rect_id = None

        self._main_window = self._find_main_window()

        self.setup_ui()
        self.transient(parent)
        self.grab_set()
        self.geometry("700x550+{}+{}".format(
            parent.winfo_x() + 50, parent.winfo_y() + 50
        ))
        self._take_screenshot()
        self.wait_window()

    def _find_main_window(self):
        root = self
        while root.master:
            root = root.master
        return root if hasattr(root, 'withdraw') else None

    def setup_ui(self):
        self.title("框选识别区域")

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        info_label = ttk.Label(
            main_frame,
            text="在下方截图上按住鼠标左键拖拽，框选要识别的区域，松开完成选择",
            foreground="blue",
        )
        info_label.pack(anchor=tk.W, pady=(0, 5))

        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg="gray", cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=5)

        self.size_label = ttk.Label(info_frame, text="选区: 无")
        self.size_label.pack(side=tk.LEFT, padx=5)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="重新截取", command=self._take_screenshot).pack(
            side=tk.LEFT, padx=10
        )
        self.confirm_btn = ttk.Button(
            btn_frame, text="确认区域", command=self._on_confirm, state=tk.DISABLED
        )
        self.confirm_btn.pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", command=self.destroy).pack(
            side=tk.LEFT, padx=10
        )

    def _take_screenshot(self):
        self.update_idletasks()
        self._saved_canvas_size = (
            max(self.canvas.winfo_width(), 660),
            max(self.canvas.winfo_height(), 360),
        )
        if self._main_window:
            self._main_window.withdraw()
        self.withdraw()
        self.after(300, self._do_capture)

    def destroy(self):
        if self._main_window:
            self._main_window.deiconify()
        super().destroy()

    def _do_capture(self):
        try:
            pil_img = self._capture.capture_to_pil()
            canvas_width, canvas_height = self._saved_canvas_size

            img_width, img_height = pil_img.size
            scale = min(
                canvas_width / img_width, canvas_height / img_height, 1.0
            )

            display_width = max(int(img_width * scale), 1)
            display_height = max(int(img_height * scale), 1)

            resized = pil_img.resize((display_width, display_height), Image.LANCZOS)
            self._full_photo = ImageTk.PhotoImage(resized)
            self._full_screenshot = pil_img
            self._scale = scale

            self.canvas.delete("all")
            self._canvas_image = self.canvas.create_image(
                canvas_width // 2, canvas_height // 2,
                image=self._full_photo,
                anchor=tk.CENTER,
            )

            self._rect = None
            self.size_label.config(text="选区: 无")
            self.confirm_btn.config(state=tk.DISABLED)

            self.deiconify()
        except Exception as e:
            messagebox.showerror("截图失败", f"截图时出错: {e}", parent=self)
            self.deiconify()

    def _on_press(self, event):
        self._start_x = event.x
        self._start_y = event.y
        if self._rect_id:
            self.canvas.delete(self._rect_id)
            self._rect_id = None

    def _on_drag(self, event):
        if self._start_x is None:
            return
        if self._rect_id:
            self.canvas.delete(self._rect_id)
        self._rect_id = self.canvas.create_rectangle(
            self._start_x, self._start_y, event.x, event.y,
            outline="red", width=2, dash=(4, 2),
        )

    def _on_release(self, event):
        if self._start_x is None:
            return

        x1, y1 = min(self._start_x, event.x), min(self._start_y, event.y)
        x2, y2 = max(self._start_x, event.x), max(self._start_y, event.y)

        if x2 - x1 < 5 or y2 - y1 < 5:
            self._start_x = None
            self._start_y = None
            return

        self._rect = (x1, y1, x2, y2)

        canvas_center_x = self.canvas.winfo_width() // 2
        canvas_center_y = self.canvas.winfo_height() // 2

        if self._canvas_image:
            bbox = self.canvas.bbox(self._canvas_image)
            if bbox:
                img_left, img_top = bbox[0], bbox[1]
            else:
                img_left = canvas_center_x - self._full_photo.width() // 2
                img_top = canvas_center_y - self._full_photo.height() // 2
        else:
            img_left = 0
            img_top = 0

        sx1 = int((x1 - img_left) / self._scale)
        sy1 = int((y1 - img_top) / self._scale)
        sx2 = int((x2 - img_left) / self._scale)
        sy2 = int((y2 - img_top) / self._scale)

        self._source_rect = (sx1, sy1, sx2, sy2)
        self.size_label.config(text=f"选区: {sx2-sx1}×{sy2-sy1}  位置: ({sx1}, {sy1}) → ({sx2}, {sy2})")
        self.confirm_btn.config(state=tk.NORMAL)
        self._start_x = None
        self._start_y = None

    def _on_confirm(self):
        if not self._source_rect:
            return
        self.result = {"region": self._source_rect}
        self.destroy()
