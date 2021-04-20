import pygame
import time
from library.network import Client
from library.contants import Colors, Values
from threading import Thread


# TODO - disconnect/exit implementation
class Player:
    def __init__(self, name, score=0, rank=1):
        self.name = name
        self.score = score
        self.rank = rank


class Pen:
    INK = 0
    ERASE = 1

    def __init__(self, size, color, mode=INK):
        self.size = size
        self.color = color
        self.mode = mode


class DrawBoard:
    def __init__(self, window: pygame.Surface, brushSizes, brushColors):
        self.window = window
        self.brushSizes = brushSizes
        self.brushColors = brushColors
        self.pen = Pen(brushSizes[0], brushColors[0])
        self.last_position = None
        self.isDrawing = False

        self.window.fill(Colors.WHITE)

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

    def setModeToInk(self):
        self.pen.mode = Pen.INK

    def setModeToEraser(self):
        self.pen.mode = Pen.ERASE

    def clearBoard(self):
        self.window.fill(Colors.WHITE)


class Game(Client):
    def __init__(self, name, code, isHost, drawBoard):
        super().__init__()

        self.drawBoard = drawBoard
        self.__game = {
            "name": name,
            "opponent": "",
            "code": code,
            "type": "host" if isHost else "join",
            "word": "",
            "rounds": 0,
            "roundTime": 0,
            "roundActive": False,
            "pendingCoordinates": [],
            "pendingGuesses": [],
            "isDrawing": False,
            "isGuessed": False,
            "exitCode": self.SUCCESS
        }

        self.__isTurn = isHost
        self.__wordChoices = []
        self.guesses = []
        self.players = []
        self.wordChosen = False

        self.__isRunning = True
        self.__setRoundInactiveCalled = False

    @property
    def playerName(self):
        return self.__game["name"]

    @property
    def opponentName(self):
        return self.__game["opponent"]

    @property
    def wordChoices(self):
        return self.__wordChoices

    @property
    def word(self):
        return self.__game["word"]

    @word.setter
    def word(self, new):
        self.wordChosen = True if new else False
        self.__game["word"] = new.strip().lower()

    @property
    def isDrawing(self):
        return self.__game["isDrawing"]

    @isDrawing.setter
    def isDrawing(self, new):
        self.__game["isDrawing"] = new

    @property
    def isGuessed(self):
        return self.__game["isGuessed"]

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
    def rounds(self):
        return self.__game["rounds"]

    @property
    def roundTime(self):
        return self.__game["roundTime"]

    @property
    def isRoundActive(self):
        return self.__game["roundActive"]

    def setRoundInactive(self):
        if not self.__setRoundInactiveCalled:
            self.__setRoundInactiveCalled = True
            self.__prepForNextRound()
            self.__game["roundActive"] = False

    def setRoundActive(self):
        self.__game["roundActive"] = True
        self.__setRoundInactiveCalled = False

    @property
    def playerType(self):
        return self.__game['type']

    @property
    def pendingCoordinates(self):
        return self.__game["pendingCoordinates"]

    @property
    def pendingGuesses(self):
        return self.__game["pendingGuesses"]

    def addToPendingGuesses(self, guess):
        self.guesses.append(guess)
        self.__game["pendingGuesses"].append(guess)
        self.__game["isGuessed"] = guess == self.word

    def addToPendingCoordinates(self, coordinate):
        if not self.__game["pendingCoordinates"]:
            self.__game["pendingCoordinates"].append(self.drawBoard.last_position)
        self.__game["pendingCoordinates"].append(coordinate)

    def __resetRound(self):
        while self.__game["pendingGuesses"] or self.__game["pendingCoordinates"]:
            pass

        self.word = ""
        self.__wordChoices.clear()
        self.__game["isGuessed"] = False
        self.__game["isDrawing"] = False
        self.__game["exitCode"] = self.SUCCESS
        self.pendingCoordinates.clear()
        self.pendingGuesses.clear()

    def __prepForNextRound(self):
        self.isTurn = not self.isTurn
        self.__resetRound()
        self._sendMsg(self.__game)
        print("Round finished.")

    def __sendDrawBoard(self):
        while True:
            # todo handle time finish condition correctly
            if self.__setRoundInactiveCalled:
                break

            self._sendMsg(self.__game)
            self.__game["pendingCoordinates"].clear()

            msg = self._receiveMsg()

            if msg:
                if msg == self.EXIT:
                    break

                isGuessed, roundActive, newGuesses = msg
                self.__game["isGuessed"] = isGuessed
                self.guesses.extend(newGuesses)
                self.__game["pendingGuesses"].extend(newGuesses)

                if not roundActive or isGuessed:
                    self.setRoundInactive()
                    break

            time.sleep(self.interval)

    def __receiveDrawBoard(self):
        while True:
            self._sendMsg(self.__game)
            self.__game["pendingGuesses"].clear()

            msg = self._receiveMsg()

            # todo handle time finish condition correctly
            if self.__setRoundInactiveCalled:
                break

            if msg:
                if msg == self.EXIT:
                    print("Exiting...")
                    break

                isDrawing, roundActive, pendingCoordinates = msg
                if not roundActive:
                    self.setRoundInactive()
                    break

                self.__game["pendingCoordinates"].extend(pendingCoordinates)
                self.drawBoard.isDrawing = self.isDrawing

            time.sleep(self.interval)

    def __receiveWord(self):
        print("waiting for word")
        self.word = self._receiveMsg()
        print(self.word)

    def __sendWord(self):
        wc = self.__wordChoices = self._receiveMsg()
        print("received:", wc)

        while not self.wordChosen:
            pass

        print("sending word", self.word)
        self._sendMsg(self.word)
        print("sent")

    def run(self):
        self.__sendDrawBoard() if self.isTurn else self.__receiveDrawBoard()
        print("Round InActive")

        while self.__isRunning:
            while not self.isRoundActive:
                pass

            if self.isTurn:
                self.__sendWord()
                self.__sendDrawBoard()
            else:
                self.__receiveWord()
                self.__receiveDrawBoard()

            print("Round InActive")

    def __setupGame(self):
        if self.isTurn:
            msg = self._receiveMsg()
            if msg:
                joinName = msg
                self.__game["opponent"] = joinName
            else:
                print("error setting up host")
            self.__sendWord()
        else:
            hostName, rounds, roundTime = self._receiveMsg()
            if hostName:
                self.__game["rounds"] = rounds
                self.__game["roundTime"] = roundTime
                self.__game["opponent"] = hostName
            else:
                print("error setting up join")
            self.__receiveWord()

    def newGame(self, rounds=None, timePerRound=None):
        self._establishConnection()

        self.__game["rounds"] = rounds
        self.__game["roundTime"] = timePerRound

        playerType = "host" if self.isTurn else "join"
        self._sendMsg({
            "code": self.gameCode,
            "name": self.playerName,
            "rounds": rounds,
            "roundTime": timePerRound,
            "type": playerType,
            "exitCode": self.SUCCESS
        })
        msg = self._receiveMsg()
        if msg == self.SUCCESS:
            print(f"game {playerType}ed by {self.playerName}")
            print("Code:", self.gameCode)

            Thread(name="setupGame", target=self.__setupGame, daemon=True).start()

            return True
        elif msg == self.FAIL:
            print(f"game {playerType}ing failed")
        else:
            print("findGame() ->", msg)

        return False

    def addPlayers(self, *players: Player):
        self.players.extend(players)

    def calculateScore(self, minLeft, secLeft):
        totalSecLeft = minLeft * 60 + secLeft
        timeTaken = self.roundTime - totalSecLeft

        score1 = totalSecLeft * 13
        score2 = timeTaken * 11

        self.players[0].score += score1
        self.players[1].score += score2

        if score1 > score2:
            self.players[0].rank = 1
            self.players[1].rank = 2
        else:
            self.players[0].rank = 2
            self.players[1].rank = 1

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
