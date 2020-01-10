from django.db import models
from django.utils import timezone

class User(models.Model):
    username = models.CharField(max_length=10)
    password = models.CharField(max_length=10)
    date_registered = models.DateTimeField(default=timezone.now)


