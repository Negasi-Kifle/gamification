from .grpc import CasinoFreeBetServicer
from .REST import CasinoFreeBetDetailView, CasinoFreeBetListCreateView

__all__ = [
    # RESTful
    "CasinoFreeBetListCreateView",
    "CasinoFreeBetDetailView",
    # gRPC
    "CasinoFreeBetServicer",
]
