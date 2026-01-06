from django.conf import settings
from django.shortcuts import render
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.views.decorators.cache import cache_control, never_cache
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import datetime

from ta_app import utils
from administrators.forms import AdminJobEditForm, InstructorUpdateForm, WorktagSetting
from administrators import api as adminApi
from instructors.mixins import SummaryApplicantsMixin
from users import api as userApi


@method_decorator([never_cache], name='dispatch')
class PrepareJobs(LoginRequiredMixin, View):
    ''' Display preparing jobs '''

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        request = userApi.has_admin_access(request)

        job_list = adminApi.job_filters(request, 'prepare_jobs')

        page = request.GET.get('page', 1)
        paginator = Paginator(job_list, utils.TABLE_PAGE_SIZE)

        try:
            jobs = paginator.page(page)
        except PageNotAnInteger:
            jobs = paginator.page(1)
        except EmptyPage:
            jobs = paginator.page(paginator.num_pages)

        for job in jobs:
            job.worktag_setting = None
            worktag_settings_filtered = WorktagSetting.objects.filter(application_id__in=[app.id for app in job.application_set.all()]).order_by('-updated_at')
            if not job.worktag_setting and worktag_settings_filtered.exists():
                job.worktag_setting = worktag_settings_filtered.first()

        return render(request, 'administrators/jobs/prepare_jobs.html', {
            'loggedin_user': request.user,
            'jobs': jobs,
            'total_jobs': len(job_list),
            'new_next': adminApi.build_new_next(request),
            'worktags': settings.WORKTAGS,
            'save_worktag_setting_url': request.get_full_path(),
            'delete_worktag_setting_url': reverse('administrators:delete_job_worktag_setting')
        })

    @method_decorator(require_POST)
    def post(self, request, *args, **kwargs):
        is_valid = adminApi.valid_worktag_setting(request)
        if is_valid:
            jid, aid, program_info, worktag = adminApi.get_worktag(request)
            job = adminApi.get_job(jid)

            create_objs = []
            update_objs = []
            update_fields = []
            for app in job.application_set.all():
                success = False

                # Update Worktag Setting
                ws_filtered = WorktagSetting.objects.filter(application_id=app.id, job_id=job.id)
                if ws_filtered.exists():
                    ws = ws_filtered.first()
                    if not adminApi.compare_two_dicts_by_key(ws.program_info, program_info):
                        ws.program_info = program_info
                        update_fields.append('program_info')
                    
                    if ws.worktag != worktag:
                        ws.worktag = worktag
                        update_fields.append('worktag')
                    
                    if len(update_fields) > 0:
                        update_objs.append(ws)
                        success = True
                else:
                    create_objs.append(WorktagSetting(application_id=app.id, job_id=jid, program_info=program_info, worktag=worktag))
                    success = True
                
                if success:
                    adminApi.update_worktag_in_admin_docs(app, worktag, None)
            
            has_submitted = False
            if len(create_objs) > 0:
                WorktagSetting.objects.bulk_create(create_objs)
                has_submitted = True
            
            if len(update_objs) > 0:
                WorktagSetting.objects.bulk_update(update_objs, update_fields)
                has_submitted = True

            if has_submitted:
                
                messages.success(request, 'Success! Updated the Worktag Setting of applications in this Job (Job ID: {0})'.format(jid))
        else:
            messages.error(request, 'An error occurred. Your input values are not valid. Please try again.')

        return HttpResponseRedirect(request.POST.get('next'))


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_job_worktag_setting(request):
    jid = request.POST['job']
    job = adminApi.get_job(jid)

    deleted = WorktagSetting.objects.filter(job_id=jid).delete()
    if deleted[0] == job.application_set.count():
        messages.success(request, 'Success! Deleted the Worktag Setting of applications in this Job (Job ID: {0})'.format(jid))
    elif deleted[0] < job.application_set.count():
        messages.warning(request, 'Warning! There are some undeleted applications in this Job (Job ID: {0})'.format(jid))
    else:
        messages.error(request, 'An error occurred. Failed to delete the Worktag Setting of applications in this Job (Job ID: {0}). Please try again.'.format(jid))
    
    return HttpResponseRedirect(request.POST.get('next'))


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_app_worktag_setting(request):
    aid = request.POST['application']
    deleted = WorktagSetting.objects.filter(application_id=aid).delete()
    if deleted[0] == 1:
        messages.success(request, 'Success! Deleted the Worktag Setting of this Application (Application ID: {0})'.format(aid))
    else:
        messages.error(request, 'An error occurred. Failed to delete the Worktag Setting of this Application (Application ID: {0}). Please try again.'.format(aid))
    return HttpResponseRedirect(request.POST.get('next'))


