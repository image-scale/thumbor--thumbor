"""Tornado application and server for the image service."""

import argparse
import asyncio
import signal
import sys

import tornado.web
import tornado.ioloop

from imgsvc.config import Config
from imgsvc.context import ServerContext
from imgsvc.handlers import ImageHandler, HealthHandler


def make_app(context):
    """
    Create the Tornado application.

    Args:
        context: ServerContext instance

    Returns:
        tornado.web.Application
    """
    return tornado.web.Application([
        (r"/health/?", HealthHandler),
        (r"/(.+)", ImageHandler, {"context": context}),
    ], debug=context.config.DEBUG)


async def run_server(config):
    """
    Run the image service server.

    Args:
        config: Config instance
    """
    context = ServerContext(config)
    app = make_app(context)

    server = app.listen(config.PORT, config.HOST)

    print(f"Image service running at http://{config.HOST}:{config.PORT}")
    print(f"Health check: http://{config.HOST}:{config.PORT}/health")

    if config.ALLOW_UNSAFE_URL:
        print("WARNING: Unsafe URLs are enabled")
    else:
        print("URL signing required (security key set)")

    shutdown_event = asyncio.Event()

    def handle_signal():
        print("\nShutting down...")
        shutdown_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, handle_signal)

    await shutdown_event.wait()

    server.stop()
    await asyncio.sleep(0.1)


def main():
    """Entry point for the image service."""
    parser = argparse.ArgumentParser(description="Image transformation service")
    parser.add_argument(
        "-c", "--config",
        help="Path to configuration file",
        default=None
    )
    parser.add_argument(
        "-p", "--port",
        type=int,
        help="Port to listen on",
        default=None
    )
    parser.add_argument(
        "-H", "--host",
        help="Host to bind to",
        default=None
    )
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    parser.add_argument(
        "-k", "--security-key",
        help="Security key for URL signing",
        default=None
    )

    args = parser.parse_args()

    if args.config:
        config = Config.from_file(args.config)
    else:
        config = Config.from_environment()

    if args.port:
        config.PORT = args.port
    if args.host:
        config.HOST = args.host
    if args.debug:
        config.DEBUG = True
    if args.security_key:
        config.SECURITY_KEY = args.security_key
        config.ALLOW_UNSAFE_URL = False

    try:
        asyncio.run(run_server(config))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
