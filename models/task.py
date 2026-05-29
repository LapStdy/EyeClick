from typing import Optional


class Task:
    def __init__(
        self,
        task_id: int = 0,
        task_type: str = "left_click",
        countdown: float = 2.0,
        template_path: str = "",
        confidence_threshold: float = 0.8,
        match_scale: float = 0.0,
        click_offset_x: int = 0,
        click_offset_y: int = 0,
        click_x: Optional[int] = None,
        click_y: Optional[int] = None,
        search_region: Optional[tuple] = None,
        wait_duration: float = 0.0,
        max_retries: int = 1,
        retry_interval: float = 0.5,
    ):
        self.id = task_id
        self.task_type = task_type
        self.countdown = countdown
        self.template_path = template_path
        self.confidence_threshold = confidence_threshold
        self.match_scale = match_scale
        self.click_offset_x = click_offset_x
        self.click_offset_y = click_offset_y
        self.click_x = click_x
        self.click_y = click_y
        self.search_region = search_region
        self.wait_duration = wait_duration
        self.max_retries = max_retries
        self.retry_interval = retry_interval

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "task_type": self.task_type,
            "countdown": self.countdown,
            "template_path": self.template_path,
            "confidence_threshold": self.confidence_threshold,
            "match_scale": self.match_scale,
            "click_offset_x": self.click_offset_x,
            "click_offset_y": self.click_offset_y,
            "search_region": self.search_region,
            "wait_duration": self.wait_duration,
            "max_retries": self.max_retries,
            "retry_interval": self.retry_interval,
        }
        if self.click_x is not None and self.click_y is not None:
            d["click_x"] = self.click_x
            d["click_y"] = self.click_y
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            task_id=data.get("id", 0),
            task_type=data.get("task_type", "left_click"),
            countdown=data.get("countdown", 2.0),
            template_path=data.get("template_path", ""),
            confidence_threshold=data.get("confidence_threshold", 0.8),
            match_scale=data.get("match_scale", 0.0),
            click_offset_x=data.get("click_offset_x", 0),
            click_offset_y=data.get("click_offset_y", 0),
            click_x=data.get("click_x"),
            click_y=data.get("click_y"),
            search_region=data.get("search_region"),
            wait_duration=data.get("wait_duration", 0.0),
            max_retries=data.get("max_retries", 1),
            retry_interval=data.get("retry_interval", 0.5),
        )

    def get_type_display(self) -> str:
        display_map = {
            "left_click": "左键点击",
            "right_click": "右键点击",
            "wait": "等待",
        }
        return display_map.get(self.task_type, self.task_type)
