from protocol import protocol_pb2 as pb
from . import log
import threading
import websockets
import asyncio
import argparse
import queue
import sys

from . import screen

class Client():
    def __init__(self, args, main_loop):
        self.main_loop = main_loop
        self.args = args
        self.updates_queue = asyncio.Queue()
        self.input_queue = asyncio.Queue()
        self.init_actions()
        self.screen = screen.Screen(self.input_queue,
                                    self.updates_queue,
                                    self.main_loop)

        thread = threading.Thread(target=self.screen.run)
        thread.start()

    def action_down(self):
        return pb.PlayerMessage(action=pb.ActionType.MoveDown)
    def action_up(self):
        return pb.PlayerMessage(action=pb.ActionType.MoveUp)
    def action_right(self):
        return pb.PlayerMessage(action=pb.ActionType.MoveRight)
    def action_left(self):
        return pb.PlayerMessage(action=pb.ActionType.MoveLeft)

    def init_actions(self):
        self.actions = {}

        self.actions['j'] = self.action_down
        self.actions['k'] = self.action_up
        self.actions['h'] = self.action_left
        self.actions['l'] = self.action_right

    async def sender(self, websocket):
        while True:
            try:
                key = await self.input_queue.get()

                log.glog(f"[+] {key=}")
                if key == '\x03':
                    await websocket.close()
                    break; # ctrl-c

                action = self.actions.get(key, None)
                if not action: continue

                buffer = action()
                if buffer:
                    await websocket.send(buffer.SerializeToString())
            except Exception as e:
                log.glog(f"[!] sender handler exception: {e}")
                break
        log.glog(f"[+] sender handler finished.")

    async def receiver(self, websocket):
        async for message_bytes in websocket:
            log.glog(f"[+] got update from server")
            try:
                server_message = pb.ServerMessage()
                server_message.ParseFromString(message_bytes)

                for player_update in server_message.players_updates:
                    await self.updates_queue.put([2, player_update.id, player_update.x, player_update.y])
            except Exception as e:
                log.glog(f"{e=}")
        log.glog(f"[+] receiver handler finished.")

    async def run(self):
        uri = "ws://localhost:8765"
        try:
            async with websockets.connect(uri) as websocket:
                hello = pb.Hello()
                hello.id = self.args.name

                await websocket.send(hello.SerializeToString())
                response_bytes = await websocket.recv()

                bye = pb.Bye()
                bye.ParseFromString(response_bytes)
                if bye.status != pb.Status.Ok:
                    log.glog(f"[!] server returned: {bye.status=}")
                    return

                await asyncio.gather(self.receiver(websocket), self.sender(websocket))
        except Exception as e:
            log.glog(f"[!] run() exception: {e}")
        finally:
            await self.updates_queue.put([1]) # signal screen thread to exit
            log.glog(f"[+] runner finished.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Client arguments")
    parser.add_argument("name", help="Your name")

    args = parser.parse_args()

    main_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(main_loop)

    client = Client(args, main_loop)
    main_loop.run_until_complete(client.run())
