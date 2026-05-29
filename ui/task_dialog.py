import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from core.path_utils import get_project_root, to_relative_path
from models.task import Task
from ui.widgets import ConfidenceScale, TemplatePreview


class TaskDialog(tk.Toplevel):
    def __init__(self, parent, task=None, template_dir="templates"):
        super().__init__(parent)
        self.task = task
        self.template_dir = template_dir
        self.result = None
        self._photo = None
        self._search_region = None
        self._click_pos = None
        self.setup_ui()

        if task:
            self.title(f"编辑指令 #{task.id}")
            self._load_task(task)
        else:
            self.title("添加指令")
            self._on_type_change()

        self.transient(parent)
        self.grab_set()
        self.geometry("480x800+{}+{}".format(
            parent.winfo_x() + 100, parent.winfo_y() + 50
        ))
        self.resizable(False, False)
        self.wait_window()

    def setup_ui(self):
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        row0 = ttk.Frame(main_frame)
        row0.pack(fill=tk.X, pady=5)
        ttk.Label(row0, text="指令类型:").pack(side=tk.LEFT)
        self.type_combo = ttk.Combobox(
            row0,
            values=["左键点击", "右键点击", "等待"],
            state="readonly",
            width=15,
        )
        self.type_combo.current(0)
        self.type_combo.pack(side=tk.LEFT, padx=10)
        self.type_combo.bind("<<ComboboxSelected>>", lambda e: self._on_type_change())

        row1 = ttk.Frame(main_frame)
        row1.pack(fill=tk.X, pady=5)
        ttk.Label(row1, text="倒计时:").pack(side=tk.LEFT)
        self.countdown_entry = ttk.Entry(row1, width=10)
        self.countdown_entry.insert(0, "2.0")
        self.countdown_entry.pack(side=tk.LEFT, padx=10)
        ttk.Label(row1, text="秒").pack(side=tk.LEFT)

        sep1 = ttk.Separator(main_frame, orient=tk.HORIZONTAL)
        sep1.pack(fill=tk.X, pady=10)

        template_frame = ttk.LabelFrame(main_frame, text="图像模板", padding=10)
        template_frame.pack(fill=tk.X, pady=5)

        preview_frame = ttk.Frame(template_frame)
        preview_frame.pack(pady=5)
        self.preview = TemplatePreview(preview_frame, width=160, height=80)
        self.preview.pack()

        btn_frame1 = ttk.Frame(template_frame)
        btn_frame1.pack(pady=5)
        self.load_btn = ttk.Button(btn_frame1, text="加载模板文件", command=self._on_load_file)
        self.load_btn.pack(side=tk.LEFT, padx=5)
        self.clear_template_btn = ttk.Button(btn_frame1, text="清除模板", command=self._on_clear_template)
        self.clear_template_btn.pack(side=tk.LEFT, padx=5)

        self.template_path_label = ttk.Label(
            template_frame, text="文件: (无)", foreground="gray"
        )
        self.template_path_label.pack(anchor=tk.W, pady=5)

        sep_region = ttk.Separator(template_frame, orient=tk.HORIZONTAL)
        sep_region.pack(fill=tk.X, pady=5)

        region_header = ttk.Frame(template_frame)
        region_header.pack(fill=tk.X, pady=2)
        ttk.Label(region_header, text="识别区域（可选）:", font=("", 9, "bold")).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Label(region_header, text="留空=全屏搜索", foreground="gray").pack(
            side=tk.LEFT, padx=5
        )

        self.region_label = ttk.Label(
            template_frame, text="未设置区域", foreground="gray"
        )
        self.region_label.pack(anchor=tk.W, pady=2)

        btn_region = ttk.Frame(template_frame)
        btn_region.pack(pady=3)
        self.region_select_btn = ttk.Button(btn_region, text="框选识别区域", command=self._on_select_region)
        self.region_select_btn.pack(side=tk.LEFT, padx=5)
        self.region_clear_btn = ttk.Button(btn_region, text="清除区域", command=self._on_clear_region)
        self.region_clear_btn.pack(side=tk.LEFT, padx=5)

        sep2 = ttk.Separator(main_frame, orient=tk.HORIZONTAL)
        sep2.pack(fill=tk.X, pady=10)

        param_frame = ttk.Frame(main_frame)
        param_frame.pack(fill=tk.X, pady=5)

        self.confidence_scale = ConfidenceScale(param_frame, "置信度阈值:", 0.8)
        self.confidence_scale.pack(fill=tk.X, pady=3)

        scale_row = ttk.Frame(param_frame)
        scale_row.pack(fill=tk.X, pady=3)
        ttk.Label(scale_row, text="匹配缩放:").pack(side=tk.LEFT)
        self.scale_entry = ttk.Entry(scale_row, width=10)
        self.scale_entry.insert(0, "0.0")
        self.scale_entry.pack(side=tk.LEFT, padx=10)
        ttk.Label(scale_row, text="(0=自动多尺度)").pack(side=tk.LEFT)

        pos_row = ttk.Frame(param_frame)
        pos_row.pack(fill=tk.X, pady=3)
        ttk.Label(pos_row, text="点击位置:").pack(side=tk.LEFT)
        self.pos_select_btn = ttk.Button(
            pos_row, text="在截图上选择", command=self._on_select_click_pos
        )
        self.pos_select_btn.pack(side=tk.LEFT, padx=10)
        self.pos_clear_btn = ttk.Button(
            pos_row, text="清除坐标", command=self._on_clear_click_pos
        )
        self.pos_clear_btn.pack(side=tk.LEFT, padx=2)

        self.pos_label = ttk.Label(
            param_frame, text="未设置（点击模板匹配中心）", foreground="gray"
        )
        self.pos_label.pack(anchor=tk.W, padx=22, pady=(0, 3))

        retry_row = ttk.Frame(param_frame)
        retry_row.pack(fill=tk.X, pady=3)
        ttk.Label(retry_row, text="最大重试:").pack(side=tk.LEFT)
        self.retry_entry = ttk.Entry(retry_row, width=8)
        self.retry_entry.insert(0, "1")
        self.retry_entry.pack(side=tk.LEFT, padx=10)
        ttk.Label(retry_row, text="次   间隔:").pack(side=tk.LEFT)
        self.retry_interval_entry = ttk.Entry(retry_row, width=8)
        self.retry_interval_entry.insert(0, "0.5")
        self.retry_interval_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(retry_row, text="秒").pack(side=tk.LEFT)

        wait_frame = ttk.LabelFrame(main_frame, text="等待设置（仅等待类型）", padding=10)
        wait_frame.pack(fill=tk.X, pady=10)

        wait_row = ttk.Frame(wait_frame)
        wait_row.pack()
        ttk.Label(wait_row, text="等待时长:").pack(side=tk.LEFT)
        self.wait_duration_entry = ttk.Entry(wait_row, width=10)
        self.wait_duration_entry.insert(0, "3.0")
        self.wait_duration_entry.pack(side=tk.LEFT, padx=10)
        ttk.Label(wait_row, text="秒").pack(side=tk.LEFT)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="确定", command=self._on_ok).pack(
            side=tk.LEFT, padx=10
        )
        ttk.Button(btn_frame, text="取消", command=self.destroy).pack(
            side=tk.LEFT, padx=10
        )

    def _on_type_change(self):
        is_wait = self.type_combo.get() == "等待"
        state = tk.DISABLED if is_wait else tk.NORMAL

        self.load_btn.configure(state=state)
        self.clear_template_btn.configure(state=state)
        self.region_select_btn.configure(state=state)
        self.region_clear_btn.configure(state=state)
        self.confidence_scale.scale.configure(state=state)
        self.scale_entry.configure(state=state)
        self.pos_select_btn.configure(state=state)
        self.pos_clear_btn.configure(state=state)
        self.retry_entry.configure(state=state)
        self.retry_interval_entry.configure(state=state)

    def _on_load_file(self):
        file_path = filedialog.askopenfilename(
            parent=self,
            title="选择模板图片",
            filetypes=[("PNG 图片", "*.png"), ("所有图片", "*.png *.jpg *.bmp")],
            initialdir=self.template_dir if os.path.exists(self.template_dir) else get_project_root(),
        )
        if not file_path:
            return

        try:
            from PIL import Image, ImageTk
            img = Image.open(file_path)
            img.thumbnail((160, 80))
            photo = ImageTk.PhotoImage(img)
            self._set_template(file_path, photo)
        except Exception as e:
            messagebox.showerror("错误", f"无法加载图片: {e}", parent=self)

    def _on_clear_template(self):
        self._template_path = ""
        self.template_path_label.config(text="文件: (无)", foreground="gray")
        self.preview.clear()

    def _set_template(self, path, photo):
        self._template_path = path
        self._photo = photo
        self.preview.set_image(photo)
        display_name = os.path.basename(path)
        self.template_path_label.config(
            text=f"文件: {display_name}", foreground="green"
        )

    def _on_select_region(self):
        from ui.template_capture import RegionSelectDialog
        dialog = RegionSelectDialog(self)
        if dialog.result:
            abs_region = dialog.result["region"]
            win_x, win_y = self._get_window_origin()
            if win_x is not None:
                rel_region = (
                    abs_region[0] - win_x,
                    abs_region[1] - win_y,
                    abs_region[2] - win_x,
                    abs_region[3] - win_y,
                )
            else:
                rel_region = abs_region
            self._search_region = rel_region
            self._update_region_display()

    def _on_clear_region(self):
        self._search_region = None
        self.region_label.config(text="未设置区域", foreground="gray")

    def _update_region_display(self):
        if self._search_region:
            r = self._search_region
            w = r[2] - r[0]
            h = r[3] - r[1]
            self.region_label.config(
                text=f"区域: ({r[0]}, {r[1]}) → ({r[2]}, {r[3]})  ({w}×{h})",
                foreground="blue",
            )
        else:
            self.region_label.config(text="未设置区域", foreground="gray")

    def _on_select_click_pos(self):
        from ui.template_capture import ClickPointSelectDialog
        dialog = ClickPointSelectDialog(self, self._click_pos)
        if dialog.result is not None:
            self._click_pos = dialog.result
            self._update_click_pos_display()

    def _on_clear_click_pos(self):
        self._click_pos = None
        self._update_click_pos_display()

    def _update_click_pos_display(self):
        if self._click_pos is not None:
            x, y = self._click_pos
            self.pos_label.config(
                text=f"坐标: ({x}, {y})", foreground="blue"
            )
        else:
            self.pos_label.config(
                text="未设置（点击模板匹配中心）", foreground="gray"
            )

    def _get_window_origin(self):
        try:
            parent = self.master
            while parent and not hasattr(parent, 'target_window'):
                parent = parent.master
            if parent and parent.target_window and parent.target_window.is_valid():
                rect = parent.target_window.get_client_rect()
                if rect:
                    return (rect[0], rect[1])
        except Exception:
            pass
        return (None, None)

    def _load_task(self, task):
        type_map = {"left_click": "左键点击", "right_click": "右键点击", "wait": "等待"}
        self.type_combo.set(type_map.get(task.task_type, task.task_type))
        self.countdown_entry.delete(0, tk.END)
        self.countdown_entry.insert(0, str(task.countdown))

        if task.template_path:
            self._template_path = task.template_path
            display_name = os.path.basename(task.template_path)
            self.template_path_label.config(
                text=f"文件: {display_name}", foreground="green"
            )
            full_path = task.template_path
            if not os.path.exists(full_path):
                full_path = os.path.join(
                    get_project_root(),
                    task.template_path,
                )
            if os.path.exists(full_path):
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(full_path)
                    img.thumbnail((160, 80))
                    self._photo = ImageTk.PhotoImage(img)
                    self.preview.set_image(self._photo)
                except Exception:
                    pass

        if task.search_region:
            self._search_region = task.search_region
            self._update_region_display()

        self.confidence_scale.set(task.confidence_threshold)
        self.scale_entry.delete(0, tk.END)
        self.scale_entry.insert(0, str(task.match_scale))
        self._click_pos = (task.click_x, task.click_y) if task.click_x is not None and task.click_y is not None else None
        self._update_click_pos_display()
        self.retry_entry.delete(0, tk.END)
        self.retry_entry.insert(0, str(task.max_retries))
        self.retry_interval_entry.delete(0, tk.END)
        self.retry_interval_entry.insert(0, str(task.retry_interval))
        self.wait_duration_entry.delete(0, tk.END)
        self.wait_duration_entry.insert(0, str(task.wait_duration))
        self._on_type_change()

    def _on_ok(self):
        try:
            type_display = self.type_combo.get()
            type_map = {"左键点击": "left_click", "右键点击": "right_click", "等待": "wait"}
            task_type = type_map.get(type_display, "left_click")

            countdown = float(self.countdown_entry.get())
            if countdown < 0 or countdown > 3600:
                messagebox.showwarning("输入错误", "倒计时必须在 0 ~ 3600 秒之间", parent=self)
                return

            if task_type == "wait":
                wait_duration = float(self.wait_duration_entry.get())
                if wait_duration < 0 or wait_duration > 86400:
                    messagebox.showwarning("输入错误", "等待时长必须在 0 ~ 86400 秒之间", parent=self)
                    return
                self.result = Task(
                    task_id=self.task.id if self.task else 0,
                    task_type=task_type,
                    countdown=countdown,
                    wait_duration=wait_duration,
                )
            else:
                if not getattr(self, "_template_path", None):
                    messagebox.showwarning("输入错误", "请选择模板图片", parent=self)
                    return

                confidence = self.confidence_scale.get()
                match_scale = float(self.scale_entry.get())
                if match_scale < 0 or match_scale > 5:
                    messagebox.showwarning("输入错误", "匹配缩放因子必须在 0 ~ 5 之间", parent=self)
                    return
                click_x, click_y = (self._click_pos if self._click_pos is not None else (None, None))
                max_retries = int(self.retry_entry.get())
                if max_retries < 0 or max_retries > 100:
                    messagebox.showwarning("输入错误", "重试次数必须在 0 ~ 100 之间", parent=self)
                    return
                retry_interval = float(self.retry_interval_entry.get())
                if retry_interval < 0 or retry_interval > 60:
                    messagebox.showwarning("输入错误", "重试间隔必须在 0 ~ 60 秒之间", parent=self)
                    return

                template_path = to_relative_path(self._template_path)

                self.result = Task(
                    task_id=self.task.id if self.task else 0,
                    task_type=task_type,
                    countdown=countdown,
                    template_path=template_path,
                    confidence_threshold=confidence,
                    match_scale=match_scale,
                    click_x=click_x,
                    click_y=click_y,
                    max_retries=max_retries,
                    retry_interval=retry_interval,
                    search_region=self._search_region,
                )

            self.destroy()
        except ValueError:
            messagebox.showwarning("输入错误", "请输入有效的数字", parent=self)
