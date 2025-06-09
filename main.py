import asyncio
import logging
import signal

from echo_server import EchoServer
from logger import prepare_logger

logger = logging.getLogger("echo_server")
logging.basicConfig(level=logging.DEBUG)


async def shutdown(echo_server: EchoServer, sig: signal.Signals | None = None) -> None:
    if sig:
        logger.info(f"Received exit signal {sig.name}...")
    logger.info("Starting server shutdown...")
    await echo_server.stop()
    logger.info("Server successfully shutdown")


async def main() -> None:
    prepare_logger(log_level="DEBUG")
    server = EchoServer("127.0.0.1", 8000)
    await server.start()
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        await server.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user")
