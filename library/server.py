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
                if not game["word"]:
                    game["lock"].release()
                    self.__hostSelectWord(game, conn)
                    processedData = self.ABORT
                else:
                    game["pendingCoordinates"].extend(data["pendingCoordinates"])
                    game["isDrawing"] = True if data["pendingCoordinates"] else data["isDrawing"]
                    processedData = tuple(game["pendingGuesses"])
                    game["pendingGuesses"].clear()
            elif game["playerJoined"]:
                if not game["word"]:
                    game["lock"].release()
                    self.__joinSelectWord(game, conn)
                    processedData = self.ABORT
                else:
                    game["pendingGuesses"].extend(data["pendingGuesses"])
                    processedData = game["isDrawing"], tuple(game["pendingCoordinates"])
                    game["pendingCoordinates"].clear()
            elif not game["playerJoined"]:
                print(f"Joined game... ({data['code']})")
                game["playerJoined"] = True
                processedData = self.SUCCESS
            else:
                processedData = None

            game["lock"].release() if game["lock"].locked() else ...
            return processedData
        except KeyError as e:
            if e.args[0] == data["code"]:
                if data["type"] == "host":
                    print(f"Creating New Game... ({data['code']})")

                    self.games[data["code"]] = {
                        "pendingCoordinates": [],
                        "pendingGuesses": [],
                        "word": "",
                        "isDrawing": False,
                        "playerJoined": False,
                        "gameActive": True
                    }

                    return self.SUCCESS
                else:
                    print(e)
                    return self.FAIL

            # TODO - handle error codes
            return None

    def __hostSelectWord(self, game, conn: socket.socket):
        words = self.getNRandomWords(3)
        self._sendToClient(conn, words)
        game["word"] = self._requestClient(conn)

    def __joinSelectWord(self, game, conn: socket.socket):
        self._sendToClient(conn, self.WAIT)
        while not game["word"]:
            pass
        self._sendToClient(conn, game["word"])

    def getNRandomWords(self, N):
        return random.sample(self.wordList, N)


if __name__ == '__main__':
    with open("wordlist.txt") as file:
        wordList = set(file.readline().split(", "))

    SkrableServer().run()
