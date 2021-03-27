import pygame
import time
from library.network import Client
from library.contants import Colors, Values


# TODO - disconnect/exit implementation

class Pen:
    INK = 0
    ERASE = 1

    def __init__(self, size, color, mode=INK):
        self.size = size
        self.color = color
        self.mode = mode


class DrawBoard(Client):
    def __init__(self, window: pygame.Surface, brushSizes, brushColors):
        super().__init__()
        self.window = window
        self.brushSizes = brushSizes
        self.brushColors = brushColors
        self.pen = Pen(brushSizes[0], brushColors[0])
        self.last_position = None

        self.__isTurn = True

        self.window.fill(Colors.WHITE)
        
        self.__game = {
            "code": "",
            "type": "",
            "pendingCoordinates": [],
            "pendingGuesses": [],
            "isDrawing": False,
            "exitCode": self.SUCCESS
        } 

        self.__guesses = []

    @property
    def isDrawing(self):
        return self.__game["isDrawing"]

    @isDrawing.setter
    def isDrawing(self, new):
        self.__game["isDrawing"] = new

    @property
    def gameCode(self):
        return self.__game['code']

    @gameCode.setter
    def gameCode(self, new):
        self.__game['code'] = new

    @property
    def isTurn(self):
        return self.__isTurn

    @isTurn.setter
    def isTurn(self, new):
        self.__game['type'] = "host" if new else "join"
        self.__isTurn = new

    @property
    def playerType(self):
        return self.__game['type']

    def draw(self, start, end):
        s = [x - y for x, y in zip(start, Values.POINT_DB)]
        e = [x - y for x, y in zip(end, Values.POINT_DB)]

        pygame.draw.line(
            surface=self.window,
            color=self.pen.color,
            start_pos=s,
            end_pos=e,
            width=self.pen.size
        )

        if self.isTurn:
            self.__game["pendingCoordinates"].append(start)
            if len(self.__game["pendingCoordinates"]) == 1:
                self.__game["pendingCoordinates"].append(end)

    def addGuess(self, guess):
        self.__guesses.append(guess)
        self.__game["pendingGuesses"].append(guess)

    @property
    def pendingCoordinates(self):
        return self.__game["pendingCoordinates"]

    def clearPendingCoordinates(self):
        self.__game["pendingCoordinates"].clear()

    def __sendDrawBoard(self):
        while True:
            with self.lock:
                self._sendMsg(self.__game)
                self.clearPendingCoordinates()

                newGuesses = self._receiveMsg()

                if newGuesses:
                    if newGuesses == self.EXIT:
                        break
                    self.__guesses.extend(newGuesses)

            time.sleep(self.interval)

    def __receiveDrawBoard(self):
        while True:
            with self.lock:
                self._sendMsg(self.__game)
                self.__game["pendingGuesses"].clear()

                msg = self._receiveMsg()

                if msg:
                    if msg == self.EXIT:
                        break

                    isDrawing, pendingCoordinates = msg
                    self.__game["pendingCoordinates"].extend(pendingCoordinates)
                    self.isDrawing = isDrawing

            time.sleep(self.interval)

    def findGame(self, code, playerType):
        self._establishConnection()

        self._sendMsg({"code": code, "type": playerType, "exitCode": self.SUCCESS})
        msg = self._receiveMsg()
        if msg == self.SUCCESS:
            print(f"game {playerType}ed")
            print("Code:", code)
            return True
        elif msg == self.FAIL:
            print(f"game {playerType}ing failed")
        else:
            print("findGame() ->", msg)

        return False

    def run(self):
        if self.isTurn:
            self.__sendDrawBoard()
        else:
            self.__receiveDrawBoard()

        print("Game InActive")

    def setModeToInk(self):
        self.pen.mode = Pen.INK

    def setModeToEraser(self):
        self.pen.mode = Pen.ERASE

    def clearBoard(self):
        self.window.fill(Colors.WHITE)

    def __del__(self):
        msg = {
            "code": self.gameCode,
            "type": self.playerType,
            "exitCode": self.DISCONNECT
        }
        self._sendMsg(msg)
        msg = self._receiveMsg()
        if msg == self.SUCCESS:
            print("\nSuccessfully closed at Server")
        else:
            print("\nFailed to close at Server")
        super().__del__()


class Player(Client):
    def __init__(self, name):
        super(Player, self).__init__()
        self.name = name
        self.score = 0
