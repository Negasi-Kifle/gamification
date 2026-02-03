from abc import ABC, abstractmethod
from datetime import datetime

from ..entities.CasinoFreeBet import CasinoFreeBet


class CasinoFreeBetRepository(ABC):
    """Repository interface for CasinoFreeBet"""

    @abstractmethod
    def save(self, freebet: CasinoFreeBet) -> CasinoFreeBet:
        """Save a freebet (create or update)"""
        pass

    @abstractmethod
    def find_by_id(self, freebet_id: int) -> CasinoFreeBet | None:
        """Find freebet by internal ID"""
        pass

    @abstractmethod
    def find_by_public_id(self, public_id: str) -> CasinoFreeBet | None:
        """Find freebet by public UUID"""
        pass

    @abstractmethod
    def find_active_by_tenant(
        self, tenant_id: str, current_time: datetime
    ) -> list[CasinoFreeBet]:
        """Find active freebets for tenant"""
        pass

    @abstractmethod
    def find_expiring_soon(self, minutes_threshold: int) -> list[CasinoFreeBet]:
        """Find freebets expiring soon"""
        pass

    @abstractmethod
    def delete(self, freebet_id: int) -> bool:
        """Delete a freebet"""
        pass
