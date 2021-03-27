import PySimpleGUI as sg
import clipboard
import random
import string


class Menu:
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
                    hostJoinWindow = Menu.__host()

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
                    hostJoinWindow = Menu.__join()

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
