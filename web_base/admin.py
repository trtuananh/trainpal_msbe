from django.contrib import admin

# Register your models here.

from . import models


admin.site.register(models.User)
admin.site.register(models.Location)
admin.site.register(models.Payment)
admin.site.register(models.ChatRoom)
admin.site.register(models.Message)
admin.site.register(models.Course)
admin.site.register(models.TrainingSession)
admin.site.register(models.BookingSession)
admin.site.register(models.Rating)
