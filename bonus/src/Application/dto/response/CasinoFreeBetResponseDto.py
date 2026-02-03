from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class CasinoFreeBetResponseDto:
    """Output DTO for freebet operations."""

    public_id: str
    name: str
    currency: str
    game_id: str
    unit_value: Decimal
    quantity: int
    expiry_minutes: int
    status: str
    total_value: Decimal
    expires_at: datetime | None = None
    is_expired: bool = False
