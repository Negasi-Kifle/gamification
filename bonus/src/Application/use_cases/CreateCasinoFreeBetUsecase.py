"""Create CasinoFreeBet use case."""

from django.utils import timezone
from decimal import Decimal
import uuid

from ...Domain.entities import CasinoFreeBet
from ...Domain.repositories import CasinoFreeBetRepository
from ...Domain.value_objects import FreebetCurrency

from ..dto.request.CasinoCreateFreeBetRequestDto import CasinoCreateFreeBetRequestDto
from ..dto.response.CasinoFreeBetResponseDto import CasinoFreeBetResponseDto


class CreateCasinoFreeBetUseCase:
    """Use case for creating a new casino freebet."""
    
    def __init__(self, freebet_repository: CasinoFreeBetRepository):
        self.freebet_repository = freebet_repository
    
    def execute(self, request: CasinoCreateFreeBetRequestDto) -> CasinoFreeBetResponseDto:
        """Create a new freebet with validation."""
        
        # Validate currency
        if not FreebetCurrency.validate(request.currency.value):
            raise ValueError(f"Invalid currency: {request.currency}")
        
        # Create domain entity (business rules enforced in __post_init__)
        freebet = CasinoFreeBet(
            public_id=str(uuid.uuid4()),
            tenant_id=request.tenant_id,
            name=request.name,
            description=request.description,
            currency=request.currency,
            game_id=request.game_id,
            unit_value=Decimal(str(request.unit_value)),
            quantity=request.quantity,
            expiry_minutes=request.expiry_minutes,
            status=request.initial_status,
            created_at=timezone.now(),
            updated_at=timezone.now()
        )
        
        # Persist using repository
        saved_freebet = self.freebet_repository.save(freebet)
        
        # Convert to response DTO
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
            is_expired=freebet.is_expired(timezone.now())
        )