class Client():
    def __init__(self, user_id, socket, position=(0,0)):
        self.user_id = user_id
        self.socket = socket
        self.position = position
