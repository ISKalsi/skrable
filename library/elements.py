import pygame
from library.contants import Colors, Values


class Pen:
    INK = 0
    ERASE = 1

    def __init__(self, size, color, mode=INK):
        self.size = size
        self.color = color
        self.mode = mode


class DrawBoard:
    def __init__(self, window: pygame.Surface, brushSizes, brushColors):
        self.window = window
        self.brushSizes = brushSizes
        self.brushColors = brushColors
        self.pen = Pen(brushSizes[0], brushColors[0])

        self.window.fill(Colors.WHITE)

    def draw(self, start, end):
        end = [x - y for x, y in zip(end, Values.POINT_DB)]
        start = [x - y for x, y in zip(start, Values.POINT_DB)]

        pygame.draw.line(
            surface=self.window,
            color=self.pen.color,
            start_pos=start,
            end_pos=end,
            width=self.pen.size
        )

    def setModeToInk(self):
        self.pen.mode = Pen.ERASE

    def setModeToEraser(self):
        self.pen.mode = Pen.INK

    def clearBoard(self):
        self.window.fill(Colors.WHITE)
