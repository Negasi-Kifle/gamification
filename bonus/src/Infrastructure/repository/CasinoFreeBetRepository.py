from datetime import datetime, timedelta
from typing import List, Optional, TYPE_CHECKING
from django.db import transaction
from django.db.models import F, ExpressionWrapper, DateTimeField, DurationField
from django.db.models.functions import Now
from django.utils import timezone

from ...Domain.entities import CasinoFreeBet
from ...Domain.repositories import CasinoFreeBetRepository
from ...Domain.value_objects import CasinoFreeBetStatus, FreebetCurrency

if TYPE_CHECKING:
    from ..models import CasinoFreeBetModel


class DjangoCasinoFreeBetRepository(CasinoFreeBetRepository):
    """Django ORM implementation of the CasinoFreeBetRepository interface."""
    
    def save(self, freebet: CasinoFreeBet) -> CasinoFreeBet:
        """Save a freebet (create or update)."""
        from ..models import CasinoFreeBetModel
        with transaction.atomic():
            if freebet.id:
                # Update existing
                model = CasinoFreeBetModel.objects.select_for_update().get(id=freebet.id)
                self._update_model_from_entity(model, freebet)
                model.save()
            else:
                # Create new
                model = self._create_model_from_entity(freebet)
                model.save()
                freebet.id = model.id
            
            return self._to_entity(model)
    
    def find_by_id(self, freebet_id: int) -> Optional[CasinoFreeBet]:
        """Find freebet by internal ID."""
        from ..models import CasinoFreeBetModel
        try:
            model = CasinoFreeBetModel.objects.get(id=freebet_id)
            return self._to_entity(model)
        except CasinoFreeBetModel.DoesNotExist:
            return None
    
    def find_by_public_id(self, public_id: str) -> Optional[CasinoFreeBet]:
        """Find freebet by public UUID."""
        from ..models import CasinoFreeBetModel
        try:
            model = CasinoFreeBetModel.objects.get(public_id=public_id)
            return self._to_entity(model)
        except CasinoFreeBetModel.DoesNotExist:
            return None
    
    def find_active_by_tenant(self, tenant_id: str, current_time: datetime) -> List[CasinoFreeBet]:
        """Find active freebets for tenant that are not expired.
        
        Uses DB-level filtering for better performance with large datasets.
        """
        from ..models import CasinoFreeBetModel
        
        # Annotate with expiry time and filter at DB level
        # expiry_time = created_at + expiry_minutes (as interval)
        models = CasinoFreeBetModel.objects.filter(
            tenant_id=tenant_id,
            status=CasinoFreeBetModel.Status.ACTIVE
        ).annotate(
            expiry_time=ExpressionWrapper(
                F('created_at') + timedelta(minutes=1) * F('expiry_minutes'),
                output_field=DateTimeField()
            )
        ).filter(
            expiry_time__gt=current_time  # Not expired
        )
        
        return [self._to_entity(m) for m in models]
    
    def find_expiring_soon(self, minutes_threshold: int) -> List[CasinoFreeBet]:
        """Find freebets expiring within the specified minutes.
        
        Uses DB-level filtering for better performance with large datasets.
        Finds freebets where: now < expiry_time <= now + threshold
        """
        from ..models import CasinoFreeBetModel
        now = timezone.now()
        threshold_time = now + timedelta(minutes=minutes_threshold)
        
        # Annotate with expiry time and filter at DB level
        # expiry_time = created_at + expiry_minutes (as interval)
        models = CasinoFreeBetModel.objects.filter(
            status=CasinoFreeBetModel.Status.ACTIVE
        ).annotate(
            expiry_time=ExpressionWrapper(
                F('created_at') + timedelta(minutes=1) * F('expiry_minutes'),
                output_field=DateTimeField()
            )
        ).filter(
            expiry_time__gt=now,  # Not yet expired
            expiry_time__lte=threshold_time  # Expiring within threshold
        )
        
        return [self._to_entity(m) for m in models]
    
    def delete(self, freebet_id: int) -> bool:
        """Delete a freebet."""
        from ..models import CasinoFreeBetModel
        try:
            CasinoFreeBetModel.objects.filter(id=freebet_id).delete()
            return True
        except Exception:
            return False
    
    # --- Private helper methods ---
    
    def _is_expired(self, model: 'CasinoFreeBetModel', current_time: datetime) -> bool:
        """Check if a freebet model is expired."""
        expiry_time = model.created_at + timedelta(minutes=model.expiry_minutes)
        return current_time > expiry_time
    
    def _to_entity(self, model: 'CasinoFreeBetModel') -> CasinoFreeBet:
        """Convert ORM model to domain entity."""
        return CasinoFreeBet(
            id=model.id,
            public_id=str(model.public_id),
            tenant_id=model.tenant_id,
            name=model.name,
            description=model.description,
            currency=FreebetCurrency(model.currency),
            game_id=model.game_id,
            unit_value=model.unit_value,
            quantity=model.quantity,
            expiry_minutes=model.expiry_minutes,
            status=CasinoFreeBetStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
    
    def _create_model_from_entity(self, entity: CasinoFreeBet) -> 'CasinoFreeBetModel':
        """Create a new ORM model from domain entity."""
        from ..models import CasinoFreeBetModel
        return CasinoFreeBetModel(
            public_id=entity.public_id,
            tenant_id=entity.tenant_id,
            name=entity.name,
            description=entity.description,
            currency=entity.currency.value,
            game_id=entity.game_id,
            unit_value=entity.unit_value,
            quantity=entity.quantity,
            expiry_minutes=entity.expiry_minutes,
            status=entity.status.value,
        )
    
    def _update_model_from_entity(self, model: 'CasinoFreeBetModel', entity: CasinoFreeBet) -> None:
        """Update an existing ORM model from domain entity."""
        model.name = entity.name
        model.description = entity.description
        model.currency = entity.currency.value
        model.game_id = entity.game_id
        model.unit_value = entity.unit_value
        model.quantity = entity.quantity
        model.expiry_minutes = entity.expiry_minutes
        model.status = entity.status.value
