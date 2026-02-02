from django.db import models


class CasinoFreeBetModel(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
    
    class Currency(models.TextChoices):
        ETB = "ETB", "Ethiopian Birr"
        SZL = "SZL", "Swazi Lilangeni"
        TSH = "TSh", "Tanzanian Shilling"
        ZMW = "ZMW", "Zambian Kwacha"
        USD = "USD", "US Dollar"
    
    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(unique=True, db_index=True)
    tenant_id = models.CharField(max_length=100, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    currency = models.CharField(max_length=5, choices=Currency.choices)
    game_id = models.CharField(max_length=100, db_index=True)
    unit_value = models.DecimalField(max_digits=18, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    expiry_minutes = models.PositiveIntegerField()
    status = models.CharField( max_length=20, choices=Status.choices, default=Status.INACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = "bonus"
        db_table = "bonus_casino_freebet"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant_id", "status"]),
            models.Index(fields=["created_at", "expiry_minutes"]),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.public_id})"
