from collections.abc import Iterable as _Iterable
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper

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
    __slots__ = (
        "currency",
        "description",
        "expiry_minutes",
        "game_id",
        "initial_status",
        "name",
        "quantity",
        "tenant_id",
        "unit_value",
    )
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
    def __init__(
        self,
        tenant_id: str | None = ...,
        name: str | None = ...,
        description: str | None = ...,
        currency: FreebetCurrency | str | None = ...,
        game_id: str | None = ...,
        unit_value: str | None = ...,
        quantity: int | None = ...,
        expiry_minutes: int | None = ...,
        initial_status: CasinoFreeBetStatus | str | None = ...,
    ) -> None: ...

class UpdateStatusRequest(_message.Message):
    __slots__ = ("new_status", "public_id")
    PUBLIC_ID_FIELD_NUMBER: _ClassVar[int]
    NEW_STATUS_FIELD_NUMBER: _ClassVar[int]
    public_id: str
    new_status: CasinoFreeBetStatus
    def __init__(
        self,
        public_id: str | None = ...,
        new_status: CasinoFreeBetStatus | str | None = ...,
    ) -> None: ...

class GetExpiringRequest(_message.Message):
    __slots__ = ("hours_threshold",)
    HOURS_THRESHOLD_FIELD_NUMBER: _ClassVar[int]
    hours_threshold: int
    def __init__(self, hours_threshold: int | None = ...) -> None: ...

class FreebetResponse(_message.Message):
    __slots__ = (
        "currency",
        "expires_at",
        "expiry_minutes",
        "game_id",
        "is_expired",
        "name",
        "public_id",
        "quantity",
        "status",
        "total_value",
        "unit_value",
    )
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
    def __init__(
        self,
        public_id: str | None = ...,
        name: str | None = ...,
        currency: str | None = ...,
        game_id: str | None = ...,
        unit_value: str | None = ...,
        quantity: int | None = ...,
        expiry_minutes: int | None = ...,
        status: str | None = ...,
        total_value: str | None = ...,
        expires_at: str | None = ...,
        is_expired: bool = ...,
    ) -> None: ...

class FreebetListResponse(_message.Message):
    __slots__ = ("count", "freebets")
    FREEBETS_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    freebets: _containers.RepeatedCompositeFieldContainer[FreebetResponse]
    count: int
    def __init__(
        self,
        freebets: _Iterable[FreebetResponse | _Mapping] | None = ...,
        count: int | None = ...,
    ) -> None: ...
