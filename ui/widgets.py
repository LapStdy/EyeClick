import time
import tkinter as tk
from tkinter import ttk


class ConfidenceScale(ttk.Frame):
    def __init__(self, parent, label_text="置信度阈值:", default=0.8, **kwargs):
        super().__init__(parent, **kwargs)
        self.value = tk.DoubleVar(value=default)

        ttk.Label(self, text=label_text).pack(side=tk.LEFT, padx=(0, 5))

        self.scale = ttk.Scale(
            self,
            from_=0.0,
            to=1.0,
            variable=self.value,
            orient=tk.HORIZONTAL,
            length=150,
            command=self._on_scale,
        )
        self.scale.pack(side=tk.LEFT, padx=5)

        self.value_label = ttk.Label(self, text=f"{default:.2f}", width=5)
        self.value_label.pack(side=tk.LEFT, padx=2)

    def _on_scale(self, *args):
        self.value_label.config(text=f"{self.value.get():.2f}")

    def get(self) -> float:
        return round(self.value.get(), 2)

    def set(self, val: float):
        self.value.set(val)
        self.value_label.config(text=f"{val:.2f}")


class TemplatePreview(ttk.Label):
    def __init__(self, parent, width=160, height=80, **kwargs):
        super().__init__(
            parent,
            text="无模板",
            relief=tk.SUNKEN,
            anchor=tk.CENTER,
            width=width // 8,
            **kwargs,
        )
        self._width = width
        self._height = height
        self._photo = None

    def set_image(self, photo):
        self._photo = photo
        self.config(image=photo, text="", compound=tk.NONE)

    def clear(self):
        self._photo = None
        self.config(image="", text="无模板")


class LogWidget(tk.Frame):
    def __init__(self, parent, height=6, **kwargs):
        super().__init__(parent, **kwargs)
        self.text = tk.Text(self, height=height, wrap=tk.WORD, state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)

        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def log(self, msg):
        self.text.configure(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        self.text.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.text.see(tk.END)
        self.text.configure(state=tk.DISABLED)

    def clear(self):
        self.text.configure(state=tk.NORMAL)
        self.text.delete(1.0, tk.END)
        self.text.configure(state=tk.DISABLED)


class DraggableTreeview(ttk.Treeview):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._drag_data = {"item": None, "start_y": 0}
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _on_press(self, event):
        region = self.identify_region(event.x, event.y)
        if region == "heading":
            return
        item = self.identify_row(event.y)
        if item:
            self._drag_data["item"] = item
            self._drag_data["start_y"] = event.y

    def _on_drag(self, event):
        if not self._drag_data["item"]:
            return
        item = self.identify_row(event.y)
        if item and item != self._drag_data["item"]:
            self.move(item, self.parent(item), self.index(self._drag_data["item"]))

    def _on_release(self, event):
        self._drag_data["item"] = None
