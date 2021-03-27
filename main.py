import pygame
from threading import Lock
from library.contants import Values, Colors
from library.elements import DrawBoard, Player
from library.ui import Menu

menu = Menu()

if menu.isQuit:
    exit(0)

pygame.init()
pygame.display.set_caption("skrable")

mainWindow = pygame.display.set_mode(Values.SIZE_MW)
clock = pygame.time.Clock()
lock = Lock()

drawBoard = DrawBoard(
    window=pygame.surface.Surface(Values.SIZE_DB),
    brushSizes=Values.SIZE_BRUSHES,
    brushColors=Colors.getAllColors()
)


def update():
    mainWindow.blit(drawBoard.window, Values.POINT_DB)
    pygame.display.update()


def drawLoop():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit(0)

        if event.type == pygame.MOUSEBUTTONDOWN:
            buttons = pygame.mouse.get_pressed(3)
            if buttons[0]:
                drawBoard.setModeToInk()
                if drawBoard.last_position is None:
                    drawBoard.last_position = pygame.mouse.get_pos()
                drawBoard.isDrawing = True
            elif buttons[1]:
                drawBoard.setModeToEraser()
                if drawBoard.last_position is None:
                    drawBoard.last_position = pygame.mouse.get_pos()
                drawBoard.isDrawing = True

        if drawBoard.isDrawing and event.type == pygame.MOUSEMOTION:
            pos = pygame.mouse.get_pos()
            drawBoard.draw(drawBoard.last_position, pos)
            drawBoard.last_position = pos

        if event.type == pygame.MOUSEBUTTONUP:
            drawBoard.last_position = None
            drawBoard.isDrawing = False


def guessLoop():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit(0)
        if event.type == pygame.KEYDOWN:
            pass

    with lock:
        pc = drawBoard.pendingCoordinates
        if len(pc) > 1:
            for i in range(len(pc)-1):
                drawBoard.draw(pc[0], pc[1])
                pc.pop(0)

        if pc and not drawBoard.isDrawing:
            drawBoard.clearPendingCoordinates()


def run(loop):
    while True:
        clock.tick(Values.FRAMERATE)
        loop()
        update()


if __name__ == '__main__':
    player = Player(menu.playerName)
    gameFound = drawBoard.findGame(menu.gameCode, "host" if menu.isHost else "join")

    if gameFound:
        drawBoard.isTurn = menu.isHost
        drawBoard.gameCode = menu.gameCode
        drawBoard.start()

    if drawBoard.isTurn:
        run(drawLoop)
    else:
        run(guessLoop)
