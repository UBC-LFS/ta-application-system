from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET
from django.urls import resolve
from urllib.parse import urlparse
from django.core.exceptions import SuspiciousOperation
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count

from ta_app import utils
from administrators import api as adminApi
from users import api as userApi

 
class SessionMixin:
    def setup(self, request, *args, **kwargs):
        setup = super().setup(request, *args, **kwargs)

        parsed = urlparse(request.get_full_path())
        resolved = resolve(parsed.path)

        if not resolved.url_name:
            raise SuspiciousOperation
        
        self.url_name = resolved.url_name

        return setup

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        request = userApi.has_admin_access(request)
        request.session['next_session'] = adminApi.build_new_next(request)

        year_q = request.GET.get('year')
        term_q = request.GET.get('term')

        session_list = adminApi.get_sessions()
        if bool(year_q):
            session_list = session_list.filter(year__icontains=year_q)
        if bool(term_q):
            session_list = session_list.filter(term__code__icontains=term_q)

        is_archived = False if self.url_name == 'current_sessions' else True
        session_list = session_list.filter(is_archived=is_archived)
        for session in session_list:
            session.num_jobs = session.job_set.filter(course__is_active=True).count()
            session.num_instructors = session.job_set.filter(course__is_active=True).annotate(num_instructors=Count('instructors')).filter(num_instructors__gt=0).count()

        page = request.GET.get('page', 1)
        paginator = Paginator(session_list, utils.TABLE_PAGE_SIZE)

        try:
            sessions = paginator.page(page)
        except PageNotAnInteger:
            sessions = paginator.page(1)
        except EmptyPage:
            sessions = paginator.page(paginator.num_pages)

        template = 'administrators/sessions/{0}.html'.format(self.url_name)

        return render(request, template, context={
            'loggedin_user': request.user,
            'sessions': sessions,
            'total_sessions': len(session_list),
            'new_next': adminApi.build_new_next(request)
        })