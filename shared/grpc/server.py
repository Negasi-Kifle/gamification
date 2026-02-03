"""gRPC Server for the Gamification service.

This module provides the single gRPC server entry point that registers
all module servicers (Bonus, CRM, Loyalty, etc.).

Usage:
    python -m shared.grpc.server

Environment Variables:
    GRPC_PORT: Port to listen on (default: 50051)
    GRPC_MAX_WORKERS: Maximum number of worker threads (default: 10)
"""

import logging
import os
from concurrent import futures

import grpc

logger = logging.getLogger(__name__)


def _setup_django():
    """Set up Django if not already configured."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gamification.settings")

    import django
    from django.apps import apps

    if not apps.ready:
        django.setup()


def create_server(port: int = 50051, max_workers: int = 10) -> grpc.Server:
    """
    Create and configure the gRPC server with all module servicers.

    Args:
        port: Port number to listen on
        max_workers: Maximum number of worker threads

    Returns:
        Configured gRPC server instance
    """
    # Ensure Django is set up before importing Django-dependent modules
    _setup_django()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))

    # Register all module servicers
    _register_bonus_servicer(server)

    # Add insecure port (use secure channel in production)
    server.add_insecure_port(f"[::]:{port}")

    return server


# Register all module servicers
def _register_bonus_servicer(server: grpc.Server) -> None:
    """Register the Bonus module gRPC servicer."""
    from bonus.src.Infrastructure.repository import DjangoCasinoFreeBetRepository
    from bonus.src.Presentation.grpc import CasinoFreeBetServicer
    from shared.grpc import bonus_pb2_grpc

    repository = DjangoCasinoFreeBetRepository()
    servicer = CasinoFreeBetServicer(repository)
    bonus_pb2_grpc.add_CasinoFreeBetServiceServicer_to_server(servicer, server)

    logger.info("Registered Bonus module gRPC servicer")


def serve():
    """Start the gRPC server and block until termination."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Get configuration from environment
    port = int(os.environ.get("GRPC_PORT", "50051"))
    max_workers = int(os.environ.get("GRPC_MAX_WORKERS", "10"))

    # Create and start server
    server = create_server(port=port, max_workers=max_workers)
    server.start()

    logger.info(f"gRPC server started on port {port} with {max_workers} workers")
    logger.info("Registered services: Bonus")
    logger.info("Press Ctrl+C to stop the server")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server...")
        server.stop(grace=5)  # 5 second grace period
        logger.info("gRPC server stopped")


if __name__ == "__main__":
    serve()
