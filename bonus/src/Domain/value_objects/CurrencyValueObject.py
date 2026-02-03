from enum import Enum


class FreebetCurrency(str, Enum):
    ETB = "ETB"
    SZL = "SZL"
    TSH = "TSh"  # Tanzanian Shilling - member name uppercase, value as currency code
    ZMW = "ZMW"
    USD = "USD"

    @classmethod
    def validate(cls, value: str) -> bool:
        return value in cls._value2member_map_
