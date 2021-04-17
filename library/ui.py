import PySimpleGUI as sg
import pygame_gui as gui
from pygame_gui.core import ObjectID as OID
import pygame_gui.elements as guiElements
from pygame.rect import Rect
from library.contants import Values
from threading import Thread
import clipboard
import random
import string
import time


def fitRectToLabel(label: guiElements.UILabel):
    print(label.font.size(label.text))
    label.set_dimensions(label.font.size(label.text))


class StartGame:
    def __init__(self):
        self.isHost = None
        self.playerName = None
        self.gameCode = None
        self.isQuit = self.__root()

    def __root(self):
        nameWindow = self.__name()

        while True:
            event, values = nameWindow.read()

            if event == "Exit" or event == sg.WIN_CLOSED:
                print("game exit. ByeBye!")
                nameWindow.close()
                return True
            elif event == 'OK':
                self.playerName = values['-NAME-']
                nameWindow.hide()

            gameModeWindow = self.__gameMode()
            while True:
                event, values = gameModeWindow.read()
                gameModeWindow.Hide()

                if event == '-HOST-':
                    self.isHost = True
                    hostJoinWindow = StartGame.__host()

                    event, values = hostJoinWindow.read()
                    if event == 'Copy':
                        code = self.gameCode = hostJoinWindow['-CODE-'].get()
                        clipboard.copy(code)
                        hostJoinWindow.close()
                        gameModeWindow.close()
                        nameWindow.close()
                        return False
                    elif event == 'Back':
                        hostJoinWindow.close()
                        gameModeWindow.UnHide()
                elif event == '-JOIN-':
                    self.isHost = False
                    hostJoinWindow = StartGame.__join()

                    while True:
                        event, values = hostJoinWindow.read()
                        if event == 'Back' or event == sg.WIN_CLOSED:
                            hostJoinWindow.close()
                            gameModeWindow.UnHide()
                            break
                        elif event == '-CODE-':
                            if len(values['-CODE-']) > 5:
                                values['-CODE-'] = values['-CODE-'][:-1]
                            hostJoinWindow.Element('-CODE-').Update(values['-CODE-'].upper())
                        elif event == '-GO-':
                            self.gameCode = hostJoinWindow['-CODE-'].get()
                            hostJoinWindow.close()
                            gameModeWindow.close()
                            nameWindow.close()
                            return False

                elif event == 'Back' or event == sg.WIN_CLOSED:
                    gameModeWindow.close()
                    nameWindow.UnHide()
                    break

    @staticmethod
    def __name():
        layout = [
            [sg.Text("Welcome to Skrable.", font="any 20")],
            [sg.Text("Please enter your name:")],
            [sg.InputText(key='-NAME-', size=(20, 1))],
            [sg.Column([[sg.Button("OK", font="any 14", bind_return_key=True), sg.Exit(font="any 14")]],
                       justification='right')]
        ]
        return sg.Window('', layout, font="any 17", no_titlebar=True)

    @staticmethod
    def __gameMode():
        layout = [
            [sg.Button('Host Game', key='-HOST-')],
            [sg.Button('Join Game', key='-JOIN-')],
            [sg.Exit("Back")]
        ]
        return sg.Window('', layout, font="any 23", element_justification='right', no_titlebar=True)

    @staticmethod
    def __join():
        layout = [
            [sg.Text('Enter Code')],
            [sg.InputText(key='-CODE-', size=(5, 1), font="any 25", enable_events=True)],
            [sg.Button("Go", key='-GO-', font="any 14", bind_return_key=True), sg.Button('Back', font="any 14")]
        ]
        return sg.Window('', layout, font="any 19", no_titlebar=True, element_justification='center')

    @staticmethod
    def __host():
        code = ''.join((random.choice(string.ascii_uppercase) for _ in range(5)))
        layout = [
            [
                sg.Text('Room Code: '),
                sg.Text(code, text_color="yellow", key='-CODE-'),
                sg.Button('Copy', font="any 14"),
                sg.Button('Back', font="any 14")
            ]
        ]

        return sg.Window('', layout, no_titlebar=True, font="any 19")


