import asyncio
import socket
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture

from echo_server import EchoServer


class TestEchoServer:
    @pytest.fixture
    def get_host(self) -> str:
        return "127.0.0.1"

    @pytest.fixture
    def get_port(self) -> int:
        return 8000

    def test_socket_creation_success(
        self, mocker: MockerFixture, get_host: str, get_port: int
    ) -> None:
        mock_socket = mocker.patch("socket.socket")
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance
        server = EchoServer(host=get_host, port=get_port)
        result = server._setup_server_socket()
        mock_socket.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
        mock_socket_instance.setsockopt.assert_called_once_with(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
        )
        mock_socket_instance.setblocking.assert_called_once_with(False)
        mock_socket_instance.bind.assert_called_once_with((get_host, get_port))
        mock_socket_instance.listen.assert_called_once()
        assert result == mock_socket_instance

    def test_socket_creation_failure(
        self, mocker: MockerFixture, get_host: str, get_port: int
    ) -> None:
        mock_socket = mocker.patch("socket.socket")
        mock_socket_instance = MagicMock()
        mock_socket_instance.bind.side_effect = OSError("Port in use")
        mock_socket.return_value = mock_socket_instance
        server = EchoServer(host=get_host, port=get_port)
        with pytest.raises(RuntimeError, match="Error starting server"):
            server._setup_server_socket()
        mock_socket_instance.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_echo_handler(self) -> None:
        mock_conn = MagicMock()
        mock_loop = MagicMock(spec=asyncio.AbstractEventLoop)
        mock_loop.sock_recv = AsyncMock(side_effect=[b"test data", b""])
        mock_loop.sock_sendall = AsyncMock()
        await EchoServer._echo(mock_conn, mock_loop)
        assert mock_loop.sock_recv.await_count == 2
        mock_loop.sock_sendall.assert_awaited_once_with(mock_conn, b"test data")
        mock_conn.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_echo_handler_disconnect(self) -> None:
        mock_conn = MagicMock()
        mock_loop = MagicMock(spec=asyncio.AbstractEventLoop)
        mock_loop.sock_recv = AsyncMock(
            side_effect=ConnectionResetError("Client disconnected")
        )
        await EchoServer._echo(mock_conn, mock_loop)
        mock_loop.sock_recv.assert_awaited_once_with(mock_conn, 1024)
        mock_conn.close.assert_called_once()
