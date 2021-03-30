class Values:
    # CAN MODIFY BELOW VALUES
    FRAMERATE = 30
    SIZE_MAIN_WINDOW = 1270, 720
    RATIO_DB_TO_MW = 3 / 5, 6 / 9
    RATIO_PP = 2 / 3
    SIZE_BRUSHES = 5, 6, 7, 8

    PADDING = 15
    MARGINS = 3
    PADDING_WINDOW = 5

    # DO NOT TOUCH
    __SIZE_DB = [x * y for x, y in zip(SIZE_MAIN_WINDOW, RATIO_DB_TO_MW)]
    __db_y = PADDING_WINDOW + PADDING + SIZE_MAIN_WINDOW[1] * (1 - RATIO_DB_TO_MW[1]) * (1 - RATIO_PP)
    __db_x = SIZE_MAIN_WINDOW[0] * 1 / 5 + MARGINS * 2 + PADDING
    POINT_DB = __db_x, __db_y

    __db_width = __SIZE_DB[0] - 2 * (MARGINS * 2 + PADDING)
    __db_height = __SIZE_DB[1] - 2 * (MARGINS + PADDING) - PADDING_WINDOW
    SIZE_DRAW_BOARD = __db_width, __db_height


class Colors:
    BLACK = 0, 0, 0
    WHITE = 255, 255, 255
    RED = 255, 0, 0
    GREEN = 0, 255, 0
    BLUE = 0, 0, 255

    @staticmethod
    def getAllColors():
        colorList = []
        colors = Colors.__dict__
        for key in colors:
            if key.startswith("_"):
                continue
            colorList.append(colors[key])

        colorList.pop(-1)
        return colorList
