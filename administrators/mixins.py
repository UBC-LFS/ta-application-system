from django.conf import settings
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET
from django.urls import reverse, resolve
from urllib.parse import urlparse
from django.core.exceptions import SuspiciousOperation
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count

from ta_app import utils
from administrators.models import Session, Job, WorktagSetting
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

        session_list = Session.objects.all()
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
    

class JobMixin:

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

        job_list = job_filters(request)

        page = request.GET.get('page', 1)
        paginator = Paginator(job_list, utils.TABLE_PAGE_SIZE)

        try:
            jobs = paginator.page(page)
        except PageNotAnInteger:
            jobs = paginator.page(1)
        except EmptyPage:
            jobs = paginator.page(paginator.num_pages)
        
        template = 'administrators/jobs/{0}.html'.format(self.url_name)

        context = {
            'loggedin_user': request.user,
            'jobs': jobs,
            'total_jobs': len(job_list),
            'new_next': adminApi.build_new_next(request)
        }

        if self.url_name == 'prepare_jobs':
            context['worktags'] = settings.WORKTAGS
            context['save_worktag_setting_url'] = request.get_full_path()
            context['delete_worktag_setting_url'] = reverse('administrators:delete_job_worktag_setting')
        
        elif self.url_name == 'progress_jobs':
            request.session['progress_jobs_next'] = request.get_full_path()

        return render(request, template, context)
    

def job_filters(request):
    year_q = request.GET.get('year')
    term_q = request.GET.get('term')
    code_q = request.GET.get('code')
    number_q = request.GET.get('number')
    section_q = request.GET.get('section')
    is_active_q = request.GET.get('is_active')
    instructor_first_name_q = request.GET.get('instructor_first_name')
    instructor_last_name_q = request.GET.get('instructor_last_name')

    job_list = Job.objects.all()

    if bool(year_q):
        job_list = job_list.filter(session__year__icontains=year_q)
    if bool(term_q):
        job_list = job_list.filter(session__term__code__icontains=term_q)
    if bool(code_q):
        job_list = job_list.filter(course__code__name__icontains=code_q)
    if bool(number_q):
        job_list = job_list.filter(course__number__name__icontains=number_q)
    if bool(section_q):
        job_list = job_list.filter(course__section__name__icontains=section_q)
    if bool(is_active_q):
        job_list = job_list.filter(is_active=is_active_q)
    if bool(instructor_first_name_q):
        job_list = job_list.filter(instructors__first_name__icontains=instructor_first_name_q)
    if bool(instructor_last_name_q):
        job_list = job_list.filter(instructors__last_name__icontains=instructor_last_name_q)

    return job_list
