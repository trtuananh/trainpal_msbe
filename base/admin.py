from django.contrib import admin

# Register your models here.

from . import models


admin.site.register(models.Sport)
admin.site.register(models.User)
admin.site.register(models.Location)
admin.site.register(models.PaymentMethod)
admin.site.register(models.CardMethod)
admin.site.register(models.EBankingMethod)
admin.site.register(models.PaymentHistory)
admin.site.register(models.ChatRoom)
admin.site.register(models.Message)
admin.site.register(models.Course)
admin.site.register(models.AvailableSession)
admin.site.register(models.TrainingSession)
admin.site.register(models.BookingSession)
admin.site.register(models.Rating)
