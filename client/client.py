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
    def __init__(self, args):
        self.args = args
        self.to_exit = False
        self.send_queue = queue.Queue()
        self.screen_queue = queue.Queue()
        self.init_actions()
        self.screen = screen.Screen(self.screen_queue)

        thread = threading.Thread(target=self.screen.run)
        thread.start()

    def action_down(self):
        return pb.Action(type=pb.ActionType.MoveDown)
    def action_up(self):
        return pb.Action(type=pb.ActionType.MoveUp)
    def action_right(self):
        return pb.Action(type=pb.ActionType.MoveRight)
    def action_left(self):
        return pb.Action(type=pb.ActionType.MoveLeft)

    def init_actions(self):
        self.actions = {}

        self.actions['j'] = self.action_down
        self.actions['k'] = self.action_up
        self.actions['h'] = self.action_left
        self.actions['l'] = self.action_right

    def actions_loop(self, websocket):
        while not self.to_exit:
            key = sys.stdin.read(1)

            log.glog(f"[+] {key=}")
            if key == '\x03':
                self.send_queue.put([0])
                break; # ctrl-c

            action = self.actions.get(key, None)
            if not action: continue

            buffer = action()
            if buffer:
                self.send_queue.put([1, buffer.SerializeToString()])

    async def sender(self, websocket):
        while True:
            try:
                key = await asyncio.to_thread(sys.stdin.read, 1)

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
        log.glog(f"[+] sender handler finished.")

    async def receiver(self, websocket):
        async for message_bytes in websocket:
            try:
                update = pb.Update()
                update.ParseFromString(message_bytes)

                for player_update in update.players_updates:
                    self.screen_queue.put([2, player_update.id, player_update.x, player_update.y])
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
            self.screen_queue.put([1]) # signal screen thread to exit
            log.glog(f"[+] runner finished.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Client arguments")
    parser.add_argument("name", help="Your name")

    args = parser.parse_args()

    client = Client(args)

    asyncio.run(client.run())

