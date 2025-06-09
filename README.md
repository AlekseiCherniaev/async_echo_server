# Async Echo Server

A simple asynchronous echo server in Python that returns received data back to clients.

## Features

- Asynchronous connection handling using `asyncio`
- Support for multiple concurrent connections
- Proper shutdown signal handling

## Running the Server

```bash
  python -m main
```
Press Ctrl+C to gracefully shutdown the server.

## Testing
```bash
  pytest
```