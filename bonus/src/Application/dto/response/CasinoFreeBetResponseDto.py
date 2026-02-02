from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from datetime import datetime


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
    expires_at: Optional[datetime] = None
    is_expired: bool = False
