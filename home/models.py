from django.db import models
import datetime as dt


class Announcement(models.Model):
    message = models.TextField(null=True, blank=True)
    updated_at = models.DateField(default=dt.date.today)
