"""Unit tests for the Domain layer of the Bonus module."""

from datetime import datetime
from decimal import Decimal

import pytest
from django.utils import timezone

from bonus.src.Domain.entities.CasinoFreeBet import CasinoFreeBet
from bonus.src.Domain.value_objects.CurrencyValueObject import FreebetCurrency
from bonus.src.Domain.value_objects.StatusValueObject import CasinoFreeBetStatus


class TestCasinoFreeBetEntity:
    """Tests for CasinoFreeBet domain entity."""

    def _create_valid_freebet(self, **overrides):
        """Helper to create a valid freebet with optional overrides."""
        defaults = {
            "public_id": "test-uuid-123",
            "tenant_id": "tenant-1",
            "name": "Test Freebet",
            "description": "A test freebet",
            "currency": FreebetCurrency.ETB,
            "game_id": "game-123",
            "unit_value": Decimal("10.00"),
            "quantity": 5,
            "expiry_minutes": 1440,
            "status": CasinoFreeBetStatus.INACTIVE,
            "created_at": timezone.now(),
        }
        defaults.update(overrides)
        return CasinoFreeBet(**defaults)

    # --- Validation Tests ---

    def test_create_valid_freebet(self):
        """Should create freebet when all fields are valid."""
        freebet = self._create_valid_freebet()

        assert freebet.name == "Test Freebet"
        assert freebet.unit_value == Decimal("10.00")
        assert freebet.quantity == 5
        assert freebet.status == CasinoFreeBetStatus.INACTIVE

    def test_name_too_short_raises_error(self):
        """Should raise ValueError when name is less than 2 characters."""
        with pytest.raises(ValueError, match="name must be at least 2 characters"):
            self._create_valid_freebet(name="A")

    def test_empty_name_raises_error(self):
        """Should raise ValueError when name is empty."""
        with pytest.raises(ValueError, match="name must be at least 2 characters"):
            self._create_valid_freebet(name="")

    def test_whitespace_only_name_raises_error(self):
        """Should raise ValueError when name is only whitespace."""
        with pytest.raises(ValueError, match="name must be at least 2 characters"):
            self._create_valid_freebet(name="   ")

    def test_zero_unit_value_raises_error(self):
        """Should raise ValueError when unit_value is zero."""
        with pytest.raises(ValueError, match="Unit value must be positive"):
            self._create_valid_freebet(unit_value=Decimal("0"))

    def test_negative_unit_value_raises_error(self):
        """Should raise ValueError when unit_value is negative."""
        with pytest.raises(ValueError, match="Unit value must be positive"):
            self._create_valid_freebet(unit_value=Decimal("-10.00"))

    def test_negative_quantity_raises_error(self):
        """Should raise ValueError when quantity is negative."""
        with pytest.raises(ValueError, match="Quantity cannot be negative"):
            self._create_valid_freebet(quantity=-1)

    def test_zero_quantity_allowed(self):
        """Should allow zero quantity (depleted freebet)."""
        freebet = self._create_valid_freebet(quantity=0)
        assert freebet.quantity == 0

    def test_zero_expiry_minutes_raises_error(self):
        """Should raise ValueError when expiry_minutes is zero."""
        with pytest.raises(ValueError, match="Expiry time must be positive"):
            self._create_valid_freebet(expiry_minutes=0)

    def test_negative_expiry_minutes_raises_error(self):
        """Should raise ValueError when expiry_minutes is negative."""
        with pytest.raises(ValueError, match="Expiry time must be positive"):
            self._create_valid_freebet(expiry_minutes=-60)

    # --- Expiry Logic Tests ---

    def test_calculate_expiry_time(self):
        """Should calculate correct expiry time from creation."""
        creation_time = datetime(2026, 1, 1, 12, 0, 0)
        freebet = self._create_valid_freebet(expiry_minutes=60)

        expiry_time = freebet.calculate_expiry_time(creation_time)

        expected = datetime(2026, 1, 1, 13, 0, 0)
        assert expiry_time == expected

    def test_is_expired_returns_false_before_expiry(self):
        """Should return False when current time is before expiry."""
        creation_time = datetime(2026, 1, 1, 12, 0, 0)
        current_time = datetime(2026, 1, 1, 12, 30, 0)  # 30 min after creation
        freebet = self._create_valid_freebet(
            expiry_minutes=60,
            created_at=creation_time,
        )

        assert freebet.is_expired(current_time) is False

    def test_is_expired_returns_true_after_expiry(self):
        """Should return True when current time is after expiry."""
        creation_time = datetime(2026, 1, 1, 12, 0, 0)
        current_time = datetime(2026, 1, 1, 14, 0, 0)  # 2 hours after creation
        freebet = self._create_valid_freebet(
            expiry_minutes=60,
            created_at=creation_time,
        )

        assert freebet.is_expired(current_time) is True

    def test_is_expired_returns_false_when_no_created_at(self):
        """Should return False when created_at is not set."""
        freebet = self._create_valid_freebet(created_at=None)
        current_time = timezone.now()

        assert freebet.is_expired(current_time) is False

    def test_get_effective_status_returns_expired_when_expired(self):
        """Should return EXPIRED status when freebet is expired."""
        creation_time = datetime(2026, 1, 1, 12, 0, 0)
        current_time = datetime(2026, 1, 1, 14, 0, 0)
        freebet = self._create_valid_freebet(
            expiry_minutes=60,
            created_at=creation_time,
            status=CasinoFreeBetStatus.ACTIVE,
        )

        effective_status = freebet.get_effective_status(current_time)

        assert effective_status == CasinoFreeBetStatus.EXPIRED

    def test_get_effective_status_returns_actual_status_when_not_expired(self):
        """Should return actual status when freebet is not expired."""
        creation_time = datetime(2026, 1, 1, 12, 0, 0)
        current_time = datetime(2026, 1, 1, 12, 30, 0)
        freebet = self._create_valid_freebet(
            expiry_minutes=60,
            created_at=creation_time,
            status=CasinoFreeBetStatus.ACTIVE,
        )

        effective_status = freebet.get_effective_status(current_time)

        assert effective_status == CasinoFreeBetStatus.ACTIVE

    # --- can_be_used Tests ---

    def test_can_be_used_returns_true_when_active_not_expired_has_quantity(self):
        """Should return True when freebet is active, not expired, and has quantity."""
        creation_time = datetime(2026, 1, 1, 12, 0, 0)
        current_time = datetime(2026, 1, 1, 12, 30, 0)
        freebet = self._create_valid_freebet(
            expiry_minutes=60,
            created_at=creation_time,
            status=CasinoFreeBetStatus.ACTIVE,
            quantity=5,
        )

        assert freebet.can_be_used(current_time) is True

    def test_can_be_used_returns_false_when_inactive(self):
        """Should return False when freebet is inactive."""
        freebet = self._create_valid_freebet(
            status=CasinoFreeBetStatus.INACTIVE,
            quantity=5,
        )

        assert freebet.can_be_used(timezone.now()) is False

    def test_can_be_used_returns_false_when_expired(self):
        """Should return False when freebet is expired."""
        creation_time = datetime(2026, 1, 1, 12, 0, 0)
        current_time = datetime(2026, 1, 1, 14, 0, 0)
        freebet = self._create_valid_freebet(
            expiry_minutes=60,
            created_at=creation_time,
            status=CasinoFreeBetStatus.ACTIVE,
            quantity=5,
        )

        assert freebet.can_be_used(current_time) is False

    def test_can_be_used_returns_false_when_zero_quantity(self):
        """Should return False when quantity is zero."""
        freebet = self._create_valid_freebet(
            status=CasinoFreeBetStatus.ACTIVE,
            quantity=0,
        )

        assert freebet.can_be_used(timezone.now()) is False

    # --- Status Transition Tests ---

    def test_activate_from_inactive(self):
        """Should activate freebet when currently inactive."""
        freebet = self._create_valid_freebet(status=CasinoFreeBetStatus.INACTIVE)

        freebet.activate()

        assert freebet.status == CasinoFreeBetStatus.ACTIVE

    def test_activate_from_active_raises_error(self):
        """Should raise error when trying to activate already active freebet."""
        freebet = self._create_valid_freebet(status=CasinoFreeBetStatus.ACTIVE)

        with pytest.raises(ValueError, match="Cannot activate"):
            freebet.activate()

    def test_deactivate_from_active(self):
        """Should deactivate freebet when currently active."""
        freebet = self._create_valid_freebet(status=CasinoFreeBetStatus.ACTIVE)

        freebet.deactivate()

        assert freebet.status == CasinoFreeBetStatus.INACTIVE

    def test_deactivate_from_inactive_raises_error(self):
        """Should raise error when trying to deactivate already inactive freebet."""
        freebet = self._create_valid_freebet(status=CasinoFreeBetStatus.INACTIVE)

        with pytest.raises(ValueError, match="Cannot deactivate"):
            freebet.deactivate()

    # --- Value Calculation Tests ---

    def test_get_total_value(self):
        """Should calculate total value correctly."""
        freebet = self._create_valid_freebet(
            unit_value=Decimal("10.50"),
            quantity=3,
        )

        total = freebet.get_total_value()

        assert total == Decimal("31.50")

    def test_get_total_value_with_zero_quantity(self):
        """Should return zero when quantity is zero."""
        freebet = self._create_valid_freebet(
            unit_value=Decimal("10.00"),
            quantity=0,
        )

        total = freebet.get_total_value()

        assert total == Decimal("0.00")


