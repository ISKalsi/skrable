from library.network import Server
from threading import Lock
import random
import socket


class SkrableServer(Server):
    def __init__(self):
        super().__init__()
        self.games = {}
        self.wordList = wordList

    def processData(self, data, conn, addr):
        if data is None:
            return self.FAIL

        try:
            game = self.games[data["code"]]
            game["lock"].acquire()

            if data["exitCode"] != self.SUCCESS:
                if data["exitCode"] == self.EXIT:
                    game["gameActive"] = False
                    processedData = self.SUCCESS
                else:
                    processedData = self.FAIL
            elif not game["gameActive"]:
                processedData = self.EXIT
            elif "playerJoined" in game and not data["word"]:
                game["lock"].release()
                if data["type"] == "host":
                    self.hostSelectWord(game, conn)
                else:
                    game["roundActive"] = True
                    self.joinSelectWord(game, conn)
                processedData = self.ABORT
            elif data["type"] == "host":
                game["roundActive"] = data["roundActive"] if game["roundActive"] else game["roundActive"]
                game["pendingCoordinates"].extend(data["pendingCoordinates"])
                game["isDrawing"] = True if data["pendingCoordinates"] else data["isDrawing"]
                processedData = game["isGuessed"], game["roundActive"], tuple(game["pendingGuesses"])
                if game["isGuessed"]:
                    game["isGuessed"] = False
                game["pendingGuesses"].clear()
            elif game["playerJoined"]:
                game["roundActive"] = data["roundActive"] if game["roundActive"] else game["roundActive"]
                game["pendingGuesses"].extend(data["pendingGuesses"])
                if data["isGuessed"]:
                    game["isGuessed"] = True
                    game["word"] = ""
                    game["roundActive"] = False
                processedData = game["isDrawing"], game["roundActive"], tuple(game["pendingCoordinates"])
                game["pendingCoordinates"].clear()
            else:
                raise Exception(f"Could not process data, [{data}]")

            game["lock"].release() if game["lock"].locked() else ...
            return processedData
        except KeyError as e:
            if e.args[0] == data["code"] and data["type"] == "host":
                print(f"Creating New Game... ({data['code']})")

                game = self.games[data["code"]] = {
                    "hostName": data["name"],
                    "joinName": "",
                    "pendingCoordinates": [],
                    "pendingGuesses": [],
                    "word": "",
                    "rounds": data["rounds"],
                    "roundTime": data["roundTime"],
                    "isDrawing": False,
                    "isGuessed": False,
                    "roundActive": True,
                    "gameActive": True,
                    "lock": Lock(),
                }

                self.newPlayer(game, "host", conn)
                return self.ABORT
            elif e.args[0] == "playerJoined" and data["type"] == "join":
                print(f"Joined game... ({data['code']})")
                game = self.games[data["code"]]
                game["joinName"] = data["name"]
                game["playerJoined"] = True

                game["lock"].release()

                self.newPlayer(game, "join", conn)
                return self.ABORT

            # TODO - handle error codes
            print("games:", self.games)
            print("data:", data)
            return self.FAIL

    def newPlayer(self, game, playerType, conn: socket.socket):
        self._sendToClient(conn, self.SUCCESS)
        if playerType == "host":
            while not game["joinName"]:
                pass
            self._sendToClient(conn, game["joinName"])
            self.hostSelectWord(game, conn)
        else:
            self._sendToClient(conn, (game["hostName"], game["rounds"], game["roundTime"]))
            self.joinSelectWord(game, conn)

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
