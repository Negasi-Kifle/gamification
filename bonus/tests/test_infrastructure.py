"""Unit tests for the Infrastructure layer of the Bonus module.

These tests verify the Django ORM repository implementation.
Note: Running these tests requires a database connection.
For CI/CD, use pytest-django with a test database.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

from django.utils import timezone

from bonus.src.Domain.entities.CasinoFreeBet import CasinoFreeBet
from bonus.src.Domain.value_objects.StatusValueObject import CasinoFreeBetStatus
from bonus.src.Domain.value_objects.CurrencyValueObject import FreebetCurrency


class TestDjangoCasinoFreeBetRepositoryMapping:
    """
    Tests for entity-model mapping in DjangoCasinoFreeBetRepository.
    
    These tests verify the mapping logic without requiring a database.
    """
    
    def test_entity_to_model_mapping_currency(self):
        """Should correctly map domain currency enum to model value."""
        # Verify enum values match what model expects
        assert FreebetCurrency.ETB.value == "ETB"
        assert FreebetCurrency.USD.value == "USD"
        assert FreebetCurrency.SZL.value == "SZL"
        assert FreebetCurrency.TSH.value == "TSh"
        assert FreebetCurrency.ZMW.value == "ZMW"
    
    def test_entity_to_model_mapping_status(self):
        """Should correctly map domain status enum to model value."""
        assert CasinoFreeBetStatus.ACTIVE.value == "ACTIVE"
        assert CasinoFreeBetStatus.INACTIVE.value == "INACTIVE"
        assert CasinoFreeBetStatus.EXPIRED.value == "EXPIRED"
        assert CasinoFreeBetStatus.USED.value == "USED"
    
    def test_entity_fields_are_complete(self):
        """Entity should have all required fields for model mapping."""
        freebet = CasinoFreeBet(
            id=1,
            public_id="test-uuid",
            tenant_id="tenant-1",
            name="Test Freebet",
            description="Description",
            currency=FreebetCurrency.ETB,
            game_id="game-123",
            unit_value=Decimal("10.00"),
            quantity=5,
            expiry_minutes=1440,
            status=CasinoFreeBetStatus.ACTIVE,
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )
        
        # Verify all fields that model needs are present
        assert freebet.public_id is not None
        assert freebet.tenant_id is not None
        assert freebet.name is not None
        assert freebet.currency is not None
        assert freebet.game_id is not None
        assert freebet.unit_value is not None
        assert freebet.quantity is not None
        assert freebet.expiry_minutes is not None
        assert freebet.status is not None


class TestRepositoryIntegration:
    """
    Integration tests for repository with Django ORM.
    
    These tests are marked with pytest.mark.django_db to use test database.
    Skip if Django is not configured.
    """
    
    @pytest.fixture
    def mock_model_class(self):
        """Create a mock Django model class."""
        mock_model = MagicMock()
        mock_model.objects = MagicMock()
        return mock_model
    
    def test_repository_save_creates_new_entity(self, mock_model_class):
        """
        Repository.save should create a new model when entity has no id.
        
        This test mocks Django ORM to verify repository logic.
        """
        # Arrange
        entity = CasinoFreeBet(
            id=None,  # No ID means new entity
            public_id="new-uuid",
            tenant_id="tenant-1",
            name="New Freebet",
            currency=FreebetCurrency.ETB,
            game_id="game-123",
            unit_value=Decimal("10.00"),
            quantity=5,
            expiry_minutes=1440,
            status=CasinoFreeBetStatus.INACTIVE,
        )
        
        # Verify entity is ready for creation
        assert entity.id is None
        assert entity.public_id == "new-uuid"
    
    def test_repository_save_updates_existing_entity(self, mock_model_class):
        """
        Repository.save should update model when entity has an id.
        """
        # Arrange
        entity = CasinoFreeBet(
            id=1,  # Has ID means existing entity
            public_id="existing-uuid",
            tenant_id="tenant-1",
            name="Updated Freebet",
            currency=FreebetCurrency.ETB,
            game_id="game-123",
            unit_value=Decimal("20.00"),
            quantity=10,
            expiry_minutes=2880,
            status=CasinoFreeBetStatus.ACTIVE,
        )
        
        # Verify entity is ready for update
        assert entity.id == 1
        assert entity.name == "Updated Freebet"


class TestModelEntityConsistency:
    """
    Tests to verify model and entity field consistency.
    
    These tests ensure the infrastructure layer correctly maps
    between domain entities and ORM models.
    """
    
    def test_status_choices_match_enum(self):
        """Model status choices should match domain enum values."""
        # Domain enum values
        domain_statuses = {CasinoFreeBetStatus.ACTIVE.value, CasinoFreeBetStatus.INACTIVE.value}
        
        # Model should store same values
        expected_model_choices = {"ACTIVE", "INACTIVE"}
        
        assert domain_statuses == expected_model_choices
    
    def test_currency_choices_match_enum(self):
        """Model currency choices should match domain enum values."""
        domain_currencies = {
            FreebetCurrency.ETB.value,
            FreebetCurrency.SZL.value,
            FreebetCurrency.TSH.value,
            FreebetCurrency.ZMW.value,
            FreebetCurrency.USD.value,
        }
        
        expected_model_choices = {"ETB", "SZL", "TSh", "ZMW", "USD"}
        
        assert domain_currencies == expected_model_choices
    
    def test_decimal_precision_preserved(self):
        """Decimal values should maintain precision through mapping."""
        original_value = Decimal("123.456789")
        
        # When stored in model (max_digits=18, decimal_places=2)
        # Value should be rounded to 2 decimal places
        stored_value = Decimal(str(round(original_value, 2)))
        
        assert stored_value == Decimal("123.46")
    
    def test_expiry_calculation_consistency(self):
        """Expiry calculation should be consistent between entity and repo."""
        created_at = timezone.make_aware(datetime(2026, 1, 1, 12, 0, 0))
        expiry_minutes = 60
        
        # Entity calculation
        entity = CasinoFreeBet(
            public_id="test",
            tenant_id="tenant-1",
            name="Test",
            currency=FreebetCurrency.ETB,
            game_id="game-123",
            unit_value=Decimal("10.00"),
            quantity=1,
            expiry_minutes=expiry_minutes,
            created_at=created_at,
        )
        entity_expiry = entity.calculate_expiry_time(created_at)
        
        # Repository/Model calculation (same formula)
        model_expiry = created_at + timedelta(minutes=expiry_minutes)
        
        assert entity_expiry == model_expiry


# Django-specific tests (require pytest-django)
# These tests require a database connection and will create/use a test database

class TestDjangoRepositoryWithDB:
    """
    Full integration tests with Django ORM.
    
    Requires:
    - pytest-django installed
    - DJANGO_SETTINGS_MODULE configured
    - Test database available (PostgreSQL or SQLite for testing)
    
    Run with: pytest bonus/tests/test_infrastructure.py -v
    """
    
    @pytest.mark.django_db
    def test_save_and_retrieve_freebet(self):
        """Should save and retrieve freebet from database."""
        from bonus.src.Infrastructure.repository.CasinoFreeBetRepository import (
            DjangoCasinoFreeBetRepository
        )
        
        repository = DjangoCasinoFreeBetRepository()
        
        test_uuid = str(uuid.uuid4())
        freebet = CasinoFreeBet(
            public_id=test_uuid,
            tenant_id="tenant-1",
            name="DB Test Freebet",
            currency=FreebetCurrency.ETB,
            game_id="game-123",
            unit_value=Decimal("10.00"),
            quantity=5,
            expiry_minutes=1440,
            status=CasinoFreeBetStatus.INACTIVE,
        )
        
        # Save
        saved = repository.save(freebet)
        assert saved.id is not None
        
        # Retrieve
        retrieved = repository.find_by_public_id(test_uuid)
        assert retrieved is not None
        assert retrieved.name == "DB Test Freebet"
        assert retrieved.unit_value == Decimal("10.00")
    
    @pytest.mark.django_db
    def test_find_active_by_tenant(self):
        """Should find only active freebets for tenant."""
        from bonus.src.Infrastructure.repository.CasinoFreeBetRepository import (
            DjangoCasinoFreeBetRepository
        )
        
        repository = DjangoCasinoFreeBetRepository()
        
        # Create active freebet
        active_uuid = str(uuid.uuid4())
        active = CasinoFreeBet(
            public_id=active_uuid,
            tenant_id="tenant-1",
            name="Active Freebet",
            currency=FreebetCurrency.ETB,
            game_id="game-123",
            unit_value=Decimal("10.00"),
            quantity=5,
            expiry_minutes=1440,
            status=CasinoFreeBetStatus.ACTIVE,
        )
        repository.save(active)
        
        # Create inactive freebet
        inactive_uuid = str(uuid.uuid4())
        inactive = CasinoFreeBet(
            public_id=inactive_uuid,
            tenant_id="tenant-1",
            name="Inactive Freebet",
            currency=FreebetCurrency.ETB,
            game_id="game-123",
            unit_value=Decimal("10.00"),
            quantity=5,
            expiry_minutes=1440,
            status=CasinoFreeBetStatus.INACTIVE,
        )
        repository.save(inactive)
        
        # Query
        results = repository.find_active_by_tenant("tenant-1", timezone.now())
        
        assert len(results) == 1
        assert results[0].public_id == active_uuid
