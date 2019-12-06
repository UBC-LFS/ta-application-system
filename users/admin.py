from django.contrib import admin
from users.models import Profile

class ProfileAdmin(admin.ModelAdmin):
    fields = ['roles']

admin.site.register(Profile, ProfileAdmin)
