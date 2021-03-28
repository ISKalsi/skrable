import PySimpleGUI as sg
import pygame_gui as gui
import pygame_gui.elements as guiElements
from pygame.rect import Rect
from library.contants import Values
import clipboard
import random
import string


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


class UI:
    class ClassProperty:
        def __init__(self, getter):
            self.getter = getter

        def __get__(self, instance, owner):
            return self.getter(owner)

    size_window = Values.SIZE_MAIN_WINDOW
    size_drawBoard = Values.SIZE_DRAW_BOARD

    padding_window = Values.PADDING_WINDOW
    padding = Values.PADDING
    margin = Values.MARGINS

    __manager = None

    @ClassProperty
    def manager(self) -> gui.UIManager:
        if self.__manager is None:
            self.__manager = gui.UIManager(Values.SIZE_MAIN_WINDOW)
        return self.__manager


class GuessPanel:
    def __init__(self):
        size = Values.SIZE_MAIN_WINDOW
        ratio = (1 - Values.RATIO_DB_TO_MW[0]) / 2

        x = -UI.padding_window - UI.margin
        y = UI.padding_window + UI.margin

        width = size[0] * ratio - (UI.padding_window + 2 * UI.margin)
        height = size[1] - 2 * (UI.padding_window + UI.margin)

        rect = Rect(0, 0, width, height)
        rect.topright = (x, y)

        self.panel = guiElements.UIPanel(
            relative_rect=rect,
            starting_layer_height=0,
            manager=UI.manager,
            anchors={
                "left": "right",
                "right": "right",
                "top": "top",
                "bottom": "bottom"
            },
            margins={
                "left": UI.padding,
                "top": UI.padding,
                "right": UI.padding,
                "bottom": UI.padding
            }
        )

        rect = Rect((0, 0), (width - 2 * UI.padding, 2 * UI.padding))
        rect.bottomleft = (0, 0)

        self.guessInput = guiElements.UITextEntryLine(
            relative_rect=rect,
            manager=UI.manager,
            container=self.panel,
            anchors={
                "left": "left",
                "right": "right",
                "top": "bottom",
                "bottom": "bottom"
            }
        )

        width -= 2 * UI.padding
        height -= 3 * UI.padding + self.guessInput.rect.h
        rect = Rect((0, 0), (width, height))

        self.guessBox = guiElements.UITextBox(
            html_text="",
            relative_rect=rect,
            manager=UI.manager,
            container=self.panel
        )


class PenPanel:
    def __init__(self):
        size = Values.SIZE_MAIN_WINDOW
        ratio = Values.RATIO_DB_TO_MW[0], 1 - Values.RATIO_DB_TO_MW[1]

        x = size[0] * ((1 - ratio[0]) / 2) + UI.margin * 2
        y = - UI.padding_window - UI.margin

        width = size[0] * ratio[0] - (4 * UI.margin)
        height = size[1] * ratio[1] - (UI.padding_window + 2 * UI.margin)

        rect = Rect(0, 0, width, height)
        rect.bottomleft = (x, y)

        self.panel = guiElements.UIPanel(
            relative_rect=rect,
            starting_layer_height=0,
            manager=UI.manager,
            anchors={
                "left": "left",
                "right": "left",
                "top": "bottom",
                "bottom": "bottom"
            }
        )


class DrawBoardPanel:
    def __init__(self):
        size = Values.SIZE_MAIN_WINDOW
        ratio = Values.RATIO_DB_TO_MW

        x = size[0] * ((1 - ratio[0]) / 2) + UI.margin * 2
        y = UI.padding_window + UI.margin

        width = size[0] * ratio[0] - (4 * UI.margin)
        height = size[1] * ratio[1] - (UI.padding_window + 2 * UI.margin)

        rect = Rect(x, y, width, height)

        self.panel = guiElements.UIPanel(
            relative_rect=rect,
            starting_layer_height=0,
            manager=UI.manager,
            margins={
                "left": UI.padding,
                "top": UI.padding,
                "right": UI.padding,
                "bottom": UI.padding
            }
        )


class PlayerPanel:
    def __init__(self):
        size = Values.SIZE_MAIN_WINDOW
        ratio = (1 - Values.RATIO_DB_TO_MW[0]) / 2

        x = UI.padding_window + UI.margin
        y = UI.padding_window + UI.margin

        width = size[0] * ratio - (UI.padding_window + 2 * UI.margin)
        height = size[1] - 2 * (UI.padding_window + UI.margin)

        rect = Rect(x, y, width, height)

        self.panel = guiElements.UIPanel(
            relative_rect=rect,
            starting_layer_height=0,
            manager=UI.manager,
        )


if __name__ == '__main__':
    import pygame

    pygame.init()
    pygame.display.set_caption("UI Test")
    display = pygame.display.set_mode(Values.SIZE_MAIN_WINDOW)
    display.fill(UI.manager.ui_theme.get_colour("dark_bg"))

    clock = pygame.time.Clock()
    surface = pygame.surface.Surface((500, 500))
    surface.fill((25, 25, 25))

    playerPanel = PlayerPanel()
    drawBoardPanel = DrawBoardPanel()
    guessPanel = GuessPanel()
    penPanel = PenPanel()

    isRunning = True
    while isRunning:
        time_delta = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                isRunning = False

            if event.type == pygame.USEREVENT:
                if event.user_type == gui.UI_BUTTON_PRESSED:
                    pass
                    # if event.ui_element == hello_button:
                    #     print('Hello World!')

                if event.user_type == gui.UI_TEXT_ENTRY_FINISHED:
                    pass
                    # if event.ui_element == textEntry:
                    #     print(textEntry.get_text())

            UI.manager.process_events(event)

        UI.manager.update(time_delta)
        UI.manager.draw_ui(display)

        pygame.display.update()
