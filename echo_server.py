import asyncio
import logging
import socket
from asyncio import AbstractEventLoop

logger = logging.getLogger("echo_server")


class EchoServer:
    """Initializes the EchoServer with host and port."""

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.server_socket: socket.socket | None = None
        self.server_task: asyncio.Task[None] | None = None
        self.connections: set[asyncio.Task[None]] = set()

    async def start(self) -> None:
        """Starts the echo server."""
        self.server_socket = self._setup_server_socket()
        loop = asyncio.get_running_loop()
        self.server_task = asyncio.create_task(self._listen_for_connections(loop))

    async def stop(self) -> None:
        """Stops the echo server gracefully."""
        if self.server_task:
            self.server_task.cancel()
            try:
                await self.server_task
            except asyncio.CancelledError:
                pass

        for task in self.connections:
            task.cancel()

        if self.server_socket:
            self.server_socket.close()
            logger.info("Server socket closed")

    def _setup_server_socket(self) -> socket.socket:
        """Creates and configures the server socket."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.setblocking(False)
        try:
            server_address = (self.host, self.port)
            server_socket.bind(server_address)
            logger.info("Server started on %s:%d", self.host, self.port)
            server_socket.listen()
        except Exception as e:
            server_socket.close()
            logger.error("Failed to start server: %s", e)
            raise RuntimeError(f"Error starting server: {e}")
        return server_socket

    async def _listen_for_connections(self, event_loop: AbstractEventLoop) -> None:
        """Listens for incoming connections and spawns echo handlers."""
        try:
            if self.server_socket is None:
                raise RuntimeError("Server socket is not initialized")
            while True:
                client_connection, client_address = await event_loop.sock_accept(
                    self.server_socket
                )
                client_connection.setblocking(False)
                logger.info("Connection request from %s", client_address)
                task = asyncio.create_task(self._echo(client_connection, event_loop))
                self.connections.add(task)
        except Exception as e:
            logger.exception("Error in connection listener: %s", e)

    @staticmethod
    async def _echo(connection: socket.socket, event_loop: AbstractEventLoop) -> None:
        """Handles an individual client connection by echoing received data."""
        try:
            while data := await event_loop.sock_recv(connection, 1024):
                await event_loop.sock_sendall(connection, data)
        except (ConnectionResetError, BrokenPipeError):
            logger.info("Client disconnected")
        except Exception as e:
            logger.exception("Error occurred while handling connection: %s", e)
        finally:
            logger.info("Connection closed")
            connection.close()