class GuessPanel:
    def __init__(self, uiManager):
        size = Values.SIZE_MAIN_WINDOW
        ratio = (1 - Values.RATIO_DB_TO_MW[0]) / 2

        x = -UI.PADDING_WIN - UI.MARGIN
        y = UI.PADDING_WIN + UI.MARGIN

        width = size[0] * ratio - (UI.PADDING_WIN + 2 * UI.MARGIN)
        height = size[1] - 2 * (UI.PADDING_WIN + UI.MARGIN)

        rect = Rect(0, 0, width, height)
        rect.topright = (x, y)

        self.panel = guiElements.UIPanel(
            object_id="guessPanel",
            relative_rect=rect,
            starting_layer_height=0,
            manager=uiManager,
            anchors={
                "left": "right",
                "right": "right",
                "top": "top",
                "bottom": "bottom"
            },
            margins={
                "left": UI.PADDING,
                "top": UI.PADDING,
                "right": UI.PADDING,
                "bottom": UI.PADDING
            }
        )

        rect = Rect((0, 0), (width - 2 * UI.PADDING, 2 * UI.PADDING))
        rect.bottomleft = (0, 0)

        self.guessInput = guiElements.UITextEntryLine(
            object_id="guessInput",
            relative_rect=rect,
            manager=uiManager,
            container=self.panel,
            anchors={
                "left": "left",
                "right": "right",
                "top": "bottom",
                "bottom": "bottom"
            }
        )

        width -= 2 * UI.PADDING
        height -= 3 * UI.PADDING + self.guessInput.rect.h
        rect = Rect((0, 0), (width, height))

        self.guessBox = guiElements.UITextBox(
            object_id="guessBox",
            html_text="",
            relative_rect=rect,
            manager=uiManager,
            container=self.panel
        )

        self.guessBox.scroll_bar_width = 3

    def addGuess(self, guess):
        self.guessInput.set_text("")

        self.guessBox.html_text += "<br>" + guess
        self.guessBox.rebuild()

    def disableGuessInput(self):
        self.guessInput.disable()

    def enableGuessInput(self):
        self.guessInput.enable()


class WordPanel:
    def __init__(self, uiManager):
        self.currentTime = "0:00"

        size = Values.SIZE_MAIN_WINDOW
        ratio = Values.RATIO_DB_TO_MW[0], (1 - Values.RATIO_DB_TO_MW[1]) * (1 - Values.RATIO_PP)

        x = size[0] * ((1 - ratio[0]) / 2) + UI.MARGIN * 2
        y = UI.PADDING_WIN + UI.MARGIN

        width = size[0] * ratio[0] - (4 * UI.MARGIN)
        height = size[1] * ratio[1] - (UI.PADDING_WIN + 2 * UI.MARGIN)

        rect = Rect(x, y, width, height)
        self.panel = guiElements.UIPanel(
            object_id="wordPanel",
            relative_rect=rect,
            starting_layer_height=0,
            manager=uiManager
        )

        rect = Rect(0, 0, width / 3, height)
        rect.center = width / 2, height / 2
        self.word = guiElements.UILabel(
            text="",
            object_id="wordLabel",
            relative_rect=rect,
            manager=uiManager,
            container=self.panel
        )

        rect = Rect(0, 0, width / 8, height)
        rect.midleft = 0, height / 2
        self.timer = guiElements.UILabel(
            text="1:00",
            object_id="timeLabel",
            relative_rect=rect,
            manager=uiManager,
            container=self.panel
        )

        self.timer.hide()

    def __countdown(self, timeInSec):
        while timeInSec:
            mins, secs = divmod(timeInSec, 60)
            timer = '{:1d}:{:02d}'.format(mins, secs)
            self.currentTime = timer
            time.sleep(1)
            timeInSec -= 1

        self.currentTime = "0:00"

    def setWord(self, word, isHost):
        if isHost:
            self.word.set_text(word.upper())
        else:
            word = ["_" if ch != " " else " " for ch in word]
            self.word.set_text(" ".join(word))

    def getWord(self):
        return self.word.text

    def isTimeUp(self):
        return self.currentTime == "0:00"

    def updateTimer(self):
        if not self.isTimeUp():
            self.timer.set_text(self.currentTime)
        else:
            self.timer.hide()

    def startTimer(self, t):
        self.timer.show()
        Thread(name="Timer", target=self.__countdown, args=(t,), daemon=True).start()


