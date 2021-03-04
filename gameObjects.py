global mainWindow, drawBoard


def init():
    global mainWindow, drawBoard

    import pygame
    from library.contants import Values, Colors
    from library.elements import DrawBoard

    pygame.init()
    pygame.display.set_caption("skrable")

    mainWindow = pygame.display.set_mode(Values.SIZE_MW)

    drawBoard = DrawBoard(
        window=pygame.surface.Surface(Values.SIZE_DB),
        brushSizes=Values.SIZE_BRUSHES,
        brushColors=Colors.getAllColors()
    )


init()
