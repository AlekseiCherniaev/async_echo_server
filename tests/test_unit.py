import socket

import pytest
from pytest_mock import MockerFixture

from main import setup_server_socket


class TestServerSocket:
    @pytest.fixture
    def get_host(self) -> str:
        return "127.0.0.1"

    @pytest.fixture
    def get_port(self) -> int:
        return 8000

    def test_successful_socket_creation(
        self, mocker: MockerFixture, get_host: str, get_port: int
    ) -> None:
        mock_socket = mocker.patch("socket.socket")
        mock_socket_instance = mock_socket.return_value

        result = setup_server_socket(host=get_host, port=get_port)
        mock_socket.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
        mock_socket_instance.setsockopt.assert_called_once_with(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
        )
        mock_socket_instance.setblocking.assert_called_once_with(False)
        mock_socket_instance.bind.assert_called_once_with((get_host, get_port))
        mock_socket_instance.listen.assert_called_once()

        assert result == mock_socket_instance

    def test_failed_socket_creation(
        self, mocker: MockerFixture, get_host: str, get_port: int
    ) -> None:
        mock_socket = mocker.patch("socket.socket")
        mock_socket_instance = mock_socket.return_value
        mock_socket_instance.bind.side_effect = OSError("Port already in use")

        with pytest.raises(RuntimeError, match="Error starting server"):
            setup_server_socket(host=get_host, port=get_port)

        mock_socket_instance.close.assert_called_once()
