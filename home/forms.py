from django import forms
from .models import *

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['message']
