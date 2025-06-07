import asyncio
import logging
import socket

import pytest
from _pytest.logging import LogCaptureFixture

from main import setup_server_socket, listen_for_connections


class TestIntegration:
    @pytest.fixture
    def get_host(self) -> str:
        return "127.0.0.1"

    @pytest.fixture
    def get_port(self) -> int:
        return 8000

    @pytest.fixture
    def test_data(self) -> bytes:
        return b"test data"

    def test_real_socket_creation(self, get_host: str, get_port: int) -> None:
        server_socket = setup_server_socket(host=get_host, port=get_port)

        assert isinstance(server_socket, socket.socket)
        assert server_socket.getsockname() == (get_host, get_port)
        server_socket.close()

    def test_real_socket_fail(self, get_host: str, get_port: int) -> None:
        dummy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dummy_socket.bind((get_host, get_port))

        with pytest.raises(RuntimeError, match="Error starting server:"):
            setup_server_socket(host=get_host, port=get_port)

        dummy_socket.close()

    @pytest.mark.asyncio
    async def test_full_echo_cycle(
        self, get_host: str, get_port: int, test_data: bytes
    ) -> None:
        server_socket = setup_server_socket(host=get_host, port=get_port)
        event_loop = asyncio.get_event_loop()
        server_task = asyncio.create_task(
            listen_for_connections(server_socket=server_socket, event_loop=event_loop)
        )

        try:
            reader, writer = await asyncio.open_connection(get_host, get_port)
            writer.write(test_data)
            await writer.drain()

            response = await reader.read(1024)
            assert response == test_data
        finally:
            server_task.cancel()
            server_socket.close()
            await asyncio.sleep(0.1)

    @pytest.mark.asyncio
    async def test_multiple_clients_connection(
        self, get_host: str, get_port: int
    ) -> None:
        server_socket = setup_server_socket(host=get_host, port=get_port)
        event_loop = asyncio.get_event_loop()
        server_task = asyncio.create_task(
            listen_for_connections(server_socket=server_socket, event_loop=event_loop)
        )

        try:

            async def client_session(data: bytes) -> bytes:
                reader, writer = await asyncio.open_connection(get_host, get_port)
                writer.write(data)
                await writer.drain()

                response = await reader.read(1024)
                writer.close()
                await writer.wait_closed()
                return response

            test_data = [b"test_data1", b"test_data2", b"test_data3"]
            results = await asyncio.gather(
                *[client_session(data) for data in test_data]
            )
            assert test_data == results
        finally:
            server_task.cancel()
            server_socket.close()
            await asyncio.sleep(0.1)

    @pytest.mark.asyncio
    async def test_server_logging(
        self, get_host: str, get_port: int, caplog: LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.INFO):
            loop = asyncio.get_running_loop()
            server_socket = setup_server_socket(host=get_host, port=get_port)

            assert f"Server started on {get_host}:{get_port}" in caplog.text
            server_task = asyncio.create_task(
                listen_for_connections(server_socket, loop)
            )

            try:
                reader, writer = await asyncio.open_connection(get_host, get_port)
                writer.write(b"test logging")
                await writer.drain()
                assert "Connection request from" in caplog.text

                await reader.read(1024)
                writer.close()
                await writer.wait_closed()
            finally:
                server_task.cancel()
                server_socket.close()
                await asyncio.sleep(0.1)
                assert "Connection closed" in caplog.text
