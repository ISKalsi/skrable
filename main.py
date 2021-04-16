import pygame
import pygame_gui as gui
from threading import Lock
from library.contants import Values, Colors
from library.elements import DrawBoard, Game, Player
from library.ui import StartGame, UI

menu = StartGame()

if menu.isQuit:
    exit(0)

pygame.init()
pygame.display.set_caption("skrable")

mainWindow = pygame.display.set_mode(UI.SIZE_MW)
clock = pygame.time.Clock()
lock = Lock()

drawBoard = DrawBoard(
    window=pygame.surface.Surface(UI.SIZE_DB),
    brushSizes=Values.SIZE_BRUSHES,
    brushColors=Colors.getAllColors()
)

UI.init()
game = Game(drawBoard)


def isQuit(event):
    if event.type == pygame.QUIT:
        pygame.quit()
        exit(0)


def update(dt, blitDrawBoard):
    UI.panelWord.updateTimer()

    UI.manager.update(dt)
    UI.manager.draw_ui(mainWindow)

    mainWindow.blit(drawBoard.window, Values.POINT_DB) if blitDrawBoard else ...

    pygame.display.update()


def chooseWordLoop():
    for event in pygame.event.get():
        isQuit(event)

        if event.type == pygame.USEREVENT:
            if event.user_type == gui.UI_BUTTON_PRESSED:
                objID = event.ui_object_id.split(".")

                if objID[0] == "panelOverlay":
                    game.word = event.ui_element.text
                    return False

        UI.manager.process_events(event)

    return True


def waitWordLoop():
    for event in pygame.event.get():
        isQuit(event)
        UI.manager.process_events(event)

    if game.wordChosen:
        print("word chosen")
        return False

    return True


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

    with lock:
        pg = game.pendingGuesses
        for guess in pg:
            UI.panelGuess.addGuess(guess)
            pg.pop(0)

    return True


def guessLoop():
    for event in pygame.event.get():
        isQuit(event)

        if event.type == pygame.USEREVENT:
            if event.user_type == gui.UI_TEXT_ENTRY_FINISHED:
                if event.ui_object_id == "guessPanel.guessInput" and event.text:
                    game.addToPendingGuesses(event.text)
                    UI.panelGuess.addGuess(event.text)

        UI.manager.process_events(event)

    with lock:
        pc = game.pendingCoordinates
        if len(pc) > 1:
            for i in range(len(pc)-1):
                drawBoard.draw(pc[0], pc[1])
                pc.pop(0)

        if pc and not drawBoard.isDrawing:
            pc.clear()

    return True


def run(loop, blitDrawBoard=True):
    flag = True
    while flag:
        delta_time = clock.tick(Values.FRAMERATE) / 1000.0
        flag = loop()
        update(delta_time, blitDrawBoard)


if __name__ == '__main__':
    player = Player(menu.playerName)
    gameFound = game.findGame(menu.gameCode, "host" if menu.isHost else "join")

    if gameFound:
        game.isTurn = menu.isHost
        game.gameCode = menu.gameCode
        game.start()
    else:
        exit()

    UI.panelGuess.disableGuessInput()
    if game.isTurn:
        UI.panelDrawBoard.showChoosingWordOverlay(game.wordChoices)
        run(chooseWordLoop, blitDrawBoard=False)
        UI.panelDrawBoard.hideChoosingWordOverlay()

        UI.panelWord.setWord(game.word, isHost=True)
        UI.panelWord.startTimer(60)

        run(drawLoop)
    else:
        UI.panelDrawBoard.showChoosingWordOverlay()
        run(waitWordLoop, blitDrawBoard=False)
        UI.panelDrawBoard.hideChoosingWordOverlay()

        UI.panelGuess.enableGuessInput()

        UI.panelWord.setWord(game.word, isHost=False)
        UI.panelWord.startTimer(60)

        run(guessLoop)
