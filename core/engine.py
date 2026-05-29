import threading
import time
from typing import Callable

import cv2
import numpy as np

from typing import Optional

from core.image_matcher import ImageMatcher
from core.path_utils import resolve_path
from core.screen_capture import ScreenCapture
from core.mouse_controller import MouseController
from core.window_manager import TargetWindow
from models.task import Task


class ExecutionEngine:
    def __init__(
        self,
        log_callback: Callable,
        progress_callback: Callable,
        status_callback: Callable,
        highlight_callback: Callable = None,
    ):
        self.matcher = ImageMatcher()
        self.capture = ScreenCapture()
        self.mouse = MouseController()
        self.log = log_callback
        self.progress = progress_callback
        self.status = status_callback
        self.highlight = highlight_callback
        self.stop_flag = False
        self.is_running = False
        self.target_window: Optional[TargetWindow] = None

    def execute(self, tasks: list[Task]):
        self.is_running = True
        self.stop_flag = False
        threading.Thread(target=self._run, args=(tasks,), daemon=True).start()

    def stop(self):
        self.stop_flag = True

    def _run(self, tasks: list[Task]):
        total = len(tasks)
        try:
            for i, task in enumerate(tasks):
                if self.stop_flag:
                    self.log("用户停止执行")
                    break

                self.status(f"执行中: 第 {i+1}/{total} 个指令")
                self.progress(i + 1, total)

                self._do_countdown(task.countdown)
                if self.stop_flag:
                    break

                if task.task_type == "wait":
                    self._execute_wait(task)
                elif task.task_type in ("left_click", "right_click"):
                    self._execute_click(task)
                else:
                    self.log(f"未知指令类型: {task.task_type}")

            if not self.stop_flag:
                self.status("全部指令执行完成")
        except Exception as e:
            self.log(f"执行异常: {e}")
        finally:
            self.is_running = False

    def _do_countdown(self, seconds: float):
        start = time.monotonic()
        while time.monotonic() - start < seconds and not self.stop_flag:
            time.sleep(0.05)

    def _execute_wait(self, task: Task):
        self.log(f"等待 {task.wait_duration} 秒...")
        elapsed = 0.0
        while elapsed < task.wait_duration and not self.stop_flag:
            time.sleep(0.1)
            elapsed += 0.1

    def _execute_click(self, task: Task):
        template = self._load_template(task.template_path)
        if template is None:
            self.log(f"错误: 无法加载模板 {task.template_path}")
            return

        self.matcher.confidence_threshold = task.confidence_threshold
        screenshot, region_offset_x, region_offset_y = self._capture_screen(task)

        scales = None
        if task.match_scale > 0:
            scales = [task.match_scale]

        result = None
        for attempt in range(task.max_retries + 1):
            result = self.matcher.match_template(
                screenshot, template, scales=scales
            )
            if result is not None:
                break
            if attempt < task.max_retries:
                self.log(
                    f"匹配失败，{task.retry_interval}秒后重试 ({attempt+1}/{task.max_retries})"
                )
                time.sleep(task.retry_interval)
                screenshot, region_offset_x, region_offset_y = self._capture_screen(task)

        if result is None:
            self.log(f"错误: 模板匹配失败，置信度低于阈值")
            return

        cx, cy, conf = result
        screen_x = cx + region_offset_x
        screen_y = cy + region_offset_y

        if task.click_x is not None and task.click_y is not None:
            click_x, click_y = task.click_x, task.click_y
            pos_label = f"预设坐标({click_x}, {click_y})"
        else:
            click_x = screen_x + task.click_offset_x
            click_y = screen_y + task.click_offset_y
            pos_label = f"偏移({click_x}, {click_y})"

        self.log(
            f"匹配成功: 位置({screen_x}, {screen_y}) 置信度{conf:.2%} → {pos_label}"
        )

        if self.highlight:
            self.highlight((screen_x, screen_y), conf)

        if task.task_type == "left_click":
            self.mouse.click_left(click_x, click_y)
        else:
            self.mouse.click_right(click_x, click_y)

        time.sleep(0.2)

    def _load_template(self, path: str):
        return cv2.imread(resolve_path(path))

    def _capture_screen(self, task: Task):
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
            offset_x, offset_y = region[0], region[1]
            return self.capture.capture_region(region), offset_x, offset_y
        return self.capture.capture_fullscreen(), 0, 0
