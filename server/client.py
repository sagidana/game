class Client():
    def __init__(self, user_id, websocket, position):
        self.user_id = user_id
        self.websocket = websocket
        self.position = position
