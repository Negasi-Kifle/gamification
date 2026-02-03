"""gRPC Servicer for Casino Freebet operations."""

import logging
from decimal import Decimal

from shared.grpc import bonus_pb2, bonus_pb2_grpc

from ...Application import (
    CasinoCreateFreeBetRequestDto,
    CasinoFreeBetResponseDto,
    CreateCasinoFreeBetUseCase,
    GetExpiringCasinoFreeBetsUseCase,
    UpdateCasinoFreeBetStatusUseCase,
)
from ...Domain.exceptions import (
    FreebetExpiredError,
    InvalidFreebetStateError,
)
from ...Domain.repositories import CasinoFreeBetRepository
from ...Domain.value_objects import CasinoFreeBetStatus, FreebetCurrency

# Currency mapping from proto enum values to domain enum
CURRENCY_MAP = {
    1: FreebetCurrency.ETB,
    2: FreebetCurrency.SZL,
    3: FreebetCurrency.TSH,
    4: FreebetCurrency.ZMW,
    5: FreebetCurrency.USD,
}

# Status mapping from proto enum values to domain enum
STATUS_MAP = {
    1: CasinoFreeBetStatus.ACTIVE,
    2: CasinoFreeBetStatus.INACTIVE,
}

logger = logging.getLogger(__name__)


