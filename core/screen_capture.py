from typing import Optional, Tuple

import mss
import numpy as np
from PIL import Image


class ScreenCapture:
    def __init__(self):
        self._sct = mss.mss()

    def capture_fullscreen(self) -> np.ndarray:
        monitor = self._sct.monitors[1]
        screenshot = self._sct.grab(monitor)
        img = np.array(screenshot)
        return img[:, :, :3]

    def capture_region(self, region: Tuple[int, int, int, int]) -> np.ndarray:
        left, top, right, bottom = region
        monitor = {
            "left": int(left),
            "top": int(top),
            "width": max(1, int(right - left)),
            "height": max(1, int(bottom - top)),
        }
        screenshot = self._sct.grab(monitor)
        img = np.array(screenshot)
        return img[:, :, :3]

    def capture_to_pil(self, region: Optional[Tuple[int, int, int, int]] = None) -> Image.Image:
        arr = self.capture_region(region) if region else self.capture_fullscreen()
        return Image.fromarray(arr[:, :, ::-1])

    @staticmethod
    def crop_template(image: Image.Image, rect: Tuple[int, int, int, int]) -> Image.Image:
        return image.crop(rect)
