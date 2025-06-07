import socket

import pytest

from main import setup_server_socket


class TestIntegration:
    @pytest.fixture
    def get_host(self) -> str:
        return "127.0.0.1"

    @pytest.fixture
    def get_port(self) -> int:
        return 8000

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
