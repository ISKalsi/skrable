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
            if "lock" not in game.keys():
                game["lock"] = Lock()

            game["lock"].acquire()

            if data["exitCode"] != self.SUCCESS:
                if data["exitCode"] == self.EXIT:
                    game["gameActive"] = False
                    return self.SUCCESS
                else:
                    return self.FAIL

            if not game["gameActive"]:
                return self.EXIT

            if data["type"] == "host":
                game["pendingCoordinates"].extend(data["pendingCoordinates"])
                game["isDrawing"] = True if data["pendingCoordinates"] else data["isDrawing"]
                processedData = tuple(game["pendingGuesses"])
                game["pendingGuesses"].clear()
            elif game["playerJoined"]:
                game["pendingGuesses"].extend(data["pendingGuesses"])
                processedData = game["isDrawing"], tuple(game["pendingCoordinates"])
                game["pendingCoordinates"].clear()
            else:
                raise Exception(f"Could not process data, [{data}]")

            game["lock"].release() if game["lock"].locked() else ...
            return processedData
        except KeyError as e:
            if e.args[0] == data["code"]:
                if data["type"] == "host":
                    print(f"Creating New Game... ({data['code']})")

                    game = self.games[data["code"]] = {
                        "hostName": data["name"],
                        "joinName": "",
                        "pendingCoordinates": [],
                        "pendingGuesses": [],
                        "word": "",
                        "isDrawing": False,
                        "gameActive": True
                    }

                    self.newPlayer(game, "host", conn)
                    return self.ABORT
                else:
                    print(e, data)
                    return self.FAIL
            elif e.args[0] == "playerJoined":
                if data["type"] == "join":
                    print(f"Joined game... ({data['code']})")
                    game = self.games[data["code"]]
                    game["joinName"] = data["name"]
                    game["playerJoined"] = True

                    game["lock"].release()

                    self.newPlayer(game, "join", conn)
                    return self.ABORT
                else:
                    print(e, data)
                    return self.FAIL

            # TODO - handle error codes
            raise e

    def newPlayer(self, game, playerType, conn: socket.socket):
        self._sendToClient(conn, self.SUCCESS)
        if playerType == "host":
            while not game["joinName"]:
                pass
            self._sendToClient(conn, game["joinName"])
            self.hostSelectWord(game, conn)
        else:
            self._sendToClient(conn, game["hostName"])
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
