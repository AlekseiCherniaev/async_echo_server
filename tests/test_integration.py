import asyncio
import logging
import socket

import pytest
from _pytest.logging import LogCaptureFixture

from echo_server import EchoServer


class TestIntegration:
    @pytest.fixture
    def get_host(self) -> str:
        return "127.0.0.1"

    @pytest.fixture
    def get_port(self) -> int:
        return 8005

    @pytest.fixture
    def test_data(self) -> bytes:
        return b"test data"

    def test_real_socket_creation(self, get_host: str, get_port: int) -> None:
        echo_server = EchoServer(host=get_host, port=get_port)
        server_socket = echo_server._setup_server_socket()

        assert isinstance(server_socket, socket.socket)
        assert server_socket.getsockname() == (get_host, get_port)
        server_socket.close()

    def test_real_socket_fail(self, get_host: str, get_port: int) -> None:
        dummy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dummy_socket.bind((get_host, get_port))

        with pytest.raises(RuntimeError, match="Error starting server:"):
            echo_server = EchoServer(host=get_host, port=get_port)
            echo_server._setup_server_socket()

        dummy_socket.close()

    @pytest.mark.asyncio
    async def test_full_echo_cycle(
        self, get_host: str, get_port: int, test_data: bytes
    ) -> None:
        echo_server = EchoServer(host=get_host, port=get_port)
        try:
            await echo_server.start()
            reader, writer = await asyncio.open_connection(get_host, get_port)
            writer.write(test_data)
            await writer.drain()

            response = await reader.read(1024)
            assert response == test_data

            writer.close()
            await writer.wait_closed()
        finally:
            await echo_server.stop()
            await asyncio.sleep(0)

    @pytest.mark.asyncio
    async def test_multiple_clients_connection(
        self, get_host: str, get_port: int
    ) -> None:
        echo_server = EchoServer(host=get_host, port=get_port)
        try:
            await echo_server.start()

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
            await echo_server.stop()
            await asyncio.sleep(0)

    @pytest.mark.asyncio
    async def test_server_logging(
        self, get_host: str, get_port: int, caplog: LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.INFO):
            echo_server = EchoServer(host=get_host, port=get_port)
            try:
                await echo_server.start()
                assert f"Server started on {get_host}:{get_port}" in caplog.text

                reader, writer = await asyncio.open_connection(get_host, get_port)
                writer.write(b"test logging")
                await writer.drain()
                assert "Connection request from" in caplog.text

                await reader.read(1024)
                writer.close()
                await writer.wait_closed()

                await asyncio.sleep(0)
            finally:
                await echo_server.stop()
