import PySimpleGUI as sg
import pygame_gui as gui
from pygame_gui.core import ObjectID as OID
import pygame_gui.elements as guiElements
from pygame.rect import Rect
from library.contants import Values
from library.elements import Player
from threading import Thread
import clipboard
import random
import string
import time


def fitRectToLabel(label: guiElements.UILabel, fitToWidth=True, fitToHeight=True):
    width, height = label.font.size(label.text)
    label.set_dimensions(
        (width if fitToWidth else label.relative_rect.w,
         height if fitToHeight else label.relative_rect.h)
    )


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
                self.playerName = values['-NAME-'][0:7]
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

    def addGuess(self, player, guess=None):
        self.guessInput.set_text("")

        text = (player.name + ": " + guess) if guess else f"<font color='#00BB00'>{player.name} guessed the word</font>"
        self.guessBox.html_text += "<br>" + text

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

        self.__word = ""
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
        self.__isRunning = False

    def __countdown(self, timeInSec):
        while timeInSec and self.__isRunning:
            mins, secs = divmod(timeInSec, 60)
            timer = '{:1d}:{:02d}'.format(mins, secs)
            self.currentTime = timer
            time.sleep(1)
            timeInSec -= 1

        self.timer.hide()
        self.currentTime = "0:00"

    def setWord(self, word, isHost):
        self.__word = word.lower().strip()
        if isHost:
            self.word.set_text(word.upper().strip())
        else:
            word = ["_" if ch != " " else " " for ch in word]
            self.word.set_text(" ".join(word))

    def getWord(self):
        return self.__word

    def isTimeUp(self):
        return self.currentTime == "0:00"

    def updateTimer(self):
        self.timer.set_text(self.currentTime)

    def startTimer(self, t):
        self.__isRunning = True
        self.timer.show()
        Thread(name="Timer", target=self.__countdown, args=(t,), daemon=True).start()

    def stopTimer(self):
        self.__isRunning = False

    def clearWord(self):
        self.__word = ""
        self.word.set_text("")


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

        rect = Rect((0, 0), UI.SIZE_BTN)
        rect.center = [i / 2 for i in self.panel.rect.size]
        self.start = guiElements.UIButton(
            object_id="startButton",
            relative_rect=rect,
            text="Start",
            manager=uiManager,
            container=self.panel
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

        self.textOverlay = guiElements.UIPanel(
            object_id=OID("textOverlay", "panelOverlay"),
            relative_rect=Rect((x + UI.PADDING, y + UI.PADDING), UI.SIZE_DB),
            manager=uiManager,
            starting_layer_height=2,
            visible=False
        )

        sb = self.scoreBoardOverlay = guiElements.UIPanel(
            object_id=OID("scoreBoardOverlay", "panelOverlay"),
            relative_rect=Rect((x + UI.PADDING, y + UI.PADDING), UI.SIZE_DB),
            manager=uiManager,
            starting_layer_height=3,
            visible=False
        )

        self.textOneLiner = guiElements.UILabel(
            object_id="overlay",
            text=UI.CHOOSING_WORD,
            relative_rect=Rect((0, 0), UI.SIZE_DB),
            manager=uiManager,
            container=self.textOverlay,
        )

        rect = Rect(0, 0, sb.panel_container.rect.w, sb.panel_container.rect.h * 0.6)
        self.textTheWordWas = guiElements.UILabel(
            object_id=OID("theWordWas", "scoreboard"),
            text="The word was: ",
            relative_rect=rect,
            manager=uiManager,
            container=self.scoreBoardOverlay
        )

        rect.y += 10
        self.hostScore = guiElements.UILabel(
            object_id=OID("hostScore", "scoreboard"),
            text="",
            relative_rect=rect,
            manager=uiManager,
            container=self.scoreBoardOverlay
        )

        rect.y += 10
        self.joinScore = guiElements.UILabel(
            object_id=OID("joinScore", "scoreboard"),
            text="",
            relative_rect=rect,
            manager=uiManager,
            container=self.scoreBoardOverlay
        )

        self.words = []

        wordsN = 3
        dy = UI.SIZE_BTN[1] * wordsN / 2 + UI.MARGIN

        x = UI.SIZE_DB[0] / 2
        y = UI.SIZE_DB[1] / 2 - dy

        for i in range(wordsN):
            rect_btn = Rect((0, 0), UI.SIZE_BTN)
            rect_btn.center = x, y + i * dy

            btn = guiElements.UIButton(
                object_id=f"choice{i}",
                relative_rect=rect_btn,
                text="",
                manager=uiManager,
                container=self.textOverlay,
                visible=False
            )
            self.words.append(btn)

    def __toggleVisibility(self, isDrawing):
        if isDrawing:
            for button in self.words:
                button.show()
            self.textOneLiner.hide()
        else:
            for button in self.words:
                button.hide()
            self.textOneLiner.show()

    def setOneLinerText(self, text):
        self.textOneLiner.set_text(text)

    def showTextOverlay(self, words=None):
        self.textOverlay.show()

        if words:
            for button, word in zip(self.words, words):
                button.set_text(word)
            self.__toggleVisibility(isDrawing=True)
        else:
            self.__toggleVisibility(isDrawing=False)

    def hideTextOverlay(self):
        self.textOverlay.hide()


class PlayerPanel:
    CARD_HEIGHT = 60
    RANK_WIDTH = 55

    def __init__(self, uiManager):
        self.PLAYER_COUNT = 0
        self.TURN_COUNT = 0

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

        cardH = PlayerPanel.CARD_HEIGHT
        cardW = self.panel.rect.w - 2 * UI.PADDING
        roundPanel = guiElements.UIPanel(
            object_id=OID("roundPanel", "player"),
            relative_rect=Rect((0, 0), (cardW, cardH)),
            manager=uiManager,
            container=self.panel,
            starting_layer_height=1,
            margins={
                "left": UI.PADDING,
                "top": 0,
                "right": UI.PADDING,
                "bottom": UI.PADDING
            }
        )

        rect = Rect(0, 0, 200, roundPanel.panel_container.rect.h)
        self.round = guiElements.UILabel(
            object_id=OID("roundLabel", "round"),
            text="Round 1",
            relative_rect=rect,
            manager=self.panel.ui_manager,
            container=roundPanel,
            anchors={
                "left": "left",
                "right": "left",
                "top": "top",
                "bottom": "bottom"
            }
        )
        fitRectToLabel(self.round, fitToHeight=False)
        self.round.hide()

        self.players = {}

    def addPlayer(self, player: Player):
        num = self.PLAYER_COUNT + 1
        rankW = PlayerPanel.RANK_WIDTH

        cardH = PlayerPanel.CARD_HEIGHT
        cardY = (cardH + UI.MARGIN) * num
        cardW = self.panel.rect.w - 2 * UI.PADDING

        rect = Rect((0, cardY), (cardW, cardH))
        panel = guiElements.UIPanel(
            object_id=OID(f"player{num}", "player"),
            relative_rect=rect,
            manager=self.panel.ui_manager,
            container=self.panel,
            starting_layer_height=1
        )

        rect = Rect(0, 0, rankW, panel.panel_container.rect.h)
        rankLabel = guiElements.UILabel(
            object_id=OID(f"rank{num}", "rank"),
            text=f"#{player.rank}",
            relative_rect=rect,
            manager=self.panel.ui_manager,
            container=panel,
            anchors={
                "left": "left",
                "right": "left",
                "top": "top",
                "bottom": "bottom"
            }
        )

        nameW = panel.rect.w - 2 * rankW
        nameH = panel.panel_container.rect.h * 0.65

        rect = Rect(rankW, 0, nameW, nameH)
        nameLabel = guiElements.UILabel(
            object_id=OID(f"name{num}", "name"),
            text=player.name.strip(),
            relative_rect=rect,
            manager=self.panel.ui_manager,
            container=panel,
            anchors={
                "left": "left",
                "right": "right",
                "top": "top",
                "bottom": "bottom"
            }
        )

        rect.bottomleft = (rankW, panel.panel_container.rect.h + 6)
        scoreLabel = guiElements.UILabel(
            object_id=OID(f"score{num}", "score"),
            text=f"score: {player.score}",
            relative_rect=rect,
            manager=self.panel.ui_manager,
            container=panel,
            anchors={
                "left": "left",
                "right": "right",
                "top": "top",
                "bottom": "bottom"
            }
        )

        self.PLAYER_COUNT += 1
        p = self.players[f"player{self.PLAYER_COUNT}"] = {}
        p["name"] = nameLabel
        p["score"] = scoreLabel
        p["rank"] = rankLabel
        p["panel"] = panel
        p["object"] = player

    def updatePlayers(self):
        for _, player in self.players.items():
            player["score"].set_text(f"score: {player['object'].score}")
            player["rank"].set_text(f"#{player['object'].rank}")

    def updateRound(self):
        self.TURN_COUNT += 1
        self.round.set_text(f"Round {self.TURN_COUNT // self.PLAYER_COUNT + 1}")

    def showRoundLabel(self):
        self.round.show()


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

    def addGuessAndCheckCorrect(self, guess, player):
        word = self.panelWord.getWord()

        if guess == word:
            self.panelGuess.addGuess(player)
            player.hasGuessed = True
            return True
        else:
            self.panelGuess.addGuess(player, guess)
            return False

    def endRound(self):
        self.panelPlayer.updatePlayers()
        self.panelPlayer.updateRound()
        self.panelWord.stopTimer()
        self.panelWord.clearWord()
