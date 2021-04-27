from library.network import Server
from threading import Lock, Thread
import random
import socket


class SkrableServer(Server):
    def __init__(self):
        super().__init__()
        self.games = {}
        self.newPlayerJoined = False
        self.wordList = wordList

    def processData(self, data, conn, addr):
        if data is None:
            return self.FAIL

        try:
            game = self.games[data["code"]]
            # game["lock"].acquire()

            if data["exitCode"] != self.SUCCESS:
                if data["exitCode"] == self.EXIT:
                    game["gameActive"] = False
                    processedData = self.SUCCESS
                else:
                    processedData = self.FAIL
            elif not game["gameActive"]:
                processedData = self.EXIT
            elif "gameStarted" in game and not data["word"]:
                # game["lock"].release()
                if game["isRoundReset"]:
                    game["isRoundReset"] = False

                if data["type"] == "host":
                    self.hostSelectWord(game, conn)
                else:
                    game["roundActive"] = True
                    self.joinSelectWord(game, conn)

                with game["lock"]:
                    if not game["isRoundReset"]:
                        game["isRoundReset"] = True
                        game["playersLeftToSendCoordinates"] = 0
                        game["playersLeftToSendGuesses"] = 0
                        game["notGuessedCounter"] = game["totalPlayers"] - 1
                        game["pendingCoordinates"].clear()
                        game["pendingGuesses"].clear()
                processedData = self.ABORT
            elif data["type"] == "host":
                game["roundActive"] = game["notGuessedCounter"] != 0
                game["roundActive"] = data["roundActive"] if game["roundActive"] else game["roundActive"]
                game["isDrawing"] = True if data["pendingCoordinates"] else data["isDrawing"]
                game["pendingCoordinates"].extend(data["pendingCoordinates"])

                processedData = [
                    game["roundActive"],
                    self.processGuesses(game)
                ]

                if game["playersLeftToSendCoordinates"]:
                    game["readyCoordinates"] = game["pendingCoordinates"].copy()
                    game["pendingCoordinates"].clear()
                    game["playersLeftToSendCoordinates"] = game["totalPlayers"] - 1

                if not game["roundActive"]:
                    game["word"] = ""
                    if not data["roundActive"]:
                        processedData = self.ABORT
            elif game["gameStarted"]:
                if game["word"] in data["pendingGuesses"]:
                    game["notGuessedCounter"] -= 1
                game["roundActive"] = game["notGuessedCounter"] != 0
                game["roundActive"] = data["roundActive"] if game["roundActive"] else game["roundActive"]
                game["pendingGuesses"].append((data["id"], data["pendingGuesses"])) if data["pendingGuesses"] else ...

                processedData = [
                    game["isDrawing"],
                    game["roundActive"],
                    game["readyCoordinates"],
                    self.processGuesses(game)
                ]

                game["playersLeftToSendCoordinates"] -= 1

                if not game["roundActive"]:
                    game["word"] = ""
                    if not data["roundActive"]:
                        processedData = self.ABORT
            else:
                raise Exception(f"Could not process data, [{data}]")

            # game["lock"].release() if game["lock"].locked() else ...
            return processedData
        except KeyError as e:
            if e.args[0] == data["code"] and data["type"] == "host":
                print(f"Creating New Game... ({data['code']})")

                game = self.games[data["code"]] = {
                    "totalPlayers": 0,
                    "playerNames": [data["name"]],
                    "pendingCoordinates": [],
                    "readyCoordinates": [],
                    "pendingGuesses": [],
                    "readyGuesses": [],
                    "word": "",
                    "rounds": data["rounds"],
                    "roundTime": data["roundTime"],
                    "isDrawing": False,
                    "roundActive": True,
                    "isRoundReset": False,
                    "gameActive": True,
                    "playersLeftToSendName": 0,
                    "playersLeftToSendCoordinates": 0,
                    "playersLeftToSendGuesses": 0,
                    "lock": Lock(),
                }

                self.newPlayer(game, "host", conn)
                return self.ABORT
            elif e.args[0] == "gameStarted" and data["type"] == "join":
                print(f"Joined game... ({data['code']})")
                game = self.games[data["code"]]
                game["playerNames"].append(data["name"])

                # game["lock"].release()

                self.newPlayer(game, "join", conn)
                return self.ABORT

            # TODO - handle error codes
            print("games:", self.games)
            print("data:", data)
            return self.FAIL
        except Exception as e:
            game = self.games[data["code"]]
            if "gameStarted" in game:
                game["totalPlayers"] -= 1
            raise e

    @staticmethod
    def processGuesses(game):
        if game["playersLeftToSendGuesses"]:
            game["playersLeftToSendGuesses"] -= 1
            if not game["roundActive"]:
                game["readyGuesses"].extend(game["pendingGuesses"])
        else:
            game["readyGuesses"] = [game["pendingGuesses"].pop(0)] if game["pendingGuesses"] else []
            game["playersLeftToSendGuesses"] = game["totalPlayers"] - 1
        return game["readyGuesses"]

    def waitForStartSignal(self, conn, game):
        msg = self._requestClient(conn)
        print("start signal received:", msg)
        if msg == self.START:
            game["gameStarted"] = True
            game["notGuessedCounter"] = game["totalPlayers"] - 1

    def newPlayer(self, game, playerType, conn: socket.socket):
        game["totalPlayers"] += 1

        self._sendToClient(conn, self.SUCCESS)
        if playerType != "host":
            self._sendToClient(conn, (game["playerNames"], game["rounds"], game["roundTime"]))
            self.newPlayerJoined = True
        else:
            Thread(target=self.waitForStartSignal, args=(conn, game), daemon=True).start()

        while self.newPlayerJoined:
            pass

        startGame = False
        while not startGame:
            while not self.newPlayerJoined:
                if "gameStarted" in game:
                    startGame = True
                    break
            else:
                if not game["playersLeftToSendName"]:
                    game["playersLeftToSendName"] = game["totalPlayers"] - 1

                self._sendToClient(conn, game["playerNames"][-1])
                with game["lock"]:
                    game["playersLeftToSendName"] -= 1
                while game["playersLeftToSendName"]:
                    pass
            self.newPlayerJoined = False

        self._sendToClient(conn, self.START)
        self.hostSelectWord(game, conn) if playerType == "host" else self.joinSelectWord(game, conn)

    def hostSelectWord(self, game, conn: socket.socket):
        words = self.getNRandomWords(3)
        self._sendToClient(conn, words)
        game["word"] = self._requestClient(conn)

    def joinSelectWord(self, game, conn: socket.socket):
        while not game["word"]:
            pass
        self._sendToClient(conn, game["word"])

    def getNRandomWords(self, N):
        return random.sample(self.wordList, N)


if __name__ == '__main__':
    with open("wordlist.txt") as file:
        wordList = set(file.readline().split(", "))

    SkrableServer().run()