@method_decorator([never_cache], name='dispatch')
class ProgressJobs(LoginRequiredMixin, View):
    ''' See jobs in progress '''
    
    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        request = userApi.has_admin_access(request)

        job_list = adminApi.job_filters(request, 'progress_jobs')

        page = request.GET.get('page', 1)
        paginator = Paginator(job_list, utils.TABLE_PAGE_SIZE)

        try:
            jobs = paginator.page(page)
        except PageNotAnInteger:
            jobs = paginator.page(1)
        except EmptyPage:
            jobs = paginator.page(paginator.num_pages)

        request.session['progress_jobs_next'] = request.get_full_path()

        return render(request, 'administrators/jobs/progress_jobs.html', {
            'loggedin_user': request.user,
            'jobs': jobs,
            'total_jobs': len(job_list),
            'new_next': adminApi.build_new_next(request),
            'download_job_report_url': reverse('administrators:download_job_report')
        })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_job_applications(request, session_slug, job_slug):
    ''' Display a job's applications '''

    request = userApi.has_admin_access(request)
    job = adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)
    request.session['summary_applicants_next'] = request.get_full_path()

    return render(request, 'administrators/jobs/show_job_applications.html', {
        'loggedin_user': request.user,
        'job': adminApi.add_job_with_applications_statistics(job),
        'apps': job.application_set.all(),
        'app_status': utils.APP_STATUS,
        'next': request.session.get('progress_jobs_next'),
        'summary_of_applicants_link': reverse('administrators:summary_applicants', kwargs={'session_slug': job.session.slug, 'job_slug': job.course.slug}),
        'new_next': adminApi.build_new_next(request)
    })


@method_decorator([never_cache], name='dispatch')
class SummaryApplicants(LoginRequiredMixin, SummaryApplicantsMixin, View):
    pass


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def download_job_report(request):
    jobs = adminApi.job_filters(request, 'progress_jobs')
    
    data = []
    for job in jobs:
        data.append({
            'Year': job.session.year,
            'Term': job.session.term.code,
            'Course Code': job.course.code.name,
            'Course Number': job.course.number.name,
            'Course Section': job.course.section.name,
            'Course Title': job.course.name,
            'Course Overview': adminApi.extract_text(job.course_overview),
            'Description': adminApi.extract_text(job.description)
        })

    return JsonResponse({ 'status': 'success', 'data': data })


@method_decorator([never_cache], name='dispatch')
class InstructorJobs(LoginRequiredMixin, View):
    ''' Display jobs by instructor '''

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):    
        request = userApi.has_admin_access(request)

        first_name_q = request.GET.get('first_name')
        last_name_q = request.GET.get('last_name')
        preferred_name_q = request.GET.get('preferred_name')
        cwl_q = request.GET.get('cwl')

        user_list = userApi.get_instructors()
        if bool(first_name_q):
            user_list = user_list.filter(first_name__icontains=first_name_q)
        if bool(last_name_q):
            user_list = user_list.filter(last_name__icontains=last_name_q)
        if bool(preferred_name_q):
            user_list = user_list.filter(profile__preferred_name__icontains=preferred_name_q)
        if bool(cwl_q):
            user_list = user_list.filter(username__icontains=cwl_q)

        page = request.GET.get('page', 1)
        paginator = Paginator(user_list, utils.TABLE_PAGE_SIZE)

        try:
            users = paginator.page(page)
        except PageNotAnInteger:
            users = paginator.page(1)
        except EmptyPage:
            users = paginator.page(paginator.num_pages)

        for user in users:
            user.total_applicants = adminApi.add_total_applicants(user)

        return render(request, 'administrators/jobs/instructor_jobs.html', {
            'loggedin_user': request.user,
            'users': users,
            'total_users': len(user_list),
            'new_next': adminApi.build_new_next(request)
        })


