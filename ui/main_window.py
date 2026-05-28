import os
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

from PIL import Image, ImageTk

from core.dpi_helper import get_dpi_scale
from core.engine import ExecutionEngine
from core.path_utils import resolve_path
from core.window_manager import TargetWindow, WindowSelector
from models.config import ConfigManager
from models.task import Task
from ui.task_dialog import TaskDialog
from ui.widgets import LogWidget, ConfidenceScale


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("EyeClick - 基于图像识别的鼠标模拟点击工具 v2.0")
        self.geometry("900x750")
        self.minsize(750, 600)

        self.config_mgr = ConfigManager()
        self.target_window = None
        self.tasks: list[Task] = []
        self.engine = ExecutionEngine(
            log_callback=self.log_message,
            progress_callback=self._on_progress,
            status_callback=self._on_status,
        )
        self.is_running = False

        self.setup_ui()
        self._load_config()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def setup_ui(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self._create_region_area(main_frame)
        self._create_task_list_area(main_frame)
        self._create_button_area(main_frame)
        self._create_control_area(main_frame)
        self._create_log_area(main_frame)
        self._create_status_area(main_frame)

    def _create_region_area(self, parent):
        frame = ttk.LabelFrame(parent, text="搜索区域设置", padding=10)
        frame.pack(fill=tk.X, pady=(0, 8))

        row1 = ttk.Frame(frame)
        row1.pack(fill=tk.X, pady=3)
        ttk.Label(row1, text="窗口选择:").pack(side=tk.LEFT, padx=5)
        self.window_combo = ttk.Combobox(row1, width=50, state="readonly")
        self.window_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(row1, text="刷新", command=self._refresh_windows).pack(
            side=tk.LEFT, padx=3
        )
        ttk.Button(row1, text="选择目标窗口", command=self._select_target_window).pack(
            side=tk.LEFT, padx=3
        )

        self.target_label = ttk.Label(
            frame, text="当前未绑定窗口", foreground="gray"
        )
        self.target_label.pack(anchor=tk.W, pady=3)

        row2 = ttk.Frame(frame)
        row2.pack(fill=tk.X, pady=3)
        ttk.Label(row2, text="全局置信度阈值:").pack(side=tk.LEFT, padx=5)

        self.global_confidence = ConfidenceScale(row2, "", 0.8)
        self.global_confidence.pack(side=tk.LEFT, padx=5)

    def _create_task_list_area(self, parent):
        frame = ttk.LabelFrame(parent, text="指令列表", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        columns = ("序号", "类型", "倒计时", "模板预览", "置信度", "偏移")
        self.task_tree = ttk.Treeview(
            frame, columns=columns, show="headings", height=8, selectmode="browse"
        )

        self.task_tree.heading("序号", text="序号")
        self.task_tree.heading("类型", text="类型")
        self.task_tree.heading("倒计时", text="倒计时")
        self.task_tree.heading("模板预览", text="模板预览")
        self.task_tree.heading("置信度", text="置信度")
        self.task_tree.heading("偏移", text="偏移")

        self.task_tree.column("序号", width=50, anchor=tk.CENTER)
        self.task_tree.column("类型", width=80, anchor=tk.CENTER)
        self.task_tree.column("倒计时", width=70, anchor=tk.CENTER)
        self.task_tree.column("模板预览", width=100, anchor=tk.CENTER)
        self.task_tree.column("置信度", width=80, anchor=tk.CENTER)
        self.task_tree.column("偏移", width=100, anchor=tk.CENTER)

        scrollbar_y = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        scrollbar_x = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=self.task_tree.xview)
        self.task_tree.configure(
            yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set
        )

        self.task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.task_tree.bind("<Double-1>", lambda e: self._edit_selected_task())

    def _create_button_area(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=(0, 8))

        btn_frame = ttk.Frame(frame)
        btn_frame.pack()

        self.add_btn = ttk.Menubutton(btn_frame, text="添加指令 ▼")
        add_menu = tk.Menu(self.add_btn, tearoff=0)
        add_menu.add_command(
            label="左键点击", command=lambda: self._add_task("left_click")
        )
        add_menu.add_command(
            label="右键点击", command=lambda: self._add_task("right_click")
        )
        add_menu.add_command(
            label="等待（无操作）", command=lambda: self._add_task("wait")
        )
        self.add_btn.configure(menu=add_menu)
        self.add_btn.pack(side=tk.LEFT, padx=3)

        ttk.Button(btn_frame, text="编辑选中", command=self._edit_selected_task).pack(
            side=tk.LEFT, padx=3
        )
        ttk.Button(btn_frame, text="删除选中", command=self._delete_selected_task).pack(
            side=tk.LEFT, padx=3
        )
        ttk.Button(btn_frame, text="上移", command=self._move_up).pack(
            side=tk.LEFT, padx=3
        )
        ttk.Button(btn_frame, text="下移", command=self._move_down).pack(
            side=tk.LEFT, padx=3
        )
        ttk.Button(btn_frame, text="清空", command=self._clear_all).pack(
            side=tk.LEFT, padx=3
        )

    def _create_control_area(self, parent):
        frame = ttk.LabelFrame(parent, text="控制选项", padding=10)
        frame.pack(fill=tk.X, pady=(0, 8))

        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X)

        self.highlight_var = tk.BooleanVar(value=True)
        self.minimize_var = tk.BooleanVar(value=False)
        self.auto_close_var = tk.BooleanVar(value=False)
        self.auto_start_var = tk.BooleanVar(value=False)

        ttk.Checkbutton(
            control_frame, text="高亮显示匹配位置", variable=self.highlight_var
        ).pack(side=tk.LEFT, padx=8)
        ttk.Checkbutton(
            control_frame, text="执行前最小化本窗口", variable=self.minimize_var
        ).pack(side=tk.LEFT, padx=8)
        ttk.Checkbutton(
            control_frame, text="完成后自动关闭", variable=self.auto_close_var
        ).pack(side=tk.LEFT, padx=8)
        ttk.Checkbutton(
            control_frame, text="启动后自动执行", variable=self.auto_start_var
        ).pack(side=tk.LEFT, padx=8)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="保存设置", command=self._save_config_now).pack(
            side=tk.LEFT, padx=5
        )

        self.start_btn = ttk.Button(
            btn_frame, text="开始执行 ▶", command=self._start_execution
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(
            btn_frame, text="停止执行 ■", command=self._stop_execution, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="测试匹配", command=self._test_match).pack(
            side=tk.LEFT, padx=5
        )

    def _create_log_area(self, parent):
        frame = ttk.LabelFrame(parent, text="执行日志", padding=10)
        frame.pack(fill=tk.X, pady=(0, 5))

        self.log_widget = LogWidget(frame, height=5)
        self.log_widget.pack(fill=tk.X)

    def _create_status_area(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X)

        status_frame = ttk.Frame(frame)
        status_frame.pack(fill=tk.X)

        ttk.Label(status_frame, text="状态:").pack(side=tk.LEFT, padx=5)
        self.status_label = ttk.Label(status_frame, text="● 就绪", foreground="green")
        self.status_label.pack(side=tk.LEFT, padx=5)

        ttk.Label(status_frame, text="|").pack(side=tk.LEFT, padx=5)
        ttk.Label(status_frame, text="进度:").pack(side=tk.LEFT, padx=5)
        self.progress_label = ttk.Label(status_frame, text="0/0")
        self.progress_label.pack(side=tk.LEFT, padx=5)

        ttk.Label(status_frame, text="|").pack(side=tk.LEFT, padx=5)
        ttk.Label(status_frame, text="当前指令:").pack(side=tk.LEFT, padx=5)
        self.current_task_label = ttk.Label(status_frame, text="—")
        self.current_task_label.pack(side=tk.LEFT, padx=5)

    def log_message(self, msg):
        self.log_widget.log(msg)

    def _on_progress(self, current, total):
        self.progress_label.config(text=f"{current}/{total}")

    def _on_status(self, text):
        self.status_label.config(text=text)
        if "完成" in text or "就绪" in text:
            self.status_label.config(foreground="green")
        elif "异常" in text or "错误" in text:
            self.status_label.config(foreground="red")
        else:
            self.status_label.config(foreground="blue")

    def _refresh_windows(self):
        windows = WindowSelector.get_all_windows()
        window_list = [
            f"{title} (hwnd:{hwnd})" for hwnd, title in windows
        ]
        self.window_combo["values"] = window_list
        if window_list:
            self.window_combo.current(0)
            self.log_message(f"已刷新窗口列表，共 {len(window_list)} 个窗口")

    def _select_target_window(self):
        selected = self.window_combo.get()
        if not selected:
            messagebox.showwarning("未选择", "请先选择一个窗口")
            return

        try:
            hwnd = int(selected.split("hwnd:")[1].rstrip(")"))
            title = selected.split(" (hwnd:")[0]
            self.target_window = TargetWindow(hwnd, title)
            if self.target_window.is_valid():
                self.target_label.config(
                    text=f"已绑定: {title}", foreground="green"
                )
                self.log_message(f"已绑定目标窗口: {title}")
                self._save_config_now()
            else:
                messagebox.showwarning("窗口无效", "选择的窗口已关闭或无效")
                self.target_window = None
                self.target_label.config(
                    text="当前未绑定窗口", foreground="gray"
                )
        except Exception as e:
            messagebox.showwarning("选择错误", f"无法解析窗口信息: {e}")

    def _add_task(self, task_type):
        task = Task(task_type=task_type)
        dialog = TaskDialog(self, task=task)
        if dialog.result:
            self.config_mgr.task_id_counter += 1
            dialog.result.id = self.config_mgr.task_id_counter
            self.tasks.append(dialog.result)
            self._refresh_task_list()
            self._save_config_now()
            self.log_message(
                f"添加指令 #{dialog.result.id}: {dialog.result.get_type_display()}"
            )

    def _edit_selected_task(self):
        selected = self.task_tree.selection()
        if not selected:
            messagebox.showwarning("未选择", "请先选择要编辑的指令")
            return

        task_index = self.task_tree.index(selected[0])
        task = self.tasks[task_index]

        dialog = TaskDialog(self, task=task)
        if dialog.result:
            dialog.result.id = task.id
            self.tasks[task_index] = dialog.result
            self._refresh_task_list()
            self._save_config_now()
            self.log_message(f"编辑指令 #{dialog.result.id}")

    def _delete_selected_task(self):
        selected = self.task_tree.selection()
        if not selected:
            messagebox.showwarning("未选择", "请先选择要删除的指令")
            return

        task_index = self.task_tree.index(selected[0])
        task_id = self.tasks[task_index].id
        del self.tasks[task_index]
        self._renumber_tasks()
        self._refresh_task_list()
        self._save_config_now()
        self.log_message(f"删除指令 #{task_id}")

    def _move_up(self):
        selected = self.task_tree.selection()
        if not selected:
            return
        idx = self.task_tree.index(selected[0])
        if idx <= 0:
            return
        self.tasks[idx], self.tasks[idx - 1] = self.tasks[idx - 1], self.tasks[idx]
        self._renumber_tasks()
        self._refresh_task_list()
        self._save_config_now()

    def _move_down(self):
        selected = self.task_tree.selection()
        if not selected:
            return
        idx = self.task_tree.index(selected[0])
        if idx >= len(self.tasks) - 1:
            return
        self.tasks[idx], self.tasks[idx + 1] = self.tasks[idx + 1], self.tasks[idx]
        self._renumber_tasks()
        self._refresh_task_list()
        self._save_config_now()

    def _clear_all(self):
        if not self.tasks:
            return
        if messagebox.askyesno("确认清空", "确定要清空所有指令吗？"):
            self.tasks.clear()
            self.config_mgr.task_id_counter = 0
            self._refresh_task_list()
            self._save_config_now()
            self.log_message("已清空所有指令")

    def _renumber_tasks(self):
        for i, task in enumerate(self.tasks):
            task.id = i + 1

    def _refresh_task_list(self):
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)

        for task in self.tasks:
            if task.task_type == "wait":
                template_display = "—"
                confidence_display = "—"
                offset_display = "—"
            else:
                template_display = os.path.basename(task.template_path) if task.template_path else "无"
                confidence_display = f"{task.confidence_threshold:.2f}"
                offset_display = f"({task.click_offset_x}, {task.click_offset_y})"

            self.task_tree.insert(
                "",
                tk.END,
                values=(
                    task.id,
                    task.get_type_display(),
                    f"{task.countdown:.1f}s",
                    template_display,
                    confidence_display,
                    offset_display,
                ),
            )

        self.progress_label.config(text=f"0/{len(self.tasks)}")

    def _start_execution(self):
        if self.is_running:
            messagebox.showwarning("执行中", "任务正在执行，请勿重复点击")
            return

        if not self.tasks:
            messagebox.showwarning("无指令", "请先添加至少一个指令")
            return

        self.is_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        if self.minimize_var.get():
            self.withdraw()

        self.log_message("=" * 50)
        self.log_message("开始执行任务...")

        self.engine.target_window = self.target_window
        self.engine.execute(self.tasks)

        threading.Thread(target=self._monitor_execution, daemon=True).start()

    def _monitor_execution(self):
        while self.engine.is_running:
            time.sleep(0.5)

        self.after(0, self._on_execution_finished)

    def _on_execution_finished(self):
        self.is_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress_label.config(text=f"{len(self.tasks)}/{len(self.tasks)}")

        if not self.engine.stop_flag:
            self.log_message("所有指令执行完成!")
            self.deiconify()

            if self.auto_close_var.get():
                self.log_message("5秒后自动关闭程序...")
                self.after(5000, self.destroy)
        else:
            self.deiconify()

        self.engine.stop_flag = False

    def _stop_execution(self):
        self.engine.stop()
        self.log_message("正在停止执行...")

    def _test_match(self):
        selected = self.task_tree.selection()
        if not selected:
            messagebox.showwarning("未选择", "请先选择一个要测试的指令")
            return

        task_index = self.task_tree.index(selected[0])
        task = self.tasks[task_index]

        if task.task_type == "wait":
            messagebox.showinfo("提示", "等待指令无需模板匹配测试")
            return

        if not task.template_path:
            messagebox.showwarning("无模板", "该指令未绑定模板")
            return

        self.log_message(f"开始测试匹配: #{task.id} {task.get_type_display()}")
        self._on_status("测试匹配中...")

        def do_test():
            try:
                import cv2
                from core.screen_capture import ScreenCapture
                from core.image_matcher import ImageMatcher

                capture = ScreenCapture()
                matcher = ImageMatcher(task.confidence_threshold)

                if task.search_region:
                    region = task.search_region
                    if self.target_window and self.target_window.is_valid():
                        win_rect = self.target_window.get_client_rect()
                        if win_rect:
                            region = (
                                win_rect[0] + region[0],
                                win_rect[1] + region[1],
                                win_rect[0] + region[2],
                                win_rect[1] + region[3],
                            )
                    screenshot = capture.capture_region(region)
                    region_offset_x, region_offset_y = region[0], region[1]
                else:
                    screenshot = capture.capture_fullscreen()
                    region_offset_x, region_offset_y = 0, 0

                template_path = resolve_path(task.template_path)

                template = cv2.imread(template_path)
                if template is None:
                    self.after(0, lambda: self.log_message(f"错误: 无法加载模板 {task.template_path}"))
                    self.after(0, lambda: self._on_status("测试失败"))
                    return

                scales = None
                if task.match_scale > 0:
                    scales = [task.match_scale]

                result = matcher.match_template(screenshot, template, scales=scales)

                if result is None:
                    self.after(
                        0,
                        lambda: self.log_message(
                            f"匹配失败: 未找到匹配结果（置信度低于 {task.confidence_threshold:.2f}）"
                        ),
                    )
                    self.after(0, lambda: self._on_status("匹配失败"))
                else:
                    cx, cy, conf = result
                    screen_x = cx + region_offset_x
                    screen_y = cy + region_offset_y
                    self.after(
                        0,
                        lambda: self.log_message(
                            f"匹配成功: 位置({screen_x}, {screen_y}) 置信度{conf:.2%}"
                        ),
                    )
                    self.after(0, lambda: self._on_status(f"匹配成功 ({conf:.0%})"))

                    result_visual = screenshot.copy()
                    tpl_h, tpl_w = template.shape[:2]
                    top_left = (cx - tpl_w // 2, cy - tpl_h // 2)
                    bottom_right = (top_left[0] + tpl_w, top_left[1] + tpl_h)
                    cv2.rectangle(
                        result_visual, top_left, bottom_right, (0, 255, 0), 2
                    )
                    cv2.circle(result_visual, (cx, cy), 5, (0, 0, 255), -1)

                    center_text = f"({screen_x}, {screen_y})"
                    cv2.putText(
                        result_visual,
                        center_text,
                        (cx + 10, cy - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2,
                    )

                    result_rgb = cv2.cvtColor(result_visual, cv2.COLOR_BGR2RGB)
                    from PIL import Image
                    pil_img = Image.fromarray(result_rgb)

                    max_display = 600
                    w, h = pil_img.size
                    if w > max_display or h > max_display:
                        scale = min(max_display / w, max_display / h)
                        pil_img = pil_img.resize(
                            (int(w * scale), int(h * scale)), Image.LANCZOS
                        )

                    photo = ImageTk.PhotoImage(pil_img)

                    self.after(0, lambda: self._show_match_result(photo, screen_x, screen_y, conf, task))

            except Exception as e:
                self.after(0, lambda: self.log_message(f"测试异常: {e}"))
                self.after(0, lambda: self._on_status("测试异常"))

        threading.Thread(target=do_test, daemon=True).start()

    def _show_match_result(self, photo, cx, cy, conf, task):
        dialog = tk.Toplevel(self)
        dialog.title(f"匹配结果 - #{task.id}")
        dialog.transient(self)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=10)
        frame.pack()

        info_text = (
            f"指令 #{task.id}: {task.get_type_display()}\n"
            f"匹配位置: ({cx}, {cy})\n"
            f"置信度: {conf:.2%}\n"
            f"阈值: {task.confidence_threshold:.2f}"
        )
        ttk.Label(frame, text=info_text, justify=tk.LEFT).pack(anchor=tk.W, pady=5)

        img_label = ttk.Label(frame)
        img_label.image = photo
        img_label.configure(image=photo)
        img_label.pack(pady=5)

        ttk.Button(frame, text="关闭", command=dialog.destroy).pack(pady=5)

        dialog.geometry(f"+{self.winfo_x() + 100}+{self.winfo_y() + 100}")

    def _save_config_now(self):
        self.config_mgr.tasks = self.tasks
        self.config_mgr.global_confidence = self.global_confidence.get()
        self.config_mgr.target_window_title = (
            self.target_window.title if self.target_window else None
        )
        self.config_mgr.auto_close = self.auto_close_var.get()
        self.config_mgr.auto_start = self.auto_start_var.get()
        self.config_mgr.minimize_on_execute = self.minimize_var.get()
        self.config_mgr.highlight_match = self.highlight_var.get()
        self.config_mgr.save()
        self.log_message("设置已保存")

    def _load_config(self):
        self.config_mgr.load()
        self.tasks = self.config_mgr.tasks
        self._renumber_tasks()
        self.global_confidence.set(self.config_mgr.global_confidence)
        self.auto_close_var.set(self.config_mgr.auto_close)
        self.auto_start_var.set(self.config_mgr.auto_start)
        self.minimize_var.set(self.config_mgr.minimize_on_execute)
        self.highlight_var.set(self.config_mgr.highlight_match)

        if self.config_mgr.target_window_title:
            hwnd = WindowSelector.find_window_by_title(
                self.config_mgr.target_window_title
            )
            if hwnd:
                self.target_window = TargetWindow(
                    hwnd, self.config_mgr.target_window_title
                )
                self.target_label.config(
                    text=f"已绑定: {self.config_mgr.target_window_title}",
                    foreground="green",
                )
            else:
                self.target_window = TargetWindow(
                    0, self.config_mgr.target_window_title
                )
                self.target_label.config(
                    text=f"已绑定: {self.config_mgr.target_window_title}（窗口未打开）",
                    foreground="orange",
                )

        if self.tasks:
            self._refresh_task_list()
            self.log_message(f"已恢复 {len(self.tasks)} 个指令")

        if (
            self.auto_start_var.get()
            and self.target_window
            and self.target_window.is_valid()
            and self.tasks
        ):
            self.after(1000, self._start_execution)

    def _on_closing(self):
        if self.is_running:
            if messagebox.askyesno("退出确认", "任务正在执行，确定要退出吗？"):
                self.engine.stop()
                self._save_config_now()
                self.destroy()
        else:
            self._save_config_now()
            self.destroy()
