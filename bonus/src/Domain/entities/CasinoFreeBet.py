from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

from ..value_objects.CurrencyValueObject import FreebetCurrency
from ..value_objects.StatusValueObject import CasinoFreeBetStatus


@dataclass
class CasinoFreeBet:
    id: int | None = None  # database primary key (internal)
    public_id: UUID = None  # public facing UUID
    tenant_id: str = None
    name: str = None
    description: str | None = None
    currency: FreebetCurrency = None
    game_id: str = None
    unit_value: Decimal = None  # value per freebet unit
    quantity: int = 0  # how many freebets available
    expiry_minutes: int = None  # minutes until expiry
    created_at: datetime | None = None
    updated_at: datetime | None = None
    status: CasinoFreeBetStatus = CasinoFreeBetStatus.INACTIVE

    def __post_init__(self):
        """Enforce business rules on creation"""
        self._validate()

    def _validate(self):
        """Business validation rules"""
        if not self.name or len(self.name.strip()) < 2:
            raise ValueError("Freebet name must be at least 2 characters")

        if self.unit_value <= Decimal("0"):
            raise ValueError("Unit value must be positive")

        if self.quantity < 0:
            raise ValueError("Quantity cannot be negative")

        if self.expiry_minutes <= 0:
            raise ValueError("Expiry time must be positive minutes")

    def calculate_expiry_time(self, creation_time: datetime) -> datetime:
        """Calculate exact expiry time"""
        return creation_time + timedelta(minutes=self.expiry_minutes)

    def is_expired(self, current_time: datetime) -> bool:
        """Determine if freebet is expired"""
        if not self.created_at:
            return False

        expiry_time = self.calculate_expiry_time(self.created_at)
        return current_time > expiry_time

    def get_effective_status(self, current_time: datetime) -> CasinoFreeBetStatus:
        """Determine effective status (including calculated states)"""
        if self.is_expired(current_time):
            return CasinoFreeBetStatus.EXPIRED
        return self.status

    def can_be_used(self, current_time: datetime) -> bool:
        """Check if freebet can be used"""
        return (
            self.status == CasinoFreeBetStatus.ACTIVE
            and not self.is_expired(current_time)
            and self.quantity > 0
        )

    def activate(self):
        """Activate the freebet"""
        if not self.status.can_activate():
            raise ValueError(f"Cannot activate freebet in {self.status} status")
        self.status = CasinoFreeBetStatus.ACTIVE

    def deactivate(self):
        """Deactivate the freebet"""
        if not self.status.can_deactivate():
            raise ValueError(f"Cannot deactivate freebet in {self.status} status")
        self.status = CasinoFreeBetStatus.INACTIVE

    def get_total_value(self) -> Decimal:
        """Total potential value a user could get from this freebet"""
        return self.unit_value * self.quantity
