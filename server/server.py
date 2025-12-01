
from protocol import protocol_pb2 as pb
from . import server
from . import client
import websockets
import asyncio
import time


class Server():
    def __init__(self, port=8765, ticks=5):
        self.to_exit = False
        self.ticks = ticks
        self.port = port
        self.connected_clients = {}
        self.connected_clients_lock = asyncio.Lock()

        self.__init_actions()

    async def client_move_up(self, client):
        client.position[1] = max(0, client.position[1] - 1)
        print(f"[+] client: {client.user_id} is moving up")
        update = pb.ServerMessage(players_updates=[
                        pb.PlayerUpdate(id=client.user_id,
                                        x=client.position[0],
                                        y=client.position[1])
                        ])
        return update.SerializeToString()
    async def client_move_down(self, client):
        client.position[1] += 1
        print(f"[+] client: {client.user_id} is moving down")
        update = pb.ServerMessage(players_updates=[
                        pb.PlayerUpdate(id=client.user_id,
                                        x=client.position[0],
                                        y=client.position[1])
                        ])
        return update.SerializeToString()
    async def client_move_right(self, client):
        client.position[0] =client.position[0] + 1
        print(f"[+] client: {client.user_id} is moving right")

        update = pb.ServerMessage(players_updates=[
                        pb.PlayerUpdate(id=client.user_id,
                                        x=client.position[0],
                                        y=client.position[1])
                        ])
        return update.SerializeToString()
    async def client_move_left(self, client):
        client.position[0] = max(0, client.position[0] - 1)
        print(f"[+] client: {client.user_id} is moving left")
        update = pb.ServerMessage(players_updates=[
                        pb.PlayerUpdate(id=client.user_id,
                                        x=client.position[0],
                                        y=client.position[1])
                        ])
        return update.SerializeToString()

    def __init_actions(self):
        self.actions = {}
        self.actions[pb.ActionType.MoveUp] = self.client_move_up
        self.actions[pb.ActionType.MoveDown] = self.client_move_down
        self.actions[pb.ActionType.MoveRight] = self.client_move_right
        self.actions[pb.ActionType.MoveLeft] = self.client_move_left

    async def client_loop(self, client, websocket):
        async for message_bytes in websocket:
            player_message = pb.PlayerMessage()
            player_message.ParseFromString(message_bytes)

            if player_message.action == pb.ActionType.Disconnect: return

            if player_message.action in self.actions:
                buffer = await self.actions[player_message.action](client)
                if buffer:
                    await client.websocket.send(buffer)
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
            current_client = client.Client(user_id, websocket, position=[0,0])

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

    async def tick(self):
        async with self.connected_clients_lock:
            # construct the update to all players
            players_updates = []
            for user_id in self.connected_clients:
                c = self.connected_clients[user_id]
                players_updates.append(pb.PlayerUpdate(id=c.user_id, x=c.position[0], y=c.position[1]))
            server_message = pb.ServerMessage(players_updates=players_updates)

            for user_id in self.connected_clients:
                await self.connected_clients[user_id].websocket.send(server_message.SerializeToString())

    async def ticks_loop(self):
        last_tick = 0

        while not self.to_exit:
            passed = time.time() - last_tick

            time_needed_to_wait = (1.0 / self.ticks) - passed

            if time_needed_to_wait > 0: await asyncio.sleep(time_needed_to_wait)

            last_tick = time.time()

            try:
                await self.tick()
            except Exception as e:
                print(f"tick throw exception: {e}")

    async def serve(self):
        async with websockets.serve(self.handle_new_client, "localhost", self.port):
            await self.ticks_loop() # Run forever


if __name__ == "__main__":
    server = Server()
    print(f"[+] serving...")
    try:
        asyncio.run(server.serve())
    except KeyboardInterrupt:
        print(f"[+] CTRL-C closing server")
