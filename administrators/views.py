from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET

from ta_app import utils
from administrators import api as adminApi
from users import api as userApi


@method_decorator([never_cache], name='dispatch')
class Index(LoginRequiredMixin, View):
    ''' Index page of Administrator's portal '''

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        request = userApi.has_admin_access(request, utils.HR)

        apps = adminApi.get_applications()

        today_accepted_apps, today = adminApi.get_accepted_apps_by_day(apps, 'today')
        yesterday_accepted_apps, yesterday = adminApi.get_accepted_apps_by_day(apps, 'yesterday')
        week_ago_accepted_apps, week_ago = adminApi.get_accepted_apps_by_day(apps, 'week_ago')

        context = {
            'loggedin_user': userApi.add_avatar(request.user),
            'accepted_apps': apps.filter(applicationstatus__assigned=utils.ACCEPTED).exclude(applicationstatus__assigned=utils.CANCELLED).order_by('-id').distinct(),
            'today_accepted_apps': today_accepted_apps,
            'today_processed_stats': adminApi.get_processed_stats(today_accepted_apps),
            'yesterday_accepted_apps': yesterday_accepted_apps,
            'yesterday_processed_stats': adminApi.get_processed_stats(yesterday_accepted_apps),
            'week_ago_accepted_apps': week_ago_accepted_apps,
            'week_ago_processed_stats': adminApi.get_processed_stats(week_ago_accepted_apps),
            'today': today,
            'yesterday': yesterday,
            'week_ago': week_ago
        }
        if utils.ADMIN in request.user.roles or utils.SUPERADMIN in request.user.roles:
            sessions = adminApi.get_sessions()
            context['current_sessions'] = sessions.filter(is_archived=False)
            context['archived_sessions'] = sessions.filter(is_archived=True)
            context['apps'] = adminApi.get_applications()
            context['instructors'] = userApi.get_users_by_role(utils.INSTRUCTOR)
            context['students'] = userApi.get_users_by_role(utils.STUDENT)
            context['users'] = userApi.get_users()

        return render(request, 'administrators/index.html', context)