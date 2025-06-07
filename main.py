import asyncio
import logging
import socket
from asyncio import AbstractEventLoop

logger = logging.getLogger("echo_server")
logging.basicConfig(level=logging.DEBUG)


def setup_server_socket(host: str, port: int) -> socket.socket:
    # IPv4, TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.setblocking(False)

    try:
        server_address = (host, port)
        server_socket.bind(server_address)
        logger.info("Server started on %s:%d", host, port)
        server_socket.listen()
    except Exception as e:
        server_socket.close()
        logger.error("Failed to start server: %s", e)
        raise RuntimeError("Error starting server: %s", e)

    return server_socket


async def listen_for_connections(
    server_socket: socket.socket, event_loop: AbstractEventLoop
) -> None:
    while True:
        client_connection, client_address = await event_loop.sock_accept(server_socket)
        client_connection.setblocking(False)
        logger.info("Connection request from %s", client_address)
        asyncio.create_task(echo(client_connection, event_loop))


async def echo(connection: socket.socket, event_loop: AbstractEventLoop) -> None:
    try:
        while data := await event_loop.sock_recv(connection, 1024):
            await event_loop.sock_sendall(connection, data)
    except Exception as e:
        logger.exception("Error occurred while handling connection: %s", e)
    finally:
        logger.info("Connection closed")
        connection.close()


async def main() -> None:
    loop = asyncio.get_running_loop()
    server_socket = setup_server_socket(host="127.0.0.1", port=8000)
    try:
        await listen_for_connections(server_socket, loop)
    finally:
        server_socket.close()
        logger.info("Server socket closed")


if __name__ == "__main__":
    asyncio.run(main())
