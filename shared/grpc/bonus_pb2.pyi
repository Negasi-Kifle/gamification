from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CasinoFreeBetStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    FREEBET_STATUS_UNSPECIFIED: _ClassVar[CasinoFreeBetStatus]
    FREEBET_STATUS_ACTIVE: _ClassVar[CasinoFreeBetStatus]
    FREEBET_STATUS_INACTIVE: _ClassVar[CasinoFreeBetStatus]
    FREEBET_STATUS_EXPIRED: _ClassVar[CasinoFreeBetStatus]
    FREEBET_STATUS_USED: _ClassVar[CasinoFreeBetStatus]

class FreebetCurrency(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    FREEBET_CURRENCY_UNSPECIFIED: _ClassVar[FreebetCurrency]
    FREEBET_CURRENCY_ETB: _ClassVar[FreebetCurrency]
    FREEBET_CURRENCY_SZL: _ClassVar[FreebetCurrency]
    FREEBET_CURRENCY_TSH: _ClassVar[FreebetCurrency]
    FREEBET_CURRENCY_ZMW: _ClassVar[FreebetCurrency]
    FREEBET_CURRENCY_USD: _ClassVar[FreebetCurrency]
FREEBET_STATUS_UNSPECIFIED: CasinoFreeBetStatus
FREEBET_STATUS_ACTIVE: CasinoFreeBetStatus
FREEBET_STATUS_INACTIVE: CasinoFreeBetStatus
FREEBET_STATUS_EXPIRED: CasinoFreeBetStatus
FREEBET_STATUS_USED: CasinoFreeBetStatus
FREEBET_CURRENCY_UNSPECIFIED: FreebetCurrency
FREEBET_CURRENCY_ETB: FreebetCurrency
FREEBET_CURRENCY_SZL: FreebetCurrency
FREEBET_CURRENCY_TSH: FreebetCurrency
FREEBET_CURRENCY_ZMW: FreebetCurrency
FREEBET_CURRENCY_USD: FreebetCurrency

class CreateFreebetRequest(_message.Message):
    __slots__ = ("tenant_id", "name", "description", "currency", "game_id", "unit_value", "quantity", "expiry_minutes", "initial_status")
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    CURRENCY_FIELD_NUMBER: _ClassVar[int]
    GAME_ID_FIELD_NUMBER: _ClassVar[int]
    UNIT_VALUE_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    EXPIRY_MINUTES_FIELD_NUMBER: _ClassVar[int]
    INITIAL_STATUS_FIELD_NUMBER: _ClassVar[int]
    tenant_id: str
    name: str
    description: str
    currency: FreebetCurrency
    game_id: str
    unit_value: str
    quantity: int
    expiry_minutes: int
    initial_status: CasinoFreeBetStatus
    def __init__(self, tenant_id: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., currency: _Optional[_Union[FreebetCurrency, str]] = ..., game_id: _Optional[str] = ..., unit_value: _Optional[str] = ..., quantity: _Optional[int] = ..., expiry_minutes: _Optional[int] = ..., initial_status: _Optional[_Union[CasinoFreeBetStatus, str]] = ...) -> None: ...

class UpdateStatusRequest(_message.Message):
    __slots__ = ("public_id", "new_status")
    PUBLIC_ID_FIELD_NUMBER: _ClassVar[int]
    NEW_STATUS_FIELD_NUMBER: _ClassVar[int]
    public_id: str
    new_status: CasinoFreeBetStatus
    def __init__(self, public_id: _Optional[str] = ..., new_status: _Optional[_Union[CasinoFreeBetStatus, str]] = ...) -> None: ...

class GetExpiringRequest(_message.Message):
    __slots__ = ("hours_threshold",)
    HOURS_THRESHOLD_FIELD_NUMBER: _ClassVar[int]
    hours_threshold: int
    def __init__(self, hours_threshold: _Optional[int] = ...) -> None: ...

class FreebetResponse(_message.Message):
    __slots__ = ("public_id", "name", "currency", "game_id", "unit_value", "quantity", "expiry_minutes", "status", "total_value", "expires_at", "is_expired")
    PUBLIC_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    CURRENCY_FIELD_NUMBER: _ClassVar[int]
    GAME_ID_FIELD_NUMBER: _ClassVar[int]
    UNIT_VALUE_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    EXPIRY_MINUTES_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_VALUE_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_AT_FIELD_NUMBER: _ClassVar[int]
    IS_EXPIRED_FIELD_NUMBER: _ClassVar[int]
    public_id: str
    name: str
    currency: str
    game_id: str
    unit_value: str
    quantity: int
    expiry_minutes: int
    status: str
    total_value: str
    expires_at: str
    is_expired: bool
    def __init__(self, public_id: _Optional[str] = ..., name: _Optional[str] = ..., currency: _Optional[str] = ..., game_id: _Optional[str] = ..., unit_value: _Optional[str] = ..., quantity: _Optional[int] = ..., expiry_minutes: _Optional[int] = ..., status: _Optional[str] = ..., total_value: _Optional[str] = ..., expires_at: _Optional[str] = ..., is_expired: bool = ...) -> None: ...

class FreebetListResponse(_message.Message):
    __slots__ = ("freebets", "count")
    FREEBETS_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    freebets: _containers.RepeatedCompositeFieldContainer[FreebetResponse]
    count: int
    def __init__(self, freebets: _Optional[_Iterable[_Union[FreebetResponse, _Mapping]]] = ..., count: _Optional[int] = ...) -> None: ...
