"""Get expiring CasinoFreeBets use case."""

from django.utils import timezone

from ...Domain.entities import CasinoFreeBet
from ...Domain.repositories import CasinoFreeBetRepository
from ..dto.response.CasinoFreeBetResponseDto import CasinoFreeBetResponseDto


class GetExpiringCasinoFreeBetsUseCase:
    """Use case for finding freebets expiring soon (for notifications)."""

    def __init__(self, freebet_repository: CasinoFreeBetRepository):
        self.freebet_repository = freebet_repository

    def execute(self, hours_threshold: int = 24) -> list[CasinoFreeBetResponseDto]:
        """Find all freebets expiring within the specified hours."""
        minutes_threshold = hours_threshold * 60

        expiring_freebets = self.freebet_repository.find_expiring_soon(
            minutes_threshold
        )

        return [self._to_response(fb) for fb in expiring_freebets]

    def _to_response(self, freebet: CasinoFreeBet) -> CasinoFreeBetResponseDto:
        """Convert domain entity to response DTO."""
        expires_at = None
        if freebet.created_at:
            expires_at = freebet.calculate_expiry_time(freebet.created_at)

        return CasinoFreeBetResponseDto(
            public_id=freebet.public_id,
            name=freebet.name,
            currency=freebet.currency.value,
            game_id=freebet.game_id,
            unit_value=freebet.unit_value,
            quantity=freebet.quantity,
            expiry_minutes=freebet.expiry_minutes,
            status=freebet.get_effective_status(timezone.now()).value,
            total_value=freebet.get_total_value(),
            expires_at=expires_at,
            is_expired=freebet.is_expired(timezone.now()),
        )
