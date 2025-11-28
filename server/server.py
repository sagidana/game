
from protocol import protocol_pb2 as pb
from . import server
from . import client
import websockets
import asyncio


class Server():
    def __init__(self, port=8765):
        self.port = port
        self.connected_clients = {}
        self.connected_clients_lock = asyncio.Lock()

        self.__init_actions()

    async def propagate
    def client_move_up(self, client):
        x = client.position[0]
        y = client.position[1]


        print(f"[+] client: {client.user_id} is moving up")
    def client_move_down(self, client):
        print(f"[+] client: {client.user_id} is moving down")
    def client_move_right(self, client):
        print(f"[+] client: {client.user_id} is moving right")
    def client_move_left(self, client):
        print(f"[+] client: {client.user_id} is moving left")

    def __init_actions(self):
        self.actions = {}
        self.actions[pb.ActionType.MoveUp] = self.client_move_up
        self.actions[pb.ActionType.MoveDown] = self.client_move_down
        self.actions[pb.ActionType.MoveRight] = self.client_move_right
        self.actions[pb.ActionType.MoveLeft] = self.client_move_left

    async def client_loop(self, client, websocket):
        async for message_bytes in websocket:
            action = pb.Action()
            action.ParseFromString(message_bytes)

            if action.type == pb.ActionType.Disconnect: return

            if action.type in self.actions:
                self.actions[action.type](client)
            else:
                print(f"[!] client: {client.user_id} action ({action.type}) wasnt' found in supported actions.")

    async def handle_new_client(self, websocket):
        try:
            message_bytes = await websocket.recv()

            hello = pb.Hello()
            hello.ParseFromString(message_bytes)

            # TODO: add authentication
            user_id = hello.id
            # we might want to fetch that from db.
            current_client = client.Client(user_id, websocket)

            is_ok = False
            async with self.connected_clients_lock:
                if user_id not in self.connected_clients:
                    is_ok = True
                    self.connected_clients[user_id] = current_client

            if not is_ok:
                print(f"[!] client: {user_id} was trying to connect twice")
                await websocket.send(pb.Bye(status=pb.Status.AlreadyConnected).SerializeToString())
                return

            await websocket.send(pb.Bye(status=pb.Status.Ok).SerializeToString())
            print(f"[+] client: {current_client.user_id} connected.")
            try:
                await self.client_loop(current_client, websocket)
            except Exception as e:
                print(f"[!] client_loop exception: {e}")
            finally:
                async with self.connected_clients_lock:
                    del self.connected_clients[user_id]
                print(f"[+] client: {current_client.user_id} disconnected.")
        except websockets.exceptions.ConnectionClosedOK: pass

    async def serve(self):
        async with websockets.serve(self.handle_new_client, "localhost", self.port):
            await asyncio.Future()  # Run forever


if __name__ == "__main__":
    server = Server()
    print(f"[+] serving...")
    asyncio.run(server.serve())