class TestFreebetStatus:
    """Tests for CasinoFreeBetStatus value object."""

    def test_can_activate_returns_true_for_inactive(self):
        """INACTIVE status can be activated."""
        assert CasinoFreeBetStatus.INACTIVE.can_activate() is True

    def test_can_activate_returns_false_for_active(self):
        """ACTIVE status cannot be activated."""
        assert CasinoFreeBetStatus.ACTIVE.can_activate() is False

    def test_can_deactivate_returns_true_for_active(self):
        """ACTIVE status can be deactivated."""
        assert CasinoFreeBetStatus.ACTIVE.can_deactivate() is True

    def test_can_deactivate_returns_false_for_inactive(self):
        """INACTIVE status cannot be deactivated."""
        assert CasinoFreeBetStatus.INACTIVE.can_deactivate() is False


class TestFreebetCurrency:
    """Tests for FreebetCurrency value object."""

    def test_validate_returns_true_for_valid_currency(self):
        """Should return True for valid currency codes."""
        assert FreebetCurrency.validate("ETB") is True
        assert FreebetCurrency.validate("USD") is True
        assert FreebetCurrency.validate("SZL") is True

    def test_validate_returns_false_for_invalid_currency(self):
        """Should return False for invalid currency codes."""
        assert FreebetCurrency.validate("INVALID") is False
        assert FreebetCurrency.validate("") is False
        assert FreebetCurrency.validate("EUR") is False