@method_decorator([never_cache], name='dispatch')
class InstructorJobsDetails(LoginRequiredMixin, View):
    ''' Display jobs that an instructor has '''
    
    def setup(self, request, *args, **kwargs):
        setup = super().setup(request, *args, **kwargs)
        username = kwargs.get('username', None)
        if not username:
            raise Http404
        
        self.username = username
        return setup
    
    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        request = userApi.has_admin_access(request)
        adminApi.can_req_parameters_access(request, 'job', ['next', 'p'])

        user = userApi.get_user(self.username, 'username')
        user.total_applicants = adminApi.add_total_applicants(user)
        
        jobs = []
        for job in user.job_set.all():
            apps = []
            for app in job.application_set.all():
                app.applicant.gta = userApi.get_gta_flag(app.applicant)
                apps.append(app)
            job.apps = apps
            jobs.append(job)
        user.jobs =jobs
        
        return render(request, 'administrators/jobs/instructor_jobs_details.html', {
            'loggedin_user': request.user,
            'user': userApi.add_avatar(user),
            'next': adminApi.get_next(request),
            'undergrad_status_id': userApi.get_undergraduate_status_id() 
        })


@method_decorator([never_cache], name='dispatch')
class StudentJobs(LoginRequiredMixin, View):
    ''' Display jobs by student '''

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        request = userApi.has_admin_access(request)

        first_name_q = request.GET.get('first_name')
        last_name_q = request.GET.get('last_name')
        preferred_name_q = request.GET.get('preferred_name')
        cwl_q = request.GET.get('cwl')

        user_list = userApi.get_users()
        if bool(first_name_q):
            user_list = user_list.filter(first_name__icontains=first_name_q)
        if bool(last_name_q):
            user_list = user_list.filter(last_name__icontains=last_name_q)
        if bool(preferred_name_q):
            user_list = user_list.filter(profile__preferred_name__icontains=preferred_name_q)
        if bool(cwl_q):
            user_list = user_list.filter(username__icontains=cwl_q)

        user_list = user_list.filter(profile__roles__name=utils.STUDENT)

        page = request.GET.get('page', 1)
        paginator = Paginator(user_list, utils.TABLE_PAGE_SIZE)

        try:
            users = paginator.page(page)
        except PageNotAnInteger:
            users = paginator.page(1)
        except EmptyPage:
            users = paginator.page(paginator.num_pages)

        for user in users:
            user.gta = userApi.get_gta_flag(user)

        return render(request, 'administrators/jobs/student_jobs.html', {
            'loggedin_user': request.user,
            'users': users,
            'total_users': len(user_list),
            'new_next': adminApi.build_new_next(request)
        })


