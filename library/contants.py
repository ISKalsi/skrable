class Values:
    # CAN MODIFY BELOW VALUES
    FRAMERATE = 30
    SIZE_MW = 800, 800
    __RATIO_DB_MW = 0.75, 0.90
    SIZE_BRUSHES = 5, 6, 7, 8

    # DO NOT TOUCH
    SIZE_DB = tuple(x * y for x, y in zip(SIZE_MW, __RATIO_DB_MW))
    __db_y = (SIZE_MW[1] - SIZE_DB[1]) / 2
    __db_x = SIZE_MW[0] - SIZE_DB[0] - __db_y
    POINT_DB = __db_x, __db_y


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
            if key.startswith("__"):
                continue
            colorList.append(colors[key])

        return colorList
