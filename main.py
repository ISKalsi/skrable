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

ui = UI()
game = Game(drawBoard)


def isQuit(event):
    if event.type == pygame.QUIT:
        pygame.quit()
        exit(0)


def update(dt, blitDrawBoard):
    ui.panelWord.updateTimer()

    ui.manager.update(dt)
    ui.manager.draw_ui(mainWindow)

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

        ui.manager.process_events(event)

    return True


def waitWordLoop():
    for event in pygame.event.get():
        isQuit(event)
        ui.manager.process_events(event)

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

        ui.manager.process_events(event)

    with lock:
        pg = game.pendingGuesses
        for guess in pg:
            ui.panelGuess.addGuess(guess)
            pg.pop(0)

    return True


def guessLoop():
    for event in pygame.event.get():
        isQuit(event)

        if event.type == pygame.USEREVENT:
            if event.user_type == gui.UI_TEXT_ENTRY_FINISHED:
                if event.ui_object_id == "guessPanel.guessInput" and event.text:
                    game.addToPendingGuesses(event.text)
                    ui.panelGuess.addGuess(event.text)

        ui.manager.process_events(event)

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

    rounds = 2

    for _ in range(rounds * 2):
        ui.panelGuess.disableGuessInput()
        if game.isTurn:
            ui.panelDrawBoard.showChoosingWordOverlay(game.wordChoices)
            run(chooseWordLoop, blitDrawBoard=False)
            ui.panelDrawBoard.hideChoosingWordOverlay()

            ui.panelWord.setWord(game.word, isHost=True)
            ui.panelWord.startTimer(60)

            run(drawLoop)
        else:
            ui.panelDrawBoard.showChoosingWordOverlay()
            run(waitWordLoop, blitDrawBoard=False)
            ui.panelDrawBoard.hideChoosingWordOverlay()

            ui.panelGuess.enableGuessInput()

            ui.panelWord.setWord(game.word, isHost=False)
            ui.panelWord.startTimer(60)

            run(guessLoop)

        game.isTurn = not game.isTurn
