import logging
import socket

logger = logging.getLogger("echo_server")
logging.basicConfig(level=logging.DEBUG)


def setup_server_socket(host: str, port: int) -> socket.socket:
    #  IPv4, TCP
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
        logger.exception("Failed to start server: %s", e)
        raise RuntimeError(f"Error starting server: {e}")

    return server_socket


def main() -> None:
    setup_server_socket(host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
