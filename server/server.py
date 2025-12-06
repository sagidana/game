
from protocol import protocol_pb2 as pb
from . import server
from . import client
import websockets
import asyncio
import time

from functools import wraps

def propagate(func):
    @wraps(func)
    async def wrapper(self, client):
        result = await func(self, client)

        action_name = ''.join([name.capitalize() for name in func.__name__.split('_')[1:]])
        action = getattr(pb.ActionType, action_name)

        update = pb.PlayerUpdate(   id=client.user_id,
                                    x=client.position[0],
                                    y=client.position[1],
                                    action=action)
        await self.tick_queue.put(update)
        return result
    return wrapper
    # return decorator

class Server():
    def __init__(self, port=8765, ticks=30):
        self.to_exit = False
        self.ticks = ticks
        self.tick_queue = asyncio.Queue()
        self.port = port
        self.connected_clients = {}
        self.connected_clients_lock = asyncio.Lock()

        self.__load_map()

        self.__init_actions()

    def __init_actions(self):
        self.actions = {}
        self.actions[pb.ActionType.Disconnect] = self.client_disconnect
        self.actions[pb.ActionType.MoveUp] = self.client_move_up
        self.actions[pb.ActionType.MoveDown] = self.client_move_down
        self.actions[pb.ActionType.MoveRight] = self.client_move_right
        self.actions[pb.ActionType.MoveLeft] = self.client_move_left
        self.actions[pb.ActionType.HalfDashLeft] = self.client_half_dash_left
        self.actions[pb.ActionType.FullDashLeft] = self.client_full_dash_left
        self.actions[pb.ActionType.HalfDashRight] = self.client_half_dash_right
        self.actions[pb.ActionType.FullDashRight] = self.client_full_dash_right
        self.actions[pb.ActionType.HalfDashUp] = self.client_half_dash_up
        self.actions[pb.ActionType.FullDashUp] = self.client_full_dash_up
        self.actions[pb.ActionType.HalfDashDown] = self.client_half_dash_down
        self.actions[pb.ActionType.FullDashDown] = self.client_full_dash_down

    def __load_map(self):
        self.map = []
        with open('server/map') as map_file:
            for line in map_file.readlines():
                line = line.strip()
                self.map.append([ord(c) for c in line])

        self.map_data = []
        for raw in self.map:
            self.map_data.extend(raw)

    @propagate
    async def client_disconnect(self, client):
        return True
    @propagate
    async def client_move_up(self, client):
        client.position[1] = max(0, client.position[1] - 1)
        print(f"[+] client: {client.user_id} is moving up")
        return False
    @propagate
    async def client_move_down(self, client):
        print(f"[+] client: {client.user_id} is moving down")
        client.position[1] += 1
        return False
    @propagate
    async def client_move_right(self, client):
        client.position[0] =client.position[0] + 1
        print(f"[+] client: {client.user_id} is moving right")
        return False
    @propagate
    async def client_move_left(self, client):
        client.position[0] = max(0, client.position[0] - 1)
        print(f"[+] client: {client.user_id} is moving left")
        return False
    @propagate
    async def client_half_dash_left(self, client):
        client.position[0] = max(0, client.position[0] - 4)
        print(f"[+] client: {client.user_id} is half dash left")
        return False
    @propagate
    async def client_full_dash_left(self, client):
        client.position[0] = max(0, client.position[0] - 8)
        print(f"[+] client: {client.user_id} is full dash left")
        return False
    @propagate
    async def client_half_dash_right(self, client):
        client.position[0] = max(0, client.position[0] + 4)
        print(f"[+] client: {client.user_id} is half dash right")
        return False
    @propagate
    async def client_full_dash_right(self, client):
        client.position[0] = max(0, client.position[0] + 8)
        print(f"[+] client: {client.user_id} is full dash right")
        return False
    @propagate
    async def client_half_dash_up(self, client):
        client.position[1] = max(0, client.position[1] - 4)
        print(f"[+] client: {client.user_id} is half dash up")
        return False
    @propagate
    async def client_full_dash_up(self, client):
        client.position[1] = max(0, client.position[1] - 8)
        print(f"[+] client: {client.user_id} is full dash up")
        return False
    @propagate
    async def client_half_dash_down(self, client):
        client.position[1] = max(0, client.position[1] + 4)
        print(f"[+] client: {client.user_id} is half dash down")
        return False
    @propagate
    async def client_full_dash_down(self, client):
        client.position[1] = max(0, client.position[1] + 8)
        print(f"[+] client: {client.user_id} is full dash down")
        return False

    async def client_loop(self, client):
        # first update to each client is the map and its current location
        map_update = pb.MapUpdate(x=0, y=0, width=len(self.map[0]), height=len(self.map), data=self.map_data)
        current = pb.PlayerUpdate(id=client.user_id, x=client.position[0], y=client.position[1])
        server_message = pb.ServerMessage(map_update=map_update, current=current)
        await client.websocket.send(server_message.SerializeToString())

        async for message_bytes in client.websocket:
            player_message = pb.PlayerMessage()
            player_message.ParseFromString(message_bytes)

            if player_message.action in self.actions:
                to_exit = await self.actions[player_message.action](client)
                if to_exit: break
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
                await self.client_loop(current_client)
            except Exception as e:
                print(f"[!] client_loop exception: {e}")
            finally:
                async with self.connected_clients_lock:
                    del self.connected_clients[user_id]
                print(f"[+] client: {current_client.user_id} disconnected.")
        except websockets.exceptions.ConnectionClosedOK: pass

    async def drain_updates_queue(self):
        items = []
        try:
            while True:
                items.append(self.tick_queue.get_nowait())
        except asyncio.QueueEmpty: pass
        return items

    async def tick(self):
        players_updates = await self.drain_updates_queue()

        async with self.connected_clients_lock: # lock the list so new clients wont interrupt.
            # construct the update to all players
            for curr_user_id in self.connected_clients:
                # exclude this user from its own updates.
                curr_updates = [update for update in players_updates if update.id != curr_user_id]

                c = self.connected_clients[curr_user_id]
                current = pb.PlayerUpdate(id=c.user_id, x=c.position[0], y=c.position[1])
                server_message = pb.ServerMessage(current=current, players_updates=curr_updates)
                await self.connected_clients[curr_user_id].websocket.send(server_message.SerializeToString())

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