class PenPanel:
    def __init__(self, uiManager):
        size = Values.SIZE_MAIN_WINDOW
        ratio = Values.RATIO_DB_TO_MW[0], (1 - Values.RATIO_DB_TO_MW[1]) * Values.RATIO_PP

        x = size[0] * ((1 - ratio[0]) / 2) + UI.MARGIN * 2
        y = - UI.PADDING_WIN - UI.MARGIN

        width = size[0] * ratio[0] - (4 * UI.MARGIN)
        height = size[1] * ratio[1] - (UI.PADDING_WIN + 2 * UI.MARGIN)

        rect = Rect(0, 0, width, height)
        rect.bottomleft = (x, y)

        self.panel = guiElements.UIPanel(
            object_id="penPanel",
            relative_rect=rect,
            starting_layer_height=0,
            manager=uiManager,
            anchors={
                "left": "left",
                "right": "left",
                "top": "bottom",
                "bottom": "bottom"
            }
        )


class DrawBoardPanel:
    def __init__(self, uiManager):
        size = UI.SIZE_MW
        ratio = Values.RATIO_DB_TO_MW

        x = Values.POINT_DB[0] - UI.PADDING
        y = Values.POINT_DB[1] - UI.PADDING

        width = size[0] * ratio[0] - (4 * UI.MARGIN)
        height = size[1] * ratio[1] - (UI.PADDING_WIN + 2 * UI.MARGIN)

        rect = Rect(x, y, width, height)

        self.panel = guiElements.UIPanel(
            object_id="drawBoardPanel",
            relative_rect=rect,
            starting_layer_height=0,
            manager=uiManager,
            margins={
                "left": UI.PADDING,
                "top": UI.PADDING,
                "right": UI.PADDING,
                "bottom": UI.PADDING
            }
        )

        self.panelOverlay = guiElements.UIPanel(
            object_id="panelOverlay",
            relative_rect=Rect((x + UI.PADDING, y + UI.PADDING), UI.SIZE_DB),
            manager=uiManager,
            starting_layer_height=4,
        )

        self.textWord = guiElements.UILabel(
            object_id="overlay",
            text=UI.CHOOSING_WORD,
            relative_rect=Rect((0, 0), UI.SIZE_DB),
            manager=uiManager,
            container=self.panelOverlay,
        )

        self.words = []

        dy = UI.SIZE_BTN[1] * 3 / 2 + UI.MARGIN

        x = UI.SIZE_DB[0] / 2
        y = UI.SIZE_DB[1] / 2 - dy

        for i in range(3):
            rect_btn = Rect((0, 0), UI.SIZE_BTN)
            rect_btn.center = x, y + i * dy

            btn = guiElements.UIButton(
                object_id=f"choice{i}",
                relative_rect=rect_btn,
                text="",
                manager=uiManager,
                container=self.panelOverlay,
                visible=False
            )
            self.words.append(btn)

    def __toggleVisibility(self, isDrawing):
        if isDrawing:
            for button in self.words:
                button.show()
            self.textWord.hide()
        else:
            for button in self.words:
                button.hide()
            self.textWord.show()

    def setTextOverlayText(self, text):
        self.textWord.set_text(text)

    def showTextOverlay(self, words=None):
        self.panelOverlay.show()

        if words:
            for button, word in zip(self.words, words):
                button.set_text(word)
            self.__toggleVisibility(isDrawing=True)
        else:
            self.__toggleVisibility(isDrawing=False)

    def hideTextOverlay(self):
        self.panelOverlay.hide()


