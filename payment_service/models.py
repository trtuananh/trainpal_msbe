from django.db import models
from django.utils.translation import gettext_lazy as _

class Payment(models.Model):
    class PaymentMethod(models.TextChoices):
        ONLINE = "ONL", _("Online")
        OFFLINE = "OFF", _("Offline")

    sender_id = models.IntegerField()
    receiver_id = models.IntegerField()
    payment_id = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=3, choices=PaymentMethod.choices)
    value = models.IntegerField()
    payment_info = models.CharField(max_length=1000, blank=True)
    momo_transaction_id = models.CharField(max_length=100, blank=True)
    momo_payment_type = models.CharField(max_length=100, blank=True)
    is_paid = models.BooleanField(default=False, blank=True)
    success = models.BooleanField(default=False, blank=True)
    message = models.CharField(max_length=1000, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Sender ID: {self.sender_id} to Receiver ID: {self.receiver_id}: {self.value}"
    