"""Unit tests for the Application layer of the Bonus module."""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from bonus.src.Application.dto.request.CasinoCreateFreeBetRequestDto import (
    CasinoCreateFreeBetRequestDto,
)
from bonus.src.Application.dto.response.CasinoFreeBetResponseDto import (
    CasinoFreeBetResponseDto,
)
from bonus.src.Application.use_cases.CreateCasinoFreeBetUsecase import (
    CreateCasinoFreeBetUseCase,
)
from bonus.src.Application.use_cases.GetExpiringCasinoFreebetsUseCase import (
    GetExpiringCasinoFreeBetsUseCase,
)
from bonus.src.Application.use_cases.UpdateCasinoFreeBetStatusUsecase import (
    UpdateCasinoFreeBetStatusUseCase,
)
from bonus.src.Domain.entities.CasinoFreeBet import CasinoFreeBet
from bonus.src.Domain.exceptions.CasinoFreeBetExceptions import (
    FreebetExpiredError,
    InvalidFreebetStateError,
)
from bonus.src.Domain.repositories.CasinoFreeBetRepositoryInterface import (
    CasinoFreeBetRepository,
)
from bonus.src.Domain.value_objects.CurrencyValueObject import FreebetCurrency
from bonus.src.Domain.value_objects.StatusValueObject import CasinoFreeBetStatus


class MockCasinoFreeBetRepository(CasinoFreeBetRepository):
    """Mock repository for testing use cases."""

    def __init__(self):
        self.freebets = {}
        self._id_counter = 1

    def save(self, freebet: CasinoFreeBet) -> CasinoFreeBet:
        if freebet.id is None:
            freebet.id = self._id_counter
            self._id_counter += 1
        self.freebets[freebet.public_id] = freebet
        return freebet

    def find_by_id(self, freebet_id: int) -> CasinoFreeBet | None:
        for fb in self.freebets.values():
            if fb.id == freebet_id:
                return fb
        return None

    def find_by_public_id(self, public_id: str) -> CasinoFreeBet | None:
        return self.freebets.get(public_id)

    def find_active_by_tenant(
        self, tenant_id: str, current_time: datetime
    ) -> list[CasinoFreeBet]:
        return [
            fb
            for fb in self.freebets.values()
            if fb.tenant_id == tenant_id and fb.status == CasinoFreeBetStatus.ACTIVE
        ]

    def find_expiring_soon(self, minutes_threshold: int) -> list[CasinoFreeBet]:
        now = timezone.now()
        expiring = []
        for fb in self.freebets.values():
            if fb.status == CasinoFreeBetStatus.ACTIVE and fb.created_at:
                expiry_time = fb.calculate_expiry_time(fb.created_at)
                time_until_expiry = (expiry_time - now).total_seconds() / 60
                if 0 < time_until_expiry <= minutes_threshold:
                    expiring.append(fb)
        return expiring

    def delete(self, freebet_id: int) -> bool:
        for public_id, fb in list(self.freebets.items()):
            if fb.id == freebet_id:
                del self.freebets[public_id]
                return True
        return False


