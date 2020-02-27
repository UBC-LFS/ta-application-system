from django.contrib import admin
from users.models import Profile, Confidentiality

class ProfileAdmin(admin.ModelAdmin):
    fields = ['user', 'student_number', 'roles']

class ConfidentialityAdmin(admin.ModelAdmin):
    fields = ['user', 'employee_number']

admin.site.register(Profile, ProfileAdmin)
admin.site.register(Confidentiality, ConfidentialityAdmin)
