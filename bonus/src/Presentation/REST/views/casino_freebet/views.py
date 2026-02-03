"""HTTP views for the Bonus module."""

import json
import logging
from decimal import Decimal

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from bonus.src.Application import (
    CasinoCreateFreeBetRequestDto,
    CreateCasinoFreeBetUseCase,
    GetExpiringCasinoFreeBetsUseCase,
    UpdateCasinoFreeBetStatusUseCase,
)
from bonus.src.Domain.exceptions import (
    FreebetExpiredError,
    InvalidFreebetStateError,
)
from bonus.src.Domain.value_objects import CasinoFreeBetStatus, FreebetCurrency
from bonus.src.Infrastructure.repository import DjangoCasinoFreeBetRepository

logger = logging.getLogger(__name__)


def get_repository() -> DjangoCasinoFreeBetRepository:
    """Dependency injection helper - returns repository instance."""
    return DjangoCasinoFreeBetRepository()


@method_decorator(csrf_exempt, name="dispatch")
class CasinoFreeBetListCreateView(View):
    """View for listing and creating casino freebets."""

    def get(self, request):
        """List expiring freebets (for notifications)."""
        try:
            hours = int(request.GET.get("hours_threshold", 24))
            logger.debug(f"Fetching expiring freebets with threshold: {hours} hours")

            use_case = GetExpiringCasinoFreeBetsUseCase(get_repository())
            freebets = use_case.execute(hours_threshold=hours)

            logger.info(f"Found {len(freebets)} expiring freebets")
            return JsonResponse(
                {
                    "success": True,
                    "data": [self._serialize_response(fb) for fb in freebets],
                    "count": len(freebets),
                }
            )
        except Exception as e:
            logger.exception(f"Error fetching expiring freebets: {e}")
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    def post(self, request):
        """Create a new casino freebet."""
        try:
            data = json.loads(request.body)
            logger.debug(f"Creating freebet for tenant: {data.get('tenant_id')}")

            # Validate and create request DTO
            request_dto = CasinoCreateFreeBetRequestDto(
                tenant_id=data["tenant_id"],
                name=data["name"],
                game_id=data["game_id"],
                unit_value=Decimal(str(data["unit_value"])),
                currency=FreebetCurrency(data.get("currency", "ETB")),
                description=data.get("description"),
                quantity=data.get("quantity", 1),
                expiry_minutes=data.get("expiry_minutes", 1440),
                initial_status=CasinoFreeBetStatus(
                    data.get("initial_status", "INACTIVE")
                ),
            )

            use_case = CreateCasinoFreeBetUseCase(get_repository())
            result = use_case.execute(request_dto)

            logger.info(
                f"Created freebet: {result.public_id} for tenant: {data['tenant_id']}"
            )
            return JsonResponse(
                {"success": True, "data": self._serialize_response(result)}, status=201
            )

        except KeyError as e:
            logger.warning(f"Missing required field in freebet creation: {e}")
            return JsonResponse(
                {"success": False, "error": f"Missing required field: {e}"}, status=400
            )
        except ValueError as e:
            logger.warning(f"Validation error in freebet creation: {e}")
            return JsonResponse({"success": False, "error": str(e)}, status=400)
        except Exception as e:
            logger.exception(f"Error creating freebet: {e}")
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    def _serialize_response(self, dto):
        """Serialize response DTO to dict."""
        return {
            "public_id": dto.public_id,
            "name": dto.name,
            "currency": dto.currency,
            "game_id": dto.game_id,
            "unit_value": str(dto.unit_value),
            "quantity": dto.quantity,
            "expiry_minutes": dto.expiry_minutes,
            "status": dto.status,
            "total_value": str(dto.total_value),
            "expires_at": dto.expires_at.isoformat() if dto.expires_at else None,
            "is_expired": dto.is_expired,
        }


@method_decorator(csrf_exempt, name="dispatch")
class CasinoFreeBetDetailView(View):
    """View for individual casino freebet operations."""

    def patch(self, request, public_id):
        """Update casino freebet status."""
        try:
            data = json.loads(request.body)
            new_status = CasinoFreeBetStatus(data["status"])
            logger.debug(f"Updating freebet {public_id} status to: {new_status.value}")

            use_case = UpdateCasinoFreeBetStatusUseCase(get_repository())
            result = use_case.execute(public_id, new_status)

            logger.info(f"Updated freebet {public_id} status to: {new_status.value}")
            return JsonResponse(
                {"success": True, "data": self._serialize_response(result)}
            )

        except KeyError as e:
            logger.warning(
                f"Missing required field in status update for {public_id}: {e}"
            )
            return JsonResponse(
                {"success": False, "error": f"Missing required field: {e}"}, status=400
            )
        except (FreebetExpiredError, InvalidFreebetStateError) as e:
            logger.warning(f"Invalid state transition for freebet {public_id}: {e}")
            return JsonResponse({"success": False, "error": str(e)}, status=400)
        except ValueError as e:
            logger.warning(f"Freebet not found: {public_id}")
            return JsonResponse({"success": False, "error": str(e)}, status=404)
        except Exception as e:
            logger.exception(f"Error updating freebet {public_id}: {e}")
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    def _serialize_response(self, dto):
        """Serialize response DTO to dict."""
        return {
            "public_id": dto.public_id,
            "name": dto.name,
            "currency": dto.currency,
            "game_id": dto.game_id,
            "unit_value": str(dto.unit_value),
            "quantity": dto.quantity,
            "expiry_minutes": dto.expiry_minutes,
            "status": dto.status,
            "total_value": str(dto.total_value),
            "expires_at": dto.expires_at.isoformat() if dto.expires_at else None,
            "is_expired": dto.is_expired,
        }