@method_decorator([never_cache], name='dispatch')
class StudentJobsDetails(LoginRequiredMixin, View):
    ''' Display jobs that an student has '''
    
    def setup(self, request, *args, **kwargs):
        setup = super().setup(request, *args, **kwargs)
        username = kwargs.get('username', None)
        if not username:
            raise Http404
        
        self.username = username
        return setup
    
    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        request = userApi.has_admin_access(request)
        adminApi.can_req_parameters_access(request, 'job-tab', ['next', 'p', 't'])

        next = adminApi.get_next(request)
        page = request.GET.get('p')

        user = userApi.get_user(self.username, 'username')
        apps = user.application_set.all()
        apps = adminApi.add_app_info_into_applications(apps, ['offered', 'accepted', 'declined', 'cancelled'])

        offered_apps = []
        accepted_apps = []
        for app in apps:
            if app.offered:
                offered_apps.append(app)

            if adminApi.check_valid_accepted_app_or_not(app):
                accepted_apps.append(app)

        return render(request, 'administrators/jobs/student_jobs_details.html', {
            'loggedin_user': request.user,
            'user': userApi.add_avatar(user),
            'total_assigned_hours': adminApi.get_total_assigned_hours_admin(apps),
            'apps': apps,
            'offered_apps': offered_apps,
            'accepted_apps': accepted_apps,
            'tab_urls': {
                'all': adminApi.build_url(request.path, next, page, 'all'),
                'offered': adminApi.build_url(request.path, next, page, 'offered'),
                'accepted': adminApi.build_url(request.path, next, page, 'accepted')
            },
            'current_tab': request.GET.get('t'),
            'app_status': utils.APP_STATUS,
            'next': next
        })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_job(request, session_slug, job_slug):
    ''' Edit a job '''
    request = userApi.has_admin_access(request)
    adminApi.can_req_parameters_access(request, 'job', ['next', 'p'])

    job = adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)
    if request.method == 'POST':

        # Check whether a next url is valid or not
        adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

        form = AdminJobEditForm(request.POST, instance=job)
        if form.is_valid():
            updated_job = form.save(commit=False)
            updated_job.updated_at = datetime.now()
            updated_job.save()

            if updated_job:
                messages.success(request, 'Success! {0} {1} {2} {3} {4} updated'.format(updated_job.session.year, updated_job.session.term.code, updated_job.course.code.name, updated_job.course.number.name, updated_job.course.section.name))
                return HttpResponseRedirect(request.POST.get('next'))
            else:
                messages.error(request, 'An error occurred while updating a job.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect(request.get_full_path())

    return render(request, 'administrators/jobs/edit_job.html', {
        'loggedin_user': request.user,
        'job': job,
        'instructors': job.instructors.all(),
        'form': AdminJobEditForm(data=None, instance=job),
        'next': adminApi.get_next(request)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def search_instructors(request):
    ''' Search job instructors '''
    request = userApi.has_admin_access(request)

    if request.method == 'GET':
        instructors = userApi.get_instructors()
        username = request.GET.get('username')

        data = []
        if bool(username) == True:
            job = adminApi.get_job_by_session_slug_job_slug(request.GET.get('session_slug'), request.GET.get('job_slug'))
            for ins in instructors.filter( Q(username__icontains=username) & ~Q(pk__in=[ins.id for ins in job.instructors.all()]) ):
                data.append({
                    'id': ins.id,
                    'username': ins.username,
                    'first_name': ins.first_name,
                    'last_name': ins.last_name
                })
        return JsonResponse({ 'data': data, 'status': 'success' }, safe=False)
    return JsonResponse({ 'data': [], 'status': 'error' }, safe=False)


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def add_job_instructors(request, session_slug, job_slug):
    ''' Add job instructors '''
    request = userApi.has_admin_access(request)
    if request.method == 'POST':
        job = adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)

        form = InstructorUpdateForm(request.POST)
        if form.is_valid():
            instructor = form.cleaned_data['instructors']
            instructors_ids = [ ins.id for ins in job.instructors.all() ]
            if int(request.POST.get('instructors')) in instructors_ids:
                return JsonResponse({ 'status': 'error', 'message': 'An error occurred. Instructor {0} ({1})is already added int this job.'.format(instructor.first().username, instructor.first().get_full_name()) })

            if adminApi.add_job_instructors(job, form.cleaned_data['instructors']):
                return JsonResponse({
                    'status': 'success',
                    'user': {
                        'id': instructor.first().id,
                        'username': instructor.first().username,
                        'first_name': instructor.first().first_name,
                        'last_name': instructor.first().last_name
                    },
                    'data': {
                        'delete_url': reverse('administrators:delete_job_instructors', args=[session_slug, job_slug]),
                        'csrfmiddlewaretoken': request.POST.get('csrfmiddlewaretoken')
                    },
                    'message': 'Success! Instructor {0} added.'.format(instructor.first().username)
                })

            return JsonResponse({
                'status': 'error',
                'message': 'An error occurred while adding an instructor into a job.'
            })
        else:
            errors = form.errors.get_json_data()
            return JsonResponse({ 'status': 'error', 'message': 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ) })
    return JsonResponse({ 'status': 'error', 'message': 'Request method is not POST.' })



@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_job_instructors(request, session_slug, job_slug):
    ''' Delete job instructors '''
    request = userApi.has_admin_access(request)
    if request.method == 'POST':
        job = adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)

        if job.instructors.count() == 0:
            return JsonResponse({ 'status': 'error', 'message': 'An error occurred. Instructors are empty.' })

        form = InstructorUpdateForm(request.POST);
        if form.is_valid():
            instructor = form.cleaned_data['instructors']
            instructors_ids = [ ins.id for ins in job.instructors.all() ]
            if int(request.POST.get('instructors')) not in instructors_ids:
                return JsonResponse({ 'status': 'error', 'message': 'An error occurred. No instructor {0} {1} exists.'.format(instructor.first().username, instructor.first().get_full_name()) })

            if adminApi.remove_job_instructors(job, instructor):
                return JsonResponse({
                    'status': 'success',
                    'username': instructor.first().username,
                    'message': 'Success! Instructor {0} removed.'.format(instructor.first().username)
                })
            return JsonResponse({ 'status': 'error', 'message': 'An error occurred while removing an instructor into a job.' })
        else:
            errors = form.errors.get_json_data()
            return JsonResponse({ 'status': 'error', 'message': 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ) })
    return JsonResponse({ 'status': 'error', 'message': 'Request method is not POST.' })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_job(request, session_slug, job_slug):
    ''' Display job details '''
    request = userApi.has_admin_access(request, utils.HR)
    adminApi.can_req_parameters_access(request, 'job-app', ['next', 'p'])

    return render(request, 'administrators/jobs/show_job.html', {
        'loggedin_user': request.user,
        'job': adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug),
        'next': adminApi.get_next(request)
    })