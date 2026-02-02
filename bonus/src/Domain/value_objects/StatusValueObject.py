from enum import Enum

class CasinoFreeBetStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    EXPIRED = "EXPIRED"    # Calculated, not stored
    USED = "USED"          # Calculated, not stored
    
    def can_activate(self) -> bool:
        """When can a freebet be activated"""
        return self == CasinoFreeBetStatus.INACTIVE
    
    def can_deactivate(self) -> bool:
        """When can a freebet be deactivated"""
        return self == CasinoFreeBetStatus.ACTIVE