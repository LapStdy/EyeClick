from typing import Optional, Tuple

import cv2
import numpy as np


class ImageMatcher:
    def __init__(self, confidence_threshold: float = 0.8):
        self.confidence_threshold = confidence_threshold

    def match_template(
        self,
        screenshot: np.ndarray,
        template: np.ndarray,
        threshold: Optional[float] = None,
        scales: Optional[list] = None,
    ) -> Optional[Tuple[int, int, float]]:
        if threshold is None:
            threshold = self.confidence_threshold
        if scales is None:
            scales = [0.8, 0.9, 1.0, 1.1, 1.2]

        img_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        tpl_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        tH, tW = tpl_gray.shape[:2]

        best_score = -1.0
        best_loc = None
        best_scale = 1.0

        for scale in scales:
            try:
                resized = cv2.resize(
                    tpl_gray,
                    (int(tW * scale), int(tH * scale)),
                    interpolation=cv2.INTER_AREA,
                )

                if resized.shape[0] > img_gray.shape[0] or resized.shape[1] > img_gray.shape[1]:
                    continue

                result = cv2.matchTemplate(
                    img_gray, resized, cv2.TM_CCOEFF_NORMED
                )
                _, max_val, _, max_loc = cv2.minMaxLoc(result)

                if max_val > best_score:
                    best_score = max_val
                    best_loc = max_loc
                    best_scale = scale

                if best_score > 0.99:
                    break
            except cv2.error:
                continue

        if best_score < threshold or best_loc is None:
            return None

        center_x = best_loc[0] + int(tW * best_scale) // 2
        center_y = best_loc[1] + int(tH * best_scale) // 2

        return (center_x, center_y, best_score)
