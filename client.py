import protocol_pb2 as pb
import websockets
import asyncio
import argparse
import termios
import sys
import tty


async def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = await asyncio.to_thread(sys.stdin.read, 1)
        # ch = sys.stdin.read(1)  # read one character
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

actions = {}

def action_down():
    return pb.Action(type=pb.ActionType.Movement,
                       movement_action=pb.MovementAction(direction=pb.MovementDirection.Down))
def action_up():
    return pb.Action(type=pb.ActionType.Movement,
                       movement_action=pb.MovementAction(direction=pb.MovementDirection.Up))
def action_right():
    return pb.Action(type=pb.ActionType.Movement,
                       movement_action=pb.MovementAction(direction=pb.MovementDirection.Right))
def action_left():
    return pb.Action(type=pb.ActionType.Movement,
                       movement_action=pb.MovementAction(direction=pb.MovementDirection.Left))

def init_actions(args):
    global actions

    actions['j'] = action_down
    actions['k'] = action_up
    actions['h'] = action_left
    actions['l'] = action_right

async def main(args):
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        hello = pb.Hello()
        hello.id = args.name

        await websocket.send(hello.SerializeToString())
        response_bytes = await websocket.recv()

        bye = pb.Bye()
        bye.ParseFromString(response_bytes)
        if bye.status != pb.Status.Ok:
            print(f"[!] server returned: {bye.status=}")
            return

        while True:
            global actions
            key = await getch()

            print(f"[+] {key=}")
            if key == '\x03': break; # ctrl-c

            action = actions.get(key, None)
            if not action: continue

            try:
                buffer = action()
                await websocket.send(buffer.SerializeToString())
            except Exception as e:
                print(f"[!] Exception: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Client arguments")
    parser.add_argument("name", help="Your name")

    args = parser.parse_args()

    init_actions(args)

    asyncio.run(main(args))
