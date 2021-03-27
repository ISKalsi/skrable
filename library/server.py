from library.network import Server


class SkrableServer(Server):
    def __init__(self):
        super().__init__()
        self.games = {}

    def processData(self, data, addr):
        if data is None:
            return self.FAIL

        try:
            game = self.games[data["code"]]

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
                print(f"Joined game... ({data['code']})")
                game["playerJoined"] = True
                processedData = self.SUCCESS

            return processedData
        except KeyError as e:
            if e.args[0] == data["code"]:
                if data["type"] == "host":
                    print(f"Creating New Game... ({data['code']})")

                    self.games[data["code"]] = {
                        "pendingCoordinates": [],
                        "pendingGuesses": [],
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


if __name__ == '__main__':
    SkrableServer().run()
