"""Request DTO for creating CasinoFreeBet."""

from dataclasses import dataclass
from decimal import Decimal

from ....Domain.value_objects import CasinoFreeBetStatus, FreebetCurrency


@dataclass
class CasinoCreateFreeBetRequestDto:
    """Input for creating a freebet."""

    tenant_id: str
    name: str
    game_id: str
    unit_value: Decimal
    currency: FreebetCurrency = FreebetCurrency.ETB
    description: str | None = None
    quantity: int = 1
    expiry_minutes: int = 1440  # 24 hours default
    initial_status: CasinoFreeBetStatus = CasinoFreeBetStatus.INACTIVE
