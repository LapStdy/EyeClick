import time
from pynput import mouse


class MouseController:
    def __init__(self):
        self.controller = mouse.Controller()

    def click_left(self, x: int, y: int):
        self.controller.position = (x, y)
        time.sleep(0.05)
        self.controller.click(mouse.Button.left, 1)

    def click_right(self, x: int, y: int):
        self.controller.position = (x, y)
        time.sleep(0.05)
        self.controller.click(mouse.Button.right, 1)