class CasinoFreeBetServicer(bonus_pb2_grpc.CasinoFreeBetServiceServicer):
    """
    gRPC servicer for CasinoFreeBet operations.

    This class implements the gRPC service interface defined in bonus.proto.
    It delegates business logic to use cases, following clean architecture.

    Usage:
        repository = CasinoFreeBetRepository()
        servicer = CasinoFreeBetServicer(repository)
        # Register with gRPC server
    """

    def __init__(self, repository: CasinoFreeBetRepository):
        """
        Initialize servicer with repository dependency.

        Args:
            repository: Implementation of CasinoFreeBetRepository interface
        """
        self.repository = repository

    def CreateFreebet(self, request, context):
        """
        Create a new casino freebet.

        Args:
            request: CreateFreebetRequest proto message
            context: gRPC context

        Returns:
            FreebetResponse proto message
        """
        try:
            logger.debug(f"gRPC CreateFreebet called for tenant: {request.tenant_id}")

            # Map proto currency to domain enum
            currency = CURRENCY_MAP.get(request.currency)
            if not currency:
                logger.warning(f"Invalid currency value: {request.currency}")
                context.set_code(400)  # INVALID_ARGUMENT
                context.set_details("Invalid currency value")
                return self._empty_response()

            # Map proto status to domain enum
            initial_status = STATUS_MAP.get(
                request.initial_status, CasinoFreeBetStatus.INACTIVE
            )

            # Build request DTO
            request_dto = CasinoCreateFreeBetRequestDto(
                tenant_id=request.tenant_id,
                name=request.name,
                game_id=request.game_id,
                unit_value=Decimal(request.unit_value),
                currency=currency,
                description=request.description or None,
                quantity=request.quantity or 1,
                expiry_minutes=request.expiry_minutes or 1440,
                initial_status=initial_status,
            )

            # Execute use case
            use_case = CreateCasinoFreeBetUseCase(self.repository)
            result = use_case.execute(request_dto)

            logger.info(f"gRPC CreateFreebet success: {result.public_id}")
            return self._to_proto_response(result)

        except ValueError as e:
            logger.warning(f"gRPC CreateFreebet validation error: {e}")
            context.set_code(400)  # INVALID_ARGUMENT
            context.set_details(str(e))
            return self._empty_response()
        except Exception as e:
            logger.exception(f"gRPC CreateFreebet internal error: {e}")
            context.set_code(500)  # INTERNAL
            context.set_details(f"Internal error: {e!s}")
            return self._empty_response()

    def UpdateStatus(self, request, context):
        """
        Update freebet status (activate/deactivate).

        Args:
            request: UpdateStatusRequest proto message
            context: gRPC context

        Returns:
            FreebetResponse proto message
        """
        try:
            logger.debug(f"gRPC UpdateStatus called for freebet: {request.public_id}")

            # Map proto status to domain enum
            new_status = STATUS_MAP.get(request.new_status)
            if not new_status:
                logger.warning(f"Invalid status value: {request.new_status}")
                context.set_code(400)  # INVALID_ARGUMENT
                context.set_details("Invalid status value. Use ACTIVE or INACTIVE.")
                return self._empty_response()

            # Execute use case
            use_case = UpdateCasinoFreeBetStatusUseCase(self.repository)
            result = use_case.execute(request.public_id, new_status)

            logger.info(
                f"gRPC UpdateStatus success: {request.public_id} -> {new_status.value}"
            )
            return self._to_proto_response(result)

        except FreebetExpiredError as e:
            logger.warning(f"gRPC UpdateStatus expired freebet: {request.public_id}")
            context.set_code(400)  # FAILED_PRECONDITION
            context.set_details(str(e))
            return self._empty_response()
        except InvalidFreebetStateError as e:
            logger.warning(
                f"gRPC UpdateStatus invalid state: {request.public_id} - {e}"
            )
            context.set_code(400)  # FAILED_PRECONDITION
            context.set_details(str(e))
            return self._empty_response()
        except ValueError as e:
            logger.warning(f"gRPC UpdateStatus not found: {request.public_id}")
            context.set_code(404)  # NOT_FOUND
            context.set_details(str(e))
            return self._empty_response()
        except Exception as e:
            logger.exception(f"gRPC UpdateStatus internal error: {e}")
            context.set_code(500)  # INTERNAL
            context.set_details(f"Internal error: {e!s}")
            return self._empty_response()

    def GetExpiring(self, request, context):
        """
        Get freebets expiring soon (for notifications).

        Args:
            request: GetExpiringRequest proto message
            context: gRPC context

        Returns:
            FreebetListResponse proto message
        """
        try:
            hours_threshold = request.hours_threshold or 24
            logger.debug(
                f"gRPC GetExpiring called with threshold: {hours_threshold} hours"
            )

            # Execute use case
            use_case = GetExpiringCasinoFreeBetsUseCase(self.repository)
            results = use_case.execute(hours_threshold=hours_threshold)

            logger.info(f"gRPC GetExpiring returned {len(results)} freebets")
            return self._to_proto_list_response(results)

        except Exception as e:
            logger.exception(f"gRPC GetExpiring internal error: {e}")
            context.set_code(500)  # INTERNAL
            context.set_details(f"Internal error: {e!s}")
            return self._empty_list_response()

    def _to_proto_response(
        self, dto: CasinoFreeBetResponseDto
    ) -> bonus_pb2.FreebetResponse:
        """Convert response DTO to proto Message."""
        data = {
            "public_id": str(dto.public_id),
            "name": dto.name,
            "currency": str(
                dto.currency
            ),  # Ensure it's a string if proto expects string
            "game_id": dto.game_id,
            "unit_value": str(dto.unit_value),
            "quantity": dto.quantity,
            "expiry_minutes": dto.expiry_minutes,
            "status": str(dto.status),
            "total_value": str(dto.total_value),
            "expires_at": dto.expires_at.isoformat() if dto.expires_at else "",
            "is_expired": dto.is_expired,
        }
        return bonus_pb2.FreebetResponse(**data)

    def _to_proto_list_response(self, dtos: list) -> bonus_pb2.FreebetListResponse:
        """Convert list of response DTOs to proto Message."""
        return bonus_pb2.FreebetListResponse(
            freebets=[self._to_proto_response(dto) for dto in dtos],
            count=len(dtos),
        )

    def _empty_response(self) -> bonus_pb2.FreebetResponse:
        """Return empty proto message."""
        return bonus_pb2.FreebetResponse()

    def _empty_list_response(self) -> bonus_pb2.FreebetListResponse:
        """Return empty proto list message."""
        return bonus_pb2.FreebetListResponse(freebets=[], count=0)
