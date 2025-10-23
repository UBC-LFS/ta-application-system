from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_control
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from users.models import Role

from users import api as userApi
from observers.mixins import AcceptedAppsReportMixin

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def index(request):
    ''' Index page of Observer's portal '''
    request = userApi.has_user_access(request, utils.OBSERVER)

    return render(request, 'observers/index.html', {
        'loggedin_user': request.user
    })


@method_decorator([never_cache], name='dispatch')
class AcceptedAppsReportObserver(LoginRequiredMixin, View, AcceptedAppsReportMixin):
    pass