class PlayerPanel:
    CARD_HEIGHT = 60
    PLAYER_COUNT = 0
    RANK_WIDTH = 55

    def __init__(self, uiManager):
        size = Values.SIZE_MAIN_WINDOW
        ratio = (1 - Values.RATIO_DB_TO_MW[0]) / 2

        x = UI.PADDING_WIN + UI.MARGIN
        y = UI.PADDING_WIN + UI.MARGIN

        width = size[0] * ratio - (UI.PADDING_WIN + 2 * UI.MARGIN)
        height = size[1] - 2 * (UI.PADDING_WIN + UI.MARGIN)

        rect = Rect(x, y, width, height)

        self.panel = guiElements.UIPanel(
            object_id="playerPanel",
            relative_rect=rect,
            starting_layer_height=0,
            manager=uiManager,
            margins={
                "left": UI.PADDING,
                "top": UI.PADDING,
                "right": UI.PADDING,
                "bottom": UI.PADDING
            }
        )

        self.players = []

    def addPlayer(self, name, score=0, rank=1):
        num = PlayerPanel.PLAYER_COUNT
        cardH = PlayerPanel.CARD_HEIGHT
        rankW = PlayerPanel.RANK_WIDTH

        cardY = (cardH + UI.MARGIN) * num
        cardW = self.panel.rect.w - 2 * UI.PADDING

        rect = Rect((0, cardY), (cardW, cardH))
        player = guiElements.UIPanel(
            object_id=OID(f"player{num}", "player"),
            relative_rect=rect,
            manager=self.panel.ui_manager,
            container=self.panel,
            starting_layer_height=1
        )

        rect = Rect(0, 0, rankW, player.panel_container.rect.h)
        rankLabel = guiElements.UILabel(
            object_id=OID(f"rank{num}", "rank"),
            text=f"#{rank}",
            relative_rect=rect,
            manager=self.panel.ui_manager,
            container=player,
            anchors={
                "left": "left",
                "right": "left",
                "top": "top",
                "bottom": "bottom"
            }
        )

        nameW = player.rect.w - 2 * rankW
        nameH = player.panel_container.rect.h * 0.65

        rect = Rect(rankW, 0, nameW, nameH)
        nameLabel = guiElements.UILabel(
            object_id=OID(f"name{num}", "name"),
            text=name.strip(),
            relative_rect=rect,
            manager=self.panel.ui_manager,
            container=player,
            anchors={
                "left": "left",
                "right": "right",
                "top": "top",
                "bottom": "bottom"
            }
        )

        rect.bottomleft = (rankW, player.panel_container.rect.h + 6)
        scoreLabel = guiElements.UILabel(
            object_id=OID(f"score{num}", "score"),
            text=f"score: {score}",
            relative_rect=rect,
            manager=self.panel.ui_manager,
            container=player,
            anchors={
                "left": "left",
                "right": "right",
                "top": "top",
                "bottom": "bottom"
            }
        )

        PlayerPanel.PLAYER_COUNT += 1
        self.players.append((nameLabel, scoreLabel, rankLabel, player))


class UI:
    SIZE_MW = Values.SIZE_MAIN_WINDOW
    SIZE_DB = Values.SIZE_DRAW_BOARD
    SIZE_BTN = Values.SIZE_CHOOSING_BUTTON

    PADDING_WIN = Values.PADDING_WINDOW
    PADDING = Values.PADDING
    MARGIN = Values.MARGINS

    CHOOSING_WORD = "choosing word..."
    WAITING_FOR_PLAYER = "waiting for player..."

    def __init__(self):
        self.manager = gui.UIManager(Values.SIZE_MAIN_WINDOW, "library/theme.json")

        self.panelPlayer = PlayerPanel(self.manager)
        self.panelDrawBoard = DrawBoardPanel(self.manager)
        self.panelGuess = GuessPanel(self.manager)
        self.panelPen = PenPanel(self.manager)
        self.panelWord = WordPanel(self.manager)

    def addGuess(self, *guesses):
        word = self.panelWord.getWord()
        for guess in guesses:
            if guess == word:
                pass
