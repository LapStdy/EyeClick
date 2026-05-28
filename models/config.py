import json
import os
from typing import Optional

from core.path_utils import get_project_root, resolve_path
from models.task import Task


class ConfigManager:
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = os.path.join(get_project_root(), "config.json")
        self.config_path = config_path
        self.tasks: list[Task] = []
        self.task_id_counter = 0
        self.global_confidence = 0.8
        self.search_mode = "fullscreen"
        self.target_window_title: Optional[str] = None
        self.auto_close = False
        self.auto_start = False
        self.minimize_on_execute = False
        self.highlight_match = True
        self.log_level = "info"

    def to_dict(self) -> dict:
        return {
            "tasks": [t.to_dict() for t in self.tasks],
            "task_id_counter": self.task_id_counter,
            "global_confidence": self.global_confidence,
            "search_mode": self.search_mode,
            "target_window_title": self.target_window_title,
            "auto_close": self.auto_close,
            "auto_start": self.auto_start,
            "minimize_on_execute": self.minimize_on_execute,
            "highlight_match": self.highlight_match,
            "log_level": self.log_level,
        }

    def load(self):
        if not os.path.exists(self.config_path):
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
            self.task_id_counter = data.get("task_id_counter", len(self.tasks))
            self.global_confidence = data.get("global_confidence", 0.8)
            self.search_mode = data.get("search_mode", "fullscreen")
            self.target_window_title = data.get("target_window_title")
            self.auto_close = data.get("auto_close", False)
            self.auto_start = data.get("auto_start", False)
            self.minimize_on_execute = data.get("minimize_on_execute", False)
            self.highlight_match = data.get("highlight_match", True)
            self.log_level = data.get("log_level", "info")
        except Exception as e:
            print(f"加载配置失败: {e}")

    def save(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")

    @staticmethod
    def validate_task(task: Task) -> list[str]:
        errors = []
        if task.task_type not in ("left_click", "right_click", "wait"):
            errors.append(f"无效的指令类型: {task.task_type}")
        if task.countdown < 0:
            errors.append("倒计时不能为负数")
        if task.task_type != "wait":
            if not task.template_path:
                errors.append("点击指令必须绑定模板文件")
            elif not os.path.exists(resolve_path(task.template_path)):
                errors.append(f"模板文件不存在: {task.template_path}")
        if not 0.0 <= task.confidence_threshold <= 1.0:
            errors.append("置信度阈值必须在 0.0 ~ 1.0 之间")
        if task.match_scale < 0:
            errors.append("匹配缩放因子不能为负数")
        if task.wait_duration < 0:
            errors.append("等待时长不能为负数")
        if task.max_retries < 0:
            errors.append("重试次数不能为负数")
        if task.retry_interval < 0:
            errors.append("重试间隔不能为负数")
        return errors
