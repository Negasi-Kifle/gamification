"""Update CasinoFreeBet status use case."""

from django.utils import timezone

from ...Domain.entities import CasinoFreeBet
from ...Domain.exceptions import FreebetExpiredError, InvalidFreebetStateError
from ...Domain.repositories import CasinoFreeBetRepository
from ...Domain.value_objects import CasinoFreeBetStatus
from ..dto.response.CasinoFreeBetResponseDto import CasinoFreeBetResponseDto


class UpdateCasinoFreeBetStatusUseCase:
    """Use case for updating freebet status."""

    def __init__(self, freebet_repository: CasinoFreeBetRepository):
        self.freebet_repository = freebet_repository

    def execute(
        self, freebet_public_id: str, new_status: CasinoFreeBetStatus
    ) -> CasinoFreeBetResponseDto:
        """Update the status of a freebet."""

        freebet = self.freebet_repository.find_by_public_id(freebet_public_id)
        if not freebet:
            raise ValueError(f"Freebet not found: {freebet_public_id}")

        if freebet.is_expired(timezone.now()):
            raise FreebetExpiredError("Cannot update status of an expired freebet")

        if freebet.status == new_status:
            raise InvalidFreebetStateError(f"Freebet is already {new_status.value}")

        # Use domain methods for state transitions
        if new_status == CasinoFreeBetStatus.ACTIVE:
            freebet.activate()
        elif new_status == CasinoFreeBetStatus.INACTIVE:
            freebet.deactivate()
        else:
            raise InvalidFreebetStateError(
                f"Cannot manually set status to {new_status.value}"
            )

        freebet.updated_at = timezone.now()

        saved_freebet = self.freebet_repository.save(freebet)

        return self._to_response(saved_freebet)

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
            status=freebet.status.value,
            total_value=freebet.get_total_value(),
            expires_at=expires_at,
            is_expired=freebet.is_expired(timezone.now()),
        )