class TestCreateCasinoFreeBetUseCase:
    """Tests for CreateCasinoFreeBetUseCase."""

    def setup_method(self):
        """Set up test fixtures."""
        self.repository = MockCasinoFreeBetRepository()
        self.use_case = CreateCasinoFreeBetUseCase(self.repository)

    def test_create_freebet_successfully(self):
        """Should create freebet and return response DTO."""
        request = CasinoCreateFreeBetRequestDto(
            tenant_id="tenant-1",
            name="Test Freebet",
            game_id="game-123",
            unit_value=Decimal("10.00"),
            currency=FreebetCurrency.ETB,
            description="A test freebet",
            quantity=5,
            expiry_minutes=1440,
            initial_status=CasinoFreeBetStatus.INACTIVE,
        )

        result = self.use_case.execute(request)

        assert isinstance(result, CasinoFreeBetResponseDto)
        assert result.name == "Test Freebet"
        assert result.currency == "ETB"
        assert result.game_id == "game-123"
        assert result.unit_value == Decimal("10.00")
        assert result.quantity == 5
        assert result.status == "INACTIVE"
        assert result.total_value == Decimal("50.00")

    def test_create_freebet_persists_to_repository(self):
        """Should save freebet to repository."""
        request = CasinoCreateFreeBetRequestDto(
            tenant_id="tenant-1",
            name="Test Freebet",
            game_id="game-123",
            unit_value=Decimal("10.00"),
        )

        result = self.use_case.execute(request)

        # Verify freebet is in repository
        saved = self.repository.find_by_public_id(result.public_id)
        assert saved is not None
        assert saved.name == "Test Freebet"

    def test_create_freebet_generates_public_id(self):
        """Should generate a public UUID for the freebet."""
        request = CasinoCreateFreeBetRequestDto(
            tenant_id="tenant-1",
            name="Test Freebet",
            game_id="game-123",
            unit_value=Decimal("10.00"),
        )

        result = self.use_case.execute(request)

        assert result.public_id is not None
        assert len(result.public_id) > 0

    def test_create_freebet_with_invalid_name_raises_error(self):
        """Should raise ValueError when name validation fails."""
        request = CasinoCreateFreeBetRequestDto(
            tenant_id="tenant-1",
            name="A",  # Too short
            game_id="game-123",
            unit_value=Decimal("10.00"),
        )

        with pytest.raises(ValueError, match="name must be at least 2 characters"):
            self.use_case.execute(request)

    def test_create_freebet_calculates_expires_at(self):
        """Should calculate expires_at from expiry_minutes."""
        request = CasinoCreateFreeBetRequestDto(
            tenant_id="tenant-1",
            name="Test Freebet",
            game_id="game-123",
            unit_value=Decimal("10.00"),
            expiry_minutes=60,
        )

        result = self.use_case.execute(request)

        assert result.expires_at is not None
        # Should be approximately 60 minutes from now
        expected_min = timezone.now() + timedelta(minutes=59)
        expected_max = timezone.now() + timedelta(minutes=61)
        assert expected_min <= result.expires_at <= expected_max


class TestUpdateCasinoFreeBetStatusUseCase:
    """Tests for UpdateCasinoFreeBetStatusUseCase."""

    def setup_method(self):
        """Set up test fixtures."""
        self.repository = MockCasinoFreeBetRepository()
        self.use_case = UpdateCasinoFreeBetStatusUseCase(self.repository)

    def _create_freebet_in_repo(self, **overrides):
        """Helper to create and save a freebet to the mock repo."""
        defaults = {
            "id": 1,
            "public_id": "test-uuid-123",
            "tenant_id": "tenant-1",
            "name": "Test Freebet",
            "currency": FreebetCurrency.ETB,
            "game_id": "game-123",
            "unit_value": Decimal("10.00"),
            "quantity": 5,
            "expiry_minutes": 1440,
            "status": CasinoFreeBetStatus.INACTIVE,
            "created_at": timezone.now(),
        }
        defaults.update(overrides)
        freebet = CasinoFreeBet(**defaults)
        self.repository.freebets[freebet.public_id] = freebet
        return freebet

    def test_activate_inactive_freebet(self):
        """Should activate an inactive freebet."""
        freebet = self._create_freebet_in_repo(status=CasinoFreeBetStatus.INACTIVE)

        result = self.use_case.execute(freebet.public_id, CasinoFreeBetStatus.ACTIVE)

        assert result.status == "ACTIVE"

    def test_deactivate_active_freebet(self):
        """Should deactivate an active freebet."""
        freebet = self._create_freebet_in_repo(status=CasinoFreeBetStatus.ACTIVE)

        result = self.use_case.execute(freebet.public_id, CasinoFreeBetStatus.INACTIVE)

        assert result.status == "INACTIVE"

    def test_freebet_not_found_raises_error(self):
        """Should raise ValueError when freebet is not found."""
        with pytest.raises(ValueError, match="Freebet not found"):
            self.use_case.execute("non-existent-uuid", CasinoFreeBetStatus.ACTIVE)

    def test_update_expired_freebet_raises_error(self):
        """Should raise FreebetExpiredError when freebet is expired."""
        # Create freebet that expired 2 hours ago
        creation_time = timezone.now() - timedelta(hours=3)
        freebet = self._create_freebet_in_repo(
            created_at=creation_time,
            expiry_minutes=60,  # Expired after 1 hour
            status=CasinoFreeBetStatus.ACTIVE,
        )

        with pytest.raises(FreebetExpiredError, match="expired"):
            self.use_case.execute(freebet.public_id, CasinoFreeBetStatus.INACTIVE)

    def test_same_status_raises_error(self):
        """Should raise InvalidFreebetStateError when status is unchanged."""
        freebet = self._create_freebet_in_repo(status=CasinoFreeBetStatus.ACTIVE)

        with pytest.raises(InvalidFreebetStateError, match="already ACTIVE"):
            self.use_case.execute(freebet.public_id, CasinoFreeBetStatus.ACTIVE)

    def test_invalid_status_transition_raises_error(self):
        """Should raise InvalidFreebetStateError for invalid manual status."""
        freebet = self._create_freebet_in_repo(status=CasinoFreeBetStatus.INACTIVE)

        with pytest.raises(InvalidFreebetStateError):
            self.use_case.execute(freebet.public_id, CasinoFreeBetStatus.EXPIRED)


