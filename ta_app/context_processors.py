from django.conf import settings

def site_url(request):
    return {
        'site_url': settings.TA_APP_URL
    }

def user_roles(request):
    roles = []
    if hasattr(request.user, 'profile'):
        profile = request.user.profile
        if profile.roles.exists():
            roles = [role.name for role in profile.roles.all()]
    return {
        'user_roles': roles
    }
