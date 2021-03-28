import pygame
from threading import Lock
from library.contants import Values, Colors
from library.elements import DrawBoard, Game, Player
from library.ui import StartGame, UI, DrawBoardPanel, PlayerPanel, PenPanel, GuessPanel

menu = StartGame()

if menu.isQuit:
    exit(0)

pygame.init()
pygame.display.set_caption("skrable")

mainWindow = pygame.display.set_mode(UI.size_window)
clock = pygame.time.Clock()
lock = Lock()

drawBoard = DrawBoard(
    window=pygame.surface.Surface(UI.size_drawBoard),
    brushSizes=Values.SIZE_BRUSHES,
    brushColors=Colors.getAllColors()
)

PlayerPanel()
DrawBoardPanel()
GuessPanel()
PenPanel()

game = Game(drawBoard)


def isQuit(event):
    if event.type == pygame.QUIT:
        pygame.quit()
        exit(0)


def update(dt):
    UI.manager.update(dt)
    UI.manager.draw_ui(mainWindow)

    mainWindow.blit(drawBoard.window, Values.POINT_DB)

    pygame.display.update()


def drawLoop():
    for event in pygame.event.get():
        isQuit(event)

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
            game.addToPendingCoordinates(pos)

            drawBoard.draw(drawBoard.last_position, pos)
            drawBoard.last_position = pos

        if event.type == pygame.MOUSEBUTTONUP:
            drawBoard.last_position = None
            drawBoard.isDrawing = False

        UI.manager.process_events(event)


def guessLoop():
    for event in pygame.event.get():
        isQuit(event)

        if event.type == pygame.KEYDOWN:
            pass

        UI.manager.process_events(event)

    with lock:
        pc = game.pendingCoordinates
        if len(pc) > 1:
            for i in range(len(pc)-1):
                drawBoard.draw(pc[0], pc[1])
                pc.pop(0)

        if pc and not drawBoard.isDrawing:
            pc.clear()


def run(loop):
    while True:
        delta_time = clock.tick(Values.FRAMERATE) / 1000.0
        loop()
        update(delta_time)


if __name__ == '__main__':
    player = Player(menu.playerName)
    gameFound = game.findGame(menu.gameCode, "host" if menu.isHost else "join")

    if gameFound:
        game.isTurn = menu.isHost
        game.gameCode = menu.gameCode
        game.start()

    if game.isTurn:
        run(drawLoop)
    else:
        run(guessLoop)
    run(drawLoop)
