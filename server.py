import protocol_pb2 as pb
import websockets
import asyncio


async def client_loop(client, websocket):
    async for message_bytes in websocket:
        action = pb.Action()
        action.ParseFromString(message_bytes)

        if action.type == pb.ActionType.Disconnect: return

        if action.type == pb.ActionType.KeepAlive:
            print(f"[+] {client}: keepalive")
            pass

        if action.type == pb.ActionType.Movement:
            if not action.HasField('movement_action'):
                print(f"[!] action type is movement, without movement_action set.")
                return
            if action.movement_action.direction == pb.MovementDirection.Up: print(f"[+] {client}: up")
            if action.movement_action.direction == pb.MovementDirection.Down: print(f"[+] {client}: down")
            if action.movement_action.direction == pb.MovementDirection.Left: print(f"[+] {client}: left")
            if action.movement_action.direction == pb.MovementDirection.Right: print(f"[+] {client}: right")

async def handle_connection(websocket):
    try:
        async for message_bytes in websocket:
            hello = pb.Hello()
            hello.ParseFromString(message_bytes)

            client = hello.id
            await websocket.send(pb.Bye(status=pb.Status.Ok).SerializeToString())

            break
        await client_loop(client, websocket)
    except websockets.exceptions.ConnectionClosedOK:
        pass
    print("Client disconnected.")


async def main():
    async with websockets.serve(handle_connection, "localhost", 8765):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    print("Starting WebSocket server on ws://localhost:8765")
    asyncio.run(main())
