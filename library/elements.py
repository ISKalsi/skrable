import pygame
import time
import threading
from library.network import Client
from library.contants import Colors, Values
from threading import Thread


# TODO - disconnect/exit implementation
class Player:
    COUNT = 0

    def __init__(self, name):
        self.ID = Player.COUNT
        self.name = name
        self.score = 0
        self.rank = 1
        self.isTurn = Player.COUNT == 0
        self.hasGuessed = False
        self.timeLeft = 0

        Player.COUNT += 1

    def __lt__(self, other):
        return self.score < other.score


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
            "id": 0,
            "code": code,
            "type": "host" if isHost else "join",
            "word": "",
            "rounds": 0,
            "roundTime": 0,
            "roundActive": False,
            "gameStarted": False,
            "pendingCoordinates": [],
            "pendingGuesses": [],
            "isDrawing": False,
            "exitCode": self.SUCCESS
        }

        self.__isTurn = isHost
        self.__wordChoices = []
        self.guesses = []
        self.allGuesses = []
        self.players = [Player(name)] if isHost else []
        self.wordChosen = False
        self.notGuessedCounter = 0
        self.drawerID = 0

        self.__isRunning = True
        self.__setRoundInactiveCalled = False
        self.__mainThreadResponded = False
        self.__clientThreadResponded = False

    @property
    def playerName(self):
        return self.__game["name"]

    @property
    def playerID(self):
        return self.__game["id"]

    @playerID.setter
    def playerID(self, new):
        self.__game["id"] = new

    @property
    def wordChoices(self):
        return self.__wordChoices

    @property
    def word(self):
        return self.__game["word"]

    @word.setter
    def word(self, new):
        print(new)
        self.wordChosen = True if new else False
        self.__game["word"] = new.strip().lower()

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
    def isStarted(self):
        return self.__game["gameStarted"]

    def startGame(self):
        self._sendMsg(self.START)
        print("start signal sent")
        self.__game["gameStarted"] = True

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

    def nextRound(self):
        name = threading.currentThread().getName()
        if name == "ClientThread":
            self.__clientThreadResponded = True
        elif name == "MainThread":
            self.__mainThreadResponded = True

    def setRoundActive(self):
        while not self.__mainThreadResponded or not self.__clientThreadResponded:
            pass

        self.__game["roundActive"] = True
        self.__setRoundInactiveCalled = False
        self.__mainThreadResponded = False
        self.__clientThreadResponded = False

    def setRoundInactive(self, isTimeUp=False):
        if not self.__setRoundInactiveCalled:
            self.__game["roundActive"] = False
            self.__setRoundInactiveCalled = True
            if isTimeUp:
                self._sendMsg(self.__game)
            self.__prepForNextRound()

    @property
    def playerType(self):
        return self.__game['type']

    @property
    def pendingCoordinates(self):
        return self.__game["pendingCoordinates"]

    @property
    def pendingGuesses(self):
        return self.guesses

    def addToPendingGuesses(self, timeLeft, guess):
        self.__game["pendingGuesses"].append((timeLeft, guess))

    def addToPendingCoordinates(self, coordinate):
        if not self.__game["pendingCoordinates"]:
            self.__game["pendingCoordinates"].append(self.drawBoard.last_position)
        self.__game["pendingCoordinates"].append(coordinate)

    def __turnChange(self):
        N = len(self.players)
        ID = self.drawerID = (self.drawerID + 1) % N

        self.isTurn = ID == self.playerID

    def __resetRound(self):
        while self.pendingGuesses or self.pendingCoordinates:
            pass

        self.word = ""
        self.notGuessedCounter = len(self.players) - 1
        self.wordChosen = False
        self.__wordChoices.clear()
        self.__game["isDrawing"] = False
        self.__game["exitCode"] = self.SUCCESS

    def __sendUpdatedGame(self):
        self._sendMsg(self.__game)

    def __prepForNextRound(self):
        self.__turnChange()
        self.__resetRound()
        print("Sending round end info to server...")
        self.__sendUpdatedGame()
        print("Round finished")

    def __isRoundActiveOnServer(self, roundActive):
        if not roundActive:
            print("Clearing guesses list")
            while self.guesses:
                pass
            print("Cleared guesses list")

            self.setRoundInactive()
            return False
        return True

    def sendDrawBoard(self):
        while not self.__setRoundInactiveCalled:
            with self.lock:
                if self.__setRoundInactiveCalled:
                    break

                self._sendMsg(self.__game)
                self.__game["pendingCoordinates"].clear()
                msg = self._receiveMsg()

            if msg:
                if msg == self.EXIT:
                    break

                roundActive, newGuesses = msg
                self.guesses.extend(newGuesses)
                self.allGuesses.extend(newGuesses)

                if not self.__isRoundActiveOnServer(roundActive):
                    break

            time.sleep(self.interval)

    def receiveDrawBoard(self):
        while not self.__setRoundInactiveCalled:
            with self.lock:
                if self.__setRoundInactiveCalled:
                    break

                self._sendMsg(self.__game)
                self.__game["pendingGuesses"].clear()
                msg = self._receiveMsg()

            if msg:
                if msg == self.EXIT:
                    print("Exiting...")
                    break

                isDrawing, roundActive, pendingCoordinates, newGuesses = msg
                self.__game["pendingCoordinates"].extend(pendingCoordinates)
                if newGuesses:
                    self.guesses.extend(newGuesses)
                    self.allGuesses.extend(newGuesses)
                self.drawBoard.isTurn = self.isDrawing

                if not self.__isRoundActiveOnServer(roundActive):
                    break

            time.sleep(self.interval)

    def receiveWord(self):
        print("waiting for word")
        self.word = self._receiveMsg()

    def sendWord(self):
        wc = self.__wordChoices = self._receiveMsg()
        print("received:", wc)

        while not self.wordChosen:
            pass

        print("sending word", self.word)
        self._sendMsg(self.word)
        print("sent")

    def run(self):
        self.notGuessedCounter = len(self.players) - 1
        self.sendDrawBoard() if self.isTurn else self.receiveDrawBoard()
        print("Round InActive\n")

        while self.__isRunning:
            self.nextRound()
            self.setRoundActive()

            if self.isTurn:
                self.sendWord()
                self.sendDrawBoard()
            else:
                self.receiveWord()
                self.receiveDrawBoard()

            print("Round InActive\n")

    def __setupGame(self):
        if self.isTurn:
            name = self._receiveMsg()
            while name != self.START:
                if name:
                    self.players.append(Player(name))
                name = self._receiveMsg()

            self.__game["roundActive"] = True
            self.sendWord()
        else:
            msg = self._receiveMsg()
            if msg:
                name, rounds, roundTime = msg
                self.__game["rounds"] = rounds
                self.__game["roundTime"] = roundTime
                self.players.extend([Player(name) for name in name])

                self.playerID = len(self.players)-1

                name = self._receiveMsg()
                while name != self.START:
                    if name:
                        self.players.append(Player(name))
                    name = self._receiveMsg()

                self.__game["gameStarted"] = True
                self.__game["roundActive"] = True
                self.receiveWord()
            else:
                print("error setting up join")

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

    def calculateScore(self, totalSecLeft):
        playersGuessed = 0
        for player in self.players:
            if player.hasGuessed:
                playersGuessed += 1

        for player in self.players:
            if player.hasGuessed:
                player.score = player.timeLeft * 15 + 100
            elif player.isTurn:
                player.isTurn = False
                if playersGuessed:
                    player.score += (playersGuessed * 15) + (totalSecLeft * 5) + 100

        ranked = sorted(self.players, reverse=True)
        for rank, player in enumerate(ranked):
            player.rank = rank + 1
            player.hasGuessed = False
            player.timeLeft = 0

        self.players[self.drawerID].isTurn = True

    def endGame(self):
        self.__isRunning = False

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