class TestGetExpiringCasinoFreeBetsUseCase:
    """Tests for GetExpiringCasinoFreeBetsUseCase."""

    def setup_method(self):
        """Set up test fixtures."""
        self.repository = MockCasinoFreeBetRepository()
        self.use_case = GetExpiringCasinoFreeBetsUseCase(self.repository)

    def _create_freebet_in_repo(
        self, public_id: str, minutes_until_expiry: int, **overrides
    ):
        """Helper to create freebet with specific time until expiry."""
        # Calculate created_at so it expires in minutes_until_expiry
        expiry_minutes = overrides.get("expiry_minutes", 1440)
        created_at = timezone.now() - timedelta(
            minutes=expiry_minutes - minutes_until_expiry
        )

        defaults = {
            "id": len(self.repository.freebets) + 1,
            "public_id": public_id,
            "tenant_id": "tenant-1",
            "name": f"Freebet {public_id}",
            "currency": FreebetCurrency.ETB,
            "game_id": "game-123",
            "unit_value": Decimal("10.00"),
            "quantity": 5,
            "expiry_minutes": expiry_minutes,
            "status": CasinoFreeBetStatus.ACTIVE,
            "created_at": created_at,
        }
        defaults.update(overrides)
        freebet = CasinoFreeBet(**defaults)
        self.repository.freebets[freebet.public_id] = freebet
        return freebet

    def test_returns_freebets_expiring_within_threshold(self):
        """Should return freebets expiring within the threshold."""
        # Expiring in 12 hours (within 24h threshold)
        self._create_freebet_in_repo("fb-1", minutes_until_expiry=720)
        # Expiring in 48 hours (outside 24h threshold)
        self._create_freebet_in_repo("fb-2", minutes_until_expiry=2880)

        result = self.use_case.execute(hours_threshold=24)

        assert len(result) == 1
        assert result[0].public_id == "fb-1"

    def test_returns_empty_when_no_expiring_freebets(self):
        """Should return empty list when no freebets are expiring soon."""
        # Expiring in 48 hours
        self._create_freebet_in_repo("fb-1", minutes_until_expiry=2880)

        result = self.use_case.execute(hours_threshold=24)

        assert len(result) == 0

    def test_excludes_inactive_freebets(self):
        """Should exclude inactive freebets even if expiring."""
        self._create_freebet_in_repo(
            "fb-1",
            minutes_until_expiry=720,
            status=CasinoFreeBetStatus.INACTIVE,
        )

        result = self.use_case.execute(hours_threshold=24)

        assert len(result) == 0

    def test_excludes_already_expired_freebets(self):
        """Should exclude freebets that have already expired."""
        # Already expired (negative minutes until expiry)
        expiry_minutes = 60
        created_at = timezone.now() - timedelta(
            minutes=120
        )  # Created 2h ago, expires in 1h
        freebet = CasinoFreeBet(
            id=1,
            public_id="fb-expired",
            tenant_id="tenant-1",
            name="Expired Freebet",
            currency=FreebetCurrency.ETB,
            game_id="game-123",
            unit_value=Decimal("10.00"),
            quantity=5,
            expiry_minutes=expiry_minutes,
            status=CasinoFreeBetStatus.ACTIVE,
            created_at=created_at,
        )
        self.repository.freebets[freebet.public_id] = freebet

        result = self.use_case.execute(hours_threshold=24)

        assert len(result) == 0

    def test_custom_hours_threshold(self):
        """Should respect custom hours threshold."""
        # Expiring in 6 hours
        self._create_freebet_in_repo("fb-1", minutes_until_expiry=360)
        # Expiring in 12 hours
        self._create_freebet_in_repo("fb-2", minutes_until_expiry=720)

        # Only 8 hour threshold
        result = self.use_case.execute(hours_threshold=8)

        assert len(result) == 1
        assert result[0].public_id == "fb-1"
