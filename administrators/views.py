import os
from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.views.decorators.cache import cache_control, never_cache
from io import StringIO
from django.core.exceptions import SuspiciousOperation
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods, require_GET, require_POST

from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from ta_app import utils
from administrators.models import Session, Job, Application, ApplicationStatus
from administrators.forms import *
from administrators import api as adminApi

from users.models import *
from users.forms import *
from users import api as userApi

from datetime import date, datetime
import copy

from observers.mixins import AcceptedAppsReportMixin

APP_STATUS = {
    'none': ApplicationStatus.NONE,
    'applied': ApplicationStatus.NONE,
    'selected': ApplicationStatus.SELECTED,
    'offered': ApplicationStatus.OFFERED,
    'accepted': ApplicationStatus.ACCEPTED,
    'declined': ApplicationStatus.DECLINED,
    'cancelled': ApplicationStatus.CANCELLED
}


@method_decorator([never_cache], name='dispatch')
class Index(LoginRequiredMixin, View):
    ''' Index page of Administrator's portal '''

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        request = userApi.has_admin_access(request, Role.HR)

        apps = adminApi.get_applications()

        today_accepted_apps, today = adminApi.get_accepted_apps_by_day(apps, 'today')
        yesterday_accepted_apps, yesterday = adminApi.get_accepted_apps_by_day(apps, 'yesterday')
        week_ago_accepted_apps, week_ago = adminApi.get_accepted_apps_by_day(apps, 'week_ago')

        context = {
            'loggedin_user': userApi.add_avatar(request.user),
            'accepted_apps': apps.filter(applicationstatus__assigned=ApplicationStatus.ACCEPTED).exclude(applicationstatus__assigned=ApplicationStatus.CANCELLED).order_by('-id').distinct(),
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
        if Role.ADMIN in request.user.roles or Role.SUPERADMIN in request.user.roles:
            sessions = adminApi.get_sessions()
            context['current_sessions'] = sessions.filter(is_archived=False)
            context['archived_sessions'] = sessions.filter(is_archived=True)
            context['apps'] = adminApi.get_applications()
            context['instructors'] = userApi.get_users_by_role(Role.INSTRUCTOR)
            context['students'] = userApi.get_users_by_role(Role.STUDENT)
            context['users'] = userApi.get_users()

        return render(request, 'administrators/index.html', context)


# Sessions


@method_decorator([never_cache], name='dispatch')
class CurrentSessions(LoginRequiredMixin, View):
    ''' Display all information of sessions and create a session '''

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

        session_list = session_list.filter(is_archived=False)
        session_list = adminApi.add_num_instructors(session_list)

        page = request.GET.get('page', 1)
        paginator = Paginator(session_list, utils.TABLE_PAGE_SIZE)

        try:
            sessions = paginator.page(page)
        except PageNotAnInteger:
            sessions = paginator.page(1)
        except EmptyPage:
            sessions = paginator.page(paginator.num_pages)

        return render(request, 'administrators/sessions/current_sessions.html', context={
            'loggedin_user': request.user,
            'sessions': sessions,
            'total_sessions': len(session_list),
            'new_next': adminApi.build_new_next(request)
        })


@method_decorator([never_cache], name='dispatch')
class ArchivedSessions(LoginRequiredMixin, View):
    ''' Display all information of sessions and create a session '''

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

        session_list = session_list.filter(is_archived=True)
        session_list = adminApi.add_num_instructors(session_list)

        page = request.GET.get('page', 1)
        paginator = Paginator(session_list, utils.TABLE_PAGE_SIZE)

        try:
            sessions = paginator.page(page)
        except PageNotAnInteger:
            sessions = paginator.page(1)
        except EmptyPage:
            sessions = paginator.page(paginator.num_pages)

        return render(request, 'administrators/sessions/archived_sessions.html', context={
            'loggedin_user': request.user,
            'sessions': sessions,
            'total_sessions': len(session_list),
            'new_next': adminApi.build_new_next(request)
        })


@method_decorator([never_cache], name='dispatch')
class ShowSession(LoginRequiredMixin, View):
    ''' Display session details '''

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        session_slug = kwargs['session_slug']

        request = userApi.has_admin_access(request)
        adminApi.can_req_parameters_access(request, 'session', ['next', 'p'])

        return render(request, 'administrators/sessions/show_session.html', context={
            'loggedin_user': request.user,
            'session': adminApi.get_session(session_slug, 'slug'),
            'next': adminApi.get_next(request)
        })

from django.forms.models import model_to_dict

@method_decorator([never_cache], name='dispatch')
class CreateSession(LoginRequiredMixin, View):
    ''' Create a session '''

    form_class = SessionForm

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        request = userApi.has_admin_access(request)

        sessions = adminApi.get_sessions()
        return render(request, 'administrators/sessions/create_session.html', context={
            'loggedin_user': request.user,
            'current_sessions': sessions.filter(is_archived=False),
            'archived_sessions': sessions.filter(is_archived=True),
            'form': self.form_class(initial={
                'year': date.today().year,
                'title': 'TA Application'
            })
        })

    @method_decorator(require_POST)
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            data['term'] = data['term'].id
            data['is_visible'] = False if data['is_archived'] == True else data['is_visible']

            request.session['session_form_data'] = data
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))
            return redirect('administrators:create_session')

        return redirect('administrators:create_session_setup_courses')


@method_decorator([never_cache], name='dispatch')
class CreateSessionSetupCourses(LoginRequiredMixin, View):
    form_class = SessionConfirmationForm

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        request = userApi.has_admin_access(request)
        data = request.session.get('session_form_data', None)

        if not data:
            messages.error(request, 'Oops! Something went wrong for some reason. No data found.')
            return redirect('administrators:create_session')

        year = data['year']
        term = adminApi.get_term(data['term'])
        courses = adminApi.get_courses_by_term(data['term'])

        for course in courses:
            job = course.job_set.filter(session__year=int(year)-1)
            course.prev_job = job.first() if job.exists() else None

        return render(request, 'administrators/sessions/create_session_setup_courses.html', context={
            'loggedin_user': request.user,
            'session': adminApi.make_session_info(data, term),
            'term': term,
            'courses': courses
        })

    @method_decorator(require_POST)
    def post(self, request, *args, **kwargs):
        path = request.POST.get('submit_path', None)

        if path != 'Save Changes' and path != 'Save without Copy':
            messages.error(request, 'Oops! Something went wrong for some reason. No valid path found.')
            return redirect('administrators:create_session')

        data = request.session['session_form_data']
        data['selected_course_ids'] = request.POST.getlist('is_course_selected')
        data['copied_ids'] = request.POST.getlist('is_copied') if path == 'Save Changes' else []

        request.session['session_form_data'] = data
        return redirect('administrators:create_session_confirmation')


@method_decorator([never_cache], name='dispatch')
class CreateSessionConfirmation(LoginRequiredMixin, View):
    ''' Confirm all the inforamtion to create a session '''

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        request = userApi.has_admin_access(request)

        data = request.session.get('session_form_data', None)

        if not data:
            messages.error(request, 'Oops! Something went wrong for some reason. No data found.')
            return redirect('administrators:create_session_setup_courses')

        year = data['year']
        term = adminApi.get_term(data['term'])
        course_ids = data['selected_course_ids']
        copied_ids = data['copied_ids']

        courses = []
        selected_jobs = []
        for id in course_ids:
            course = adminApi.get_course(id)
            course.is_copied = False
            selected_job = {
                    'id': course.id,
                    'instructors': [],
                    'assigned_ta_hours': 0.0,
                    'course_overview': course.overview,
                    'description': course.job_description,
                    'note': course.job_note,
                    'is_active': True
                }

            if id in copied_ids:
                course.is_copied = True
                jobs = course.job_set.filter(session__year=int(year)-1)
                job = jobs.first() if jobs.exists() else None
                if job:
                    selected_job = {
                        'id': course.id,
                        'instructors': job.instructors.all() if job.instructors.count() > 0 else [],
                        'assigned_ta_hours': job.assigned_ta_hours,
                        'course_overview': job.course_overview,
                        'description': job.description,
                        'note': job.note,
                        'is_active': job.is_active
                    }

            course.selected_job = selected_job
            courses.append(course)

            copied_job = copy.deepcopy(selected_job)
            if len(copied_job['instructors']) > 0:
                copied_job['instructors'] = [ instructor.id for instructor in job.instructors.all() ]
            selected_jobs.append(copied_job)

        data['selected_jobs'] = selected_jobs
        request.session['session_form_data'] = data

        return render(request, 'administrators/sessions/create_session_confirmation.html', context={
            'loggedin_user': request.user,
            'session': adminApi.make_session_info(data, term),
            'term': term,
            'courses': courses,
            'num_courses': len(courses),
            'num_copied_ids': len(copied_ids)
        })

    @method_decorator(require_POST)
    def post(self, request, *args, **kwargs):
        data = request.session.get('session_form_data', None)
        selected_jobs = data.get('selected_jobs', None)

        if not data or not selected_jobs:
            messages.error(request, 'Oops! Something went wrong for some reason. No data found.')
            return redirect('administrators:create_session_setup_courses')

        year = data['year']
        term = adminApi.get_term(data['term'])

        # Create a session
        session_obj = Session.objects.filter(year=year, term=term)
        if session_obj.exists():
            messages.error(request, 'Oops! Something went wrong. The session already exists!')
            return redirect('administrators:create_session')

        session = Session.objects.create(
            year = year,
            term = term,
            title = data['title'],
            description = data['description'],
            note = data['note'],
            is_visible = data['is_visible'],
            is_archived = data['is_archived']
        )

        jobs = []
        job_instructors = {}
        for selected_job in selected_jobs:
            course = adminApi.get_course(selected_job['id'])

            # Create a job
            created_job = Job(
                session = session,
                course = course,
                assigned_ta_hours = selected_job['assigned_ta_hours'],
                course_overview = selected_job['course_overview'],
                description = selected_job['description'],
                note = selected_job['note'],
                is_active = selected_job['is_active']
            )
            jobs.append(created_job)

            job_instructors[course.id] = selected_job['instructors']

        created_jobs = Job.objects.bulk_create(jobs)

        # Add instructors
        for course_id, instructors in job_instructors.items():
            instructors = [ userApi.get_user(iid) for iid in instructors ]

            job = adminApi.get_job_by_session_id_and_course_id(session.id, course_id)
            job.instructors.add( *list(instructors) )

        # Remove session form data
        del request.session['session_form_data']

        messages.success(request, 'Success! {0} {1} - {2} created'.format(session.year, session.term.code, session.title))

        if data['is_archived']:
            return redirect('administrators:archived_sessions')
        return redirect('administrators:current_sessions')



@method_decorator([never_cache], name='dispatch')
class ShowReportApplicants(LoginRequiredMixin, View):
    ''' Display a session report including all applicants and their accepted information '''

    def setup(self, request, *args, **kwargs):
        setup = super().setup(request, *args, **kwargs)
        session_slug = kwargs.get('session_slug', None)
        if not session_slug:
            raise Http404

        self.session_slug = session_slug
        return setup

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        request = userApi.has_admin_access(request)
        session = adminApi.get_session(self.session_slug, 'slug')

        applicants = adminApi.get_applicants_in_session(session)
        total_applicants = applicants.count()

        if bool( request.GET.get('first_name') ):
            applicants = applicants.filter(first_name__icontains=request.GET.get('first_name'))
        if bool( request.GET.get('last_name') ):
            applicants = applicants.filter(last_name__icontains=request.GET.get('last_name'))
        if bool( request.GET.get('cwl') ):
            applicants = applicants.filter(username__icontains=request.GET.get('cwl'))
        if bool( request.GET.get('student_number') ):
            applicants = applicants.filter(profile__student_number__icontains=request.GET.get('student_number'))

        page = request.GET.get('page', 1)
        paginator = Paginator(applicants, utils.TABLE_PAGE_SIZE)

        try:
            applicants = paginator.page(page)
        except PageNotAnInteger:
            applicants = paginator.page(1)
        except EmptyPage:
            applicants = paginator.page(paginator.num_pages)

        for applicant in applicants:
            applicant.gta = userApi.get_gta_flag(applicant)
            
            applicant.has_applied = False
            apps = applicant.application_set.filter( Q(job__session__year=session.year) & Q(job__session__term__code=session.term.code) )

            if apps.count() > 0:
                applicant.has_applied = True
                accepted_apps = []
                for app in apps:
                    app = adminApi.add_app_info_into_application(app, ['accepted', 'declined'])
                    if adminApi.check_valid_accepted_app_or_not(app):
                        accepted_apps.append(app)
                applicant.accepted_apps = accepted_apps

        back_to_word = 'Current Sessions'
        if 'archived' in request.session.get('next_session', None):
            back_to_word = 'Archived Sessions'

        return render(request, 'administrators/sessions/show_report_applicants.html', {
            'loggedin_user': request.user,
            'session': session,
            'total_applicants': total_applicants,
            'applicants': applicants,
            'next_session': request.session.get('next_session', None),
            'back_to_word': back_to_word
        })


@method_decorator([never_cache], name='dispatch')
class ShowReportSummary(LoginRequiredMixin, View):
    ''' Display a session summary '''

    def setup(self, request, *args, **kwargs):
        setup = super().setup(request, *args, **kwargs)
        session_slug = kwargs['session_slug']
        if not session_slug:
            raise Http404
        
        request = userApi.has_admin_access(request)
        
        session = adminApi.get_session(session_slug, 'slug')
        self.session = session
        return setup

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        jobs = []

        total_lfs_grad = set()
        total_lfs_grad_ta_hours = 0.0
        total_others = set()
        total_others_ta_hours = 0.0
        for job in self.session.job_set.all():
            apps = adminApi.get_accepted_apps_not_terminated(job.application_set.all())
            apps = adminApi.get_filtered_accepted_apps(apps)

            lfs_grad = set()
            lfs_grad_ta_hours = 0.0
            others = set()
            others_ta_hours = 0.0
            if len(apps) > 0:
                for app in apps:
                    app.accepted = adminApi.get_accepted(app)
                    app.salary = adminApi.calculate_salary(app)
                    if userApi.get_lfs_grad_or_others(app.applicant) == 'LFS GRAD':
                        lfs_grad.add(app.applicant.id)
                        lfs_grad_ta_hours += app.accepted.assigned_hours

                        total_lfs_grad.add(app.applicant.id)
                        total_lfs_grad_ta_hours += app.accepted.assigned_hours
                    else:
                        others.add(app.applicant.id)
                        others_ta_hours += app.accepted.assigned_hours

                        total_others.add(app.applicant.id)
                        total_others_ta_hours += app.accepted.assigned_hours

                job.accepted_apps = apps

            job.stat = {
                'lfs_grad': len(lfs_grad),
                'lfs_grad_ta_hours': lfs_grad_ta_hours,
                'others': len(others),
                'others_ta_hours': others_ta_hours
            }
            jobs.append(job)

        back_to_word = 'Current Sessions'
        if 'archived' in request.session.get('next_session', None):
            back_to_word = 'Archived Sessions'

        return render(request, 'administrators/sessions/show_report_summary.html', {
            'loggedin_user': request.user,
            'session': self.session,
            'jobs': jobs,
            'ta_hours_stat': {
                'total_lfs_grad': len(total_lfs_grad),
                'total_lfs_grad_ta_hours': total_lfs_grad_ta_hours,
                'total_others': len(total_others),
                'total_others_ta_hours': total_others_ta_hours
            },
            'next_session': request.session.get('next_session', None),
            'back_to_word': back_to_word
        })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_session(request, session_slug):
    ''' Edit a session '''
    request = userApi.has_admin_access(request)
    adminApi.can_req_parameters_access(request, 'session', ['next', 'p'])

    session = adminApi.get_session(session_slug, 'slug')
    if request.method == 'POST':

        # Check whether a next url is valid or not
        adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

        form = SessionConfirmationForm(request.POST, instance=session)
        if form.is_valid():
            data = form.cleaned_data
            courses = data['courses']

            if len(courses) == 0:
                messages.error(request, 'An error occurred. Please select courses in this session.')
                return HttpResponseRedirect(request.get_full_path())

            updated_session = form.save(commit=False)
            updated_session.updated_at = datetime.now()

            if data['is_archived']:
                updated_session.is_visible = False

            updated_session.save()

            if updated_session:
                updated_jobs = adminApi.update_session_jobs(session, courses)
                if updated_jobs:
                    messages.success(request, 'Success! {0} {1} {2} updated'.format(session.year, session.term.code, session.title))
                    return HttpResponseRedirect(request.POST.get('next'))
                else:
                    messages.error(request, 'An error occurred while updating courses in a session.')
            else:
                messages.error(request, 'An error occurred while updating a session.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect(request.get_full_path())

    return render(request, 'administrators/sessions/edit_session.html', {
        'loggedin_user': request.user,
        'session': session,
        'form': SessionConfirmationForm(data=None, instance=session, initial={
            'courses': [ job.course for job in session.job_set.all() ],
            'term': session.term
        }),
        'next': adminApi.get_next(request)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def delete_session_confirmation(request, session_slug):
    ''' Confirmation to delete a Session '''
    request = userApi.has_admin_access(request)
    adminApi.can_req_parameters_access(request, 'session', ['next', 'p'])

    sessions = adminApi.get_sessions()
    if request.method == 'POST':
        adminApi.can_req_parameters_access(request, 'session', ['next'], 'POST')

        session_id = request.POST.get('session')
        deleted_session = adminApi.delete_session(session_id)
        if deleted_session:
            messages.success(request, 'Success! {0} {1} {2} deleted'.format(deleted_session.year, deleted_session.term.code, deleted_session.title))
            return HttpResponseRedirect(request.POST.get('next'))
        else:
            messages.error(request, 'An error occurred. Failed to delete {0} {1} {2}'.format(deleted_session.year, deleted_session.term.code, deleted_session.title))
        return HttpResponseRedirect(request.get_full_path())

    return render(request, 'administrators/sessions/delete_session_confirmation.html', {
        'loggedin_user': request.user,
        'current_sessions': sessions.filter(is_archived=False),
        'archived_sessions': sessions.filter(is_archived=True),
        'session': adminApi.get_session(session_slug, 'slug'),
        'next': adminApi.get_next(request)
    })


# Jobs


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_job(request, session_slug, job_slug):
    ''' Display job details '''
    request = userApi.has_admin_access(request, Role.HR)
    adminApi.can_req_parameters_access(request, 'job-app', ['next', 'p'])

    return render(request, 'administrators/jobs/show_job.html', {
        'loggedin_user': request.user,
        'job': adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug),
        'next': adminApi.get_next(request)
    })


@method_decorator([never_cache], name='dispatch')
class PrepareJobs(LoginRequiredMixin, View):
    ''' Display preparing jobs '''

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        request = userApi.has_admin_access(request)

        year_q = request.GET.get('year')
        term_q = request.GET.get('term')
        code_q = request.GET.get('code')
        number_q = request.GET.get('number')
        section_q = request.GET.get('section')
        instructor_first_name_q = request.GET.get('instructor_first_name')
        instructor_last_name_q = request.GET.get('instructor_last_name')

        job_list = adminApi.get_jobs()
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
        if bool(instructor_first_name_q):
            job_list = job_list.filter(instructors__first_name__icontains=instructor_first_name_q)
        if bool(instructor_last_name_q):
            job_list = job_list.filter(instructors__last_name__icontains=instructor_last_name_q)

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
        is_valid = valid_worktag_setting(request)
        if is_valid:
            jid, aid, program_info, worktag = get_worktag(request)
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

        year_q = request.GET.get('year')
        term_q = request.GET.get('term')
        code_q = request.GET.get('code')
        number_q = request.GET.get('number')
        section_q = request.GET.get('section')

        job_list = adminApi.get_jobs()
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
            'new_next': adminApi.build_new_next(request)
        })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def show_job_applications(request, session_slug, job_slug):
    ''' Display a job's applications '''
    request = userApi.has_admin_access(request)

    job = adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)

    apps = []
    for app in job.application_set.all():
        app.selected = None
        selected = app.applicationstatus_set.filter(assigned=ApplicationStatus.SELECTED)
        if selected.exists():
            app.selected = selected.last()

        app.applicant = userApi.add_resume(app.applicant)
        app.applicant.accepted_apps = adminApi.get_accepted_apps_in_applicant(app)
        app.applicant.preferred_ta = userApi.get_preferred_ta(app.applicant)
        app.info = userApi.get_applicant_status_program(app.applicant)

        apps.append(app)

    request.session['summary_applicants_next'] = request.get_full_path()

    return render(request, 'administrators/jobs/show_job_applications.html', {
        'loggedin_user': request.user,
        'job': adminApi.add_job_with_applications_statistics(job),
        'apps': apps,
        'app_status': APP_STATUS,
        'next': request.session.get('progress_jobs_next'),
        'new_next': adminApi.build_new_next(request)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def summary_applicants(request, session_slug, job_slug):
    ''' Display the summary of applicants in each session term '''

    request = userApi.has_admin_access(request)

    session, job, total_applicants, no_offers_applicants, applicants, searched_total_applicants = adminApi.get_summary_applicants(request, session_slug, job_slug)

    return render(request, 'administrators/jobs/summary_applicants.html', {
        'loggedin_user': request.user,
        'session': session,
        'job': job,
        'total_applicants': total_applicants,
        'total_no_offers_applicants': len(no_offers_applicants),
        'applicants': applicants,
        'searched_total_applicants': searched_total_applicants,
        'next': request.session.get('summary_applicants_next')
    })


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

        user_list = user_list.filter(profile__roles__name=Role.STUDENT)

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
            'app_status': APP_STATUS,
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


# Applications


@method_decorator([never_cache], name='dispatch')
class ShowApplication(LoginRequiredMixin, View):
    ''' Display an application details '''

    def setup(self, request, *args, **kwargs):
        setup = super().setup(request, *args, **kwargs)
        app_slug = kwargs.get('app_slug', None)
        if not app_slug:
            raise Http404
        self.app_slug = app_slug
        return setup

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        request = userApi.has_admin_access(request, Role.HR)
        adminApi.can_req_parameters_access(request, 'app', ['next', 'p'])

        return render(request, 'administrators/applications/show_application.html', {
            'loggedin_user': request.user,
            'app': adminApi.get_application(self.app_slug, 'slug'),
            'next': adminApi.get_next(request)
        })


@method_decorator([never_cache], name='dispatch')
class ApplicationsDashboard(LoginRequiredMixin, View):
    ''' Display a dashboard to take a look at updates '''

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        request = userApi.has_admin_access(request)

        year_q = request.GET.get('year')
        term_q = request.GET.get('term')
        code_q = request.GET.get('code')
        number_q = request.GET.get('number')
        section_q = request.GET.get('section')
        first_name_q = request.GET.get('first_name')
        last_name_q = request.GET.get('last_name')

        status_list = adminApi.get_application_statuses()
        if bool(year_q):
            status_list = status_list.filter(application__job__session__year__icontains=year_q)
        if bool(term_q):
            status_list = status_list.filter(application__job__session__term__code__icontains=term_q)
        if bool(code_q):
            status_list = status_list.filter(application__job__course__code__name__icontains=code_q)
        if bool(number_q):
            status_list = status_list.filter(application__job__course__number__name__icontains=number_q)
        if bool(section_q):
            status_list = status_list.filter(application__job__course__section__name__icontains=section_q)
        if bool(first_name_q):
            status_list = status_list.filter(application__applicant__first_name__icontains=first_name_q)
        if bool(last_name_q):
            status_list = status_list.filter(application__applicant__last_name__icontains=last_name_q)

        page = request.GET.get('page', 1)
        paginator = Paginator(status_list, utils.TABLE_PAGE_SIZE)

        try:
            statuses = paginator.page(page)
        except PageNotAnInteger:
            statuses = paginator.page(1)
        except EmptyPage:
            statuses = paginator.page(paginator.num_pages)

        return render(request, 'administrators/applications/applications_dashboard.html', {
            'loggedin_user': request.user,
            'statuses': statuses,
            'total_statuses': len(status_list),
            'app_status': APP_STATUS,
            'new_next': adminApi.build_new_next(request)
        })


@method_decorator([never_cache], name='dispatch')
class AllApplications(LoginRequiredMixin, View):
    ''' Display all applications '''

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        request = userApi.has_admin_access(request)

        app_list, info = adminApi.get_applications_filter_limit(request, 'all')

        page = request.GET.get('page', 1)
        paginator = Paginator(app_list, utils.TABLE_PAGE_SIZE)

        try:
            apps = paginator.page(page)
        except PageNotAnInteger:
            apps = paginator.page(1)
        except EmptyPage:
            apps = paginator.page(paginator.num_pages)

        for app in apps:
            app.applicant.gta = userApi.get_gta_flag(app.applicant)
            app.applicant.preferred_ta = userApi.get_preferred_ta(app.applicant)
            app.can_reset = adminApi.app_can_reset(app)
            app.confi_info_expiry_status = userApi.get_confidential_info_expiry_status(app.applicant)

        return render(request, 'administrators/applications/all_applications.html', {
            'loggedin_user': request.user,
            'apps': apps,
            'num_filtered_apps': info['num_filtered_apps'],
            'app_status': APP_STATUS,
            'new_next': adminApi.build_new_next(request),
            'this_year': utils.THIS_YEAR
        })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def reset_application(request):
    ''' Reset an application '''
    request = userApi.has_admin_access(request)

    # Check whether a next url is valid or not
    adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

    app_id = request.POST.get('application')
    app = adminApi.get_application(app_id)

    # An offered appliation cannot be reset
    if adminApi.app_can_reset(app) == False:
       messages.error(request, 'An error occurred. Selected or Declined applications can be reset.')
       return HttpResponseRedirect(request.POST.get('next'))

    instructor_preference = '0'

    reset_app_form = InstructorApplicationForm({ 'instructor_preference': instructor_preference })
    if reset_app_form.is_valid():
        app_status_form = ApplicationStatusForm({ 'application': app_id, 'assigned': ApplicationStatus.NONE, 'assigned_hours': '0', 'has_contract_read': False })
        if app_status_form:
            updated_app = adminApi.update_reset_application(app_id, instructor_preference)
            if updated_app:
                if app_status_form.save():
                    app_reset = ApplicationReset.objects.create(application=app, user=request.user.get_full_name())
                    if app_reset:
                        messages.success(request, 'Success! {0} - the following information (ID: {1}, {2} {3} - {4} {5} {6}) have been reset. <ul><li>Instructor Preference</li><li>Assigned Status</li><li>Assigned Hours</li></ul>'.format(updated_app.applicant.get_full_name(), updated_app.id, updated_app.job.session.year, updated_app.job.session.term.code, updated_app.job.course.code.name, updated_app.job.course.number.name, updated_app.job.course.section.name))
                    else:
                        messages.error(request, 'An error occurred while updating an application reset log.')
                else:
                    messages.error(request, 'An error occurred while updating an application status.')
            else:
                messages.error(request, 'An error occurred while updating an instructor_preference.')
        else:
            errors = app_status_form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))
    else:
        errors = reset_app_form.errors.get_json_data()
        messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return HttpResponseRedirect(request.POST.get('next'))


@method_decorator([never_cache], name='dispatch')
class SelectedApplications(LoginRequiredMixin, View):
    
    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        request = userApi.has_admin_access(request)

        app_list, info = adminApi.get_applications_filter_limit(request, 'selected')

        page = request.GET.get('page', 1)
        paginator = Paginator(app_list, utils.TABLE_PAGE_SIZE)

        try:
            apps = paginator.page(page)
        except PageNotAnInteger:
            apps = paginator.page(1)
        except EmptyPage:
            apps = paginator.page(paginator.num_pages)

        apps = adminApi.add_app_info_into_applications(apps, ['resume', 'selected', 'offered', 'declined'])

        filtered_offered_apps = { 'num_offered': 0, 'num_not_offered': 0 }
        for app in apps:
            app.applicant.gta = userApi.get_gta_flag(app.applicant)
            app.applicant.preferred_ta = userApi.get_preferred_ta(app.applicant)
            app.confi_info_expiry_status = userApi.get_confidential_info_expiry_status(app.applicant)

            assigned_hours = app.selected.assigned_hours
            if app.offered and app.offered.id > app.selected.id:
                assigned_hours = app.offered.assigned_hours

            offer_modal = {
                'title': '',
                'form_url': reverse('administrators:offer_job', args=[app.job.session.slug, app.job.course.slug]),
                'classification_id': app.classification.id if app.classification != None else -1,
                'assigned_hours': assigned_hours,
                'button_colour': 'btn-primary',
                'button_disabled': False,
                'button_disabled_message': False
            }

            latest_status = adminApi.get_latest_status_in_app(app)
            num_offers = app.applicationstatus_set.filter(assigned=ApplicationStatus.OFFERED).count()

            if latest_status == 'selected' or latest_status == 'none':
                if num_offers == 0: 
                    offer_modal['title'] = 'Offer'
                else: 
                    offer_modal['title'] = 'Re-offer'

                filtered_offered_apps['num_not_offered'] += 1

                if latest_status == 'none':
                    offer_modal['button_disabled'] = True
                    offer_modal['button_disabled_message'] = True

                    filtered_offered_apps['num_not_offered'] -= 1
                    filtered_offered_apps['num_offered'] += 1
            else:
                offer_modal['title'] = 'Edit'
                offer_modal['button_colour'] = 'btn-warning'
                filtered_offered_apps['num_offered'] += 1

            app.offer_modal = offer_modal

            if app.job.assigned_ta_hours == app.job.accumulated_ta_hours:
                app.ta_hour_progress = 'done'
            elif app.job.assigned_ta_hours < app.job.accumulated_ta_hours:
                app.ta_hour_progress = 'over'
            else:
                if (app.job.assigned_ta_hours * 3.0/4.0) < app.job.accumulated_ta_hours:
                    app.ta_hour_progress = 'under_three_quarters'
                elif (app.job.assigned_ta_hours * 2.0/4.0) < app.job.accumulated_ta_hours:
                    app.ta_hour_progress = 'under_half'
                elif (app.job.assigned_ta_hours * 1.0/4.0) < app.job.accumulated_ta_hours:
                    app.ta_hour_progress = 'under_one_quarter'

        return render(request, 'administrators/applications/selected_applications.html', {
            'loggedin_user': request.user,
            'apps': apps,
            'num_all_apps': info['num_all_apps'],
            'filtered_apps_stats': {
                'num_filtered_apps': info['num_filtered_apps'],
                'filtered_offered_apps': filtered_offered_apps,
            },
            'all_offered_apps_stats': {
                'num_offered': info['num_offered_apps'],
                'num_not_offered': info['num_not_offered_apps']
            },
            'classification_choices': adminApi.get_classifications(),
            'app_status': APP_STATUS,
            'new_next': adminApi.build_new_next(request),
            'this_year': utils.THIS_YEAR,
            'worktags': settings.WORKTAGS,
            'save_worktag_setting_url': request.get_full_path(),
            'delete_worktag_setting_url': reverse('administrators:delete_app_worktag_setting')
        })

    @method_decorator(require_POST)
    def post(self, request, *args, **kwargs):
        is_valid = valid_worktag_setting(request)
        if is_valid:
            jid, aid, program_info, worktag = get_worktag(request)
            app = adminApi.get_application(aid)        
            success = False

            # Worktag Setting
            ws_filtered = WorktagSetting.objects.filter(application_id=app.id)
            if ws_filtered.exists():
                ws = ws_filtered.first()
                update_fields = []
                if adminApi.compare_two_dicts_by_key(ws.program_info, program_info):
                    messages.warning(request, 'Warning! Nothing has been updated for the Worktag Setting (Application ID: {0})'.format(app.id))
                else:
                    ws.program_info = program_info
                    update_fields.append('program_info')
                
                if ws.worktag != worktag:
                    ws.worktag = worktag
                    update_fields.append('worktag')
                
                if len(update_fields) > 0:
                    ws.save(update_fields=update_fields)
                    success = True
                    messages.success(request, 'Success! Updated the Worktag Setting (Application ID: {0})'.format(app.id))
            else:
                ws = WorktagSetting.objects.create(application_id=aid, job_id=app.job.id, program_info=program_info, worktag=worktag)
                if ws:
                    success = True
                    messages.success(request, 'Success! Saved the Worktag Setting (Application ID: {0})'.format(app.id))
                else:
                    messages.error(request, 'An error occurred. Failed to create a new Worktag Setting for some reason. Please try again.')

            if success:
                adminApi.update_worktag_in_admin_docs(app, worktag, request.POST['processing_note'])
        else:
            messages.error(request, 'An error occurred. Your input values are not valid. Please try again.')
        
        return HttpResponseRedirect(request.POST.get('next'))
    

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def offer_job(request, session_slug, job_slug):
    ''' Admin can offer a job to each job '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':

        # Check whether a next url is valid or not
        adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

        app = adminApi.get_application(request.POST.get('application'))
        latest_status = adminApi.get_latest_status_in_app(app)
        if latest_status == 'none':
            messages.error(request, 'An error occurred. An applied application cannot be offered.')
            return HttpResponseRedirect(request.POST.get('next'))

        if 'classification' not in request.POST.keys() or len(request.POST.get('classification')) == 0:
            messages.error(request, 'An error occurred. Please select classification, then try again.')
            return HttpResponseRedirect(request.POST.get('next'))

        assigned_hours = request.POST.get('assigned_hours')

        if adminApi.is_valid_float(assigned_hours) == False:
            messages.error(request, 'An error occurred. Please check assigned hours. Assigned hours must be numerival value only.')
            return HttpResponseRedirect(request.POST.get('next'))

        if adminApi.is_valid_integer(assigned_hours) == False:
            messages.error(request, 'An error occurred. Please check assigned hours. Assign TA Hours must be non-negative integers.')
            return HttpResponseRedirect(request.POST.get('next'))

        assigned_hours = int( float(assigned_hours) )

        if assigned_hours < 0:
            messages.error(request, 'An error occurred. Please check assigned hours. Assigned hours must be greater than 0.')
            return HttpResponseRedirect(request.POST.get('next'))

        job = adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)
        if assigned_hours > int(job.assigned_ta_hours):
            messages.error(request, 'An error occurred. Please you cannot assign {0} hours Total Assigned TA Hours is {1}, then try again.'.format( assigned_hours, int(job.assigned_ta_hours) ))
            return HttpResponseRedirect(request.POST.get('next'))

        errors = []
        offer_type = request.POST.get('offer_type')
        admin_app_form = AdminApplicationForm(request.POST)
        if offer_type == 'edit':
            ApplicationStatus.objects.filter(id=request.POST.get('applicationstatus')).update(assigned_hours=assigned_hours)

        elif offer_type == 'offer':
            app_status_form = ApplicationStatusForm(request.POST)
            if app_status_form.is_valid():
                app_status_form.save()
            else:
                app_status_errors = app_status_form.errors.get_json_data()
                if app_status_errors:
                    errors.append( userApi.get_error_messages(app_status_errors) )

        if admin_app_form.is_valid():
            Application.objects.filter(id=app.id).update(
                classification = request.POST.get('classification'),
                note = request.POST.get('note'),
                updated_at = datetime.now()
            )

            if len(errors) > 0:
                messages.error(request, 'An error occurred while sending a job offer. {0}'.format( ' '.join(errors) ))
                return HttpResponseRedirect(request.POST.get('next'))

            applicant = userApi.get_user(request.POST.get('applicant'))

            if offer_type == 'edit':
                messages.success(request, 'Success! Updated this application (ID: {0})'.format(app.id))
            elif offer_type == 'offer':
                messages.success(request, 'Success! You offered this user ({0} {1}) {2} hours for this job ({3} {4} - {5} {6} {7})'.format(applicant.first_name, applicant.last_name, assigned_hours, job.session.year, job.session.term.code, job.course.code.name, job.course.number.name, job.course.section.name))
        else:
            admin_app_errors = admin_app_form.errors.get_json_data()
            if admin_app_errors:
                errors.append( userApi.get_error_messages(admin_app_errors) )

        if len(errors) > 0:
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format(' '.join(errors)))

    return HttpResponseRedirect(request.POST.get('next'))


@method_decorator([never_cache], name='dispatch')
class OfferedApplications(LoginRequiredMixin, View):
    ''' Display applications offered by admins '''

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        request = userApi.has_admin_access(request)

        app_list, info = adminApi.get_applications_filter_limit(request, 'offered')

        page = request.GET.get('page', 1)
        paginator = Paginator(app_list, utils.TABLE_PAGE_SIZE)

        try:
            apps = paginator.page(page)
        except PageNotAnInteger:
            apps = paginator.page(1)
        except EmptyPage:
            apps = paginator.page(paginator.num_pages)

        apps = adminApi.add_app_info_into_applications(apps, ['offered', 'accepted', 'declined'])
        for app in apps:
            app.applicant.gta = userApi.get_gta_flag(app.applicant)
            app.applicant.preferred_ta = userApi.get_preferred_ta(app.applicant)
            app.confi_info_expiry_status = userApi.get_confidential_info_expiry_status(app.applicant)

        return render(request, 'administrators/applications/offered_applications.html', {
            'loggedin_user': request.user,
            'apps': apps,
            'num_filtered_apps': info['num_filtered_apps'],
            'admin_emails': adminApi.get_admin_emails(),
            'new_next': adminApi.build_new_next(request),
            'this_year': utils.THIS_YEAR
        })


@method_decorator([never_cache], name='dispatch')
class AcceptedApplications(LoginRequiredMixin, View):

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        request = userApi.has_admin_access(request, Role.HR)

        app_list, info = adminApi.get_applications_filter_limit(request, 'accepted')

        page = request.GET.get('page', 1)
        paginator = Paginator(app_list, utils.TABLE_PAGE_SIZE)

        try:
            apps = paginator.page(page)
        except PageNotAnInteger:
            apps = paginator.page(1)
        except EmptyPage:
            apps = paginator.page(paginator.num_pages)

        apps = adminApi.add_app_info_into_applications(apps, ['accepted', 'declined'])

        for app in apps:
            app.salary = adminApi.calculate_salary(app)
            app.pt_percentage = adminApi.calculate_pt_percentage(app)

        return render(request, 'administrators/applications/accepted_applications.html', {
            'apps': apps,
            'processed_stats': adminApi.get_processed_stats(apps),
            'num_filtered_apps': info['num_filtered_apps'],
            'new_next': adminApi.build_new_next(request),
            'today_accepted_apps': info['today_accepted_apps'],
            'today_processed_stats': adminApi.get_processed_stats(info['today_accepted_apps']),
            'today': info['today'],
            'download_all_accepted_apps_url': reverse('administrators:download_all_accepted_apps'),
            'worktag_options': settings.WORKTAG_MAP
        })


@require_http_methods(['POST'])
def update_admin_docs(request):
    ''' Get admin docs request '''

    if request.method == 'POST':
        admin_docs = adminApi.get_admin_docs(request.POST.get('application'))
        form = AdminDocumentsForm(request.POST, instance=admin_docs)
        if form.is_valid():
            saved_admin_docs = form.save()
            if saved_admin_docs:
                if adminApi.add_admin_docs_user(saved_admin_docs, request.user):
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Success! Admin Documents of {0} updated (Application ID: {1}).'.format( saved_admin_docs.application.applicant.get_full_name(), saved_admin_docs.application.id )
                    })
                else:
                    return JsonResponse({ 'status': 'error', 'message': 'An error occurred while saving admin docs user.' }, status=400)
            else:
                return JsonResponse({ 'status': 'error', 'message': 'An error occurred while saving admin docs.' }, status=400)
        else:
            errors = form.errors.get_json_data()
            return JsonResponse({ 'status': 'error', 'message': 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ) }, status=400)

    return JsonResponse({ 'status': 'error', 'message': 'Request method is not POST.' }, status=400)


@require_http_methods(['POST'])
def import_accepted_apps(request):
    ''' Import accepted applications '''
    if request.method == 'POST':
        file = request.FILES.get('file')
        file_split = os.path.splitext(file.name)

        # only csv is allowed to update
        if 'csv' not in file_split[1].lower():
            messages.error(request, 'An error occurred. Only CSV files are allowed to update. Please check your file.')
            return HttpResponseRedirect(request.POST.get('next'))

        data = StringIO(file.read().decode())
        result, msg = adminApi.bulk_update_admin_docs(data, request.user)

        if result:
            if len(msg) > 0:
                messages.success( request, 'Success! Updated the following fields in Admin Docs through CSV. {0}'.format(msg) )
            else:
                messages.warning(request, 'Warning! No data was updated in the database. Please check your data inputs.')
        else:
            messages.error(request, msg)

    return HttpResponseRedirect(request.POST.get('next'))


@method_decorator([never_cache], name='dispatch')
class AcceptedAppsReportWorkday(LoginRequiredMixin, View):

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        request = userApi.has_admin_access(request, Role.HR)

        app_list, total_apps = adminApi.get_accepted_app_report(request)

        page = request.GET.get('page', 1)
        paginator = Paginator(app_list, utils.TABLE_PAGE_SIZE)

        try:
            apps = paginator.page(page)
        except PageNotAnInteger:
            apps = paginator.page(1)
        except EmptyPage:
            apps = paginator.page(paginator.num_pages)

        for app in apps:
            app = adminApi.make_workday_data(app)

        return render(request, 'administrators/applications/accepted_apps_report_workday.html', {
            'total_apps': total_apps,
            'apps': apps,
            'download_accepted_apps_workday_url': reverse('administrators:download_accepted_apps_workday'),
            'workday_costing_alloc_level': settings.WORKDAY_COSTING_ALLOCATION_LEVEL,
            'workday_mcml_location': settings.WORKDAY_MCML_LOCATION,
            'workday_fnh_location': settings.WORKDAY_FNH_LOCATION,
        })


@require_http_methods(['GET'])
@require_http_methods(['GET'])
def download_accepted_apps_workday(request):
    ''' Download accepted applications for Workday '''

    apps, total_apps = adminApi.get_accepted_app_report(request)
    data = []
    for app in apps:
        app = adminApi.make_workday_data(app)
        data.append({
            'Fields': '',
            'Bot Action': '',
            'Primary Initiator': '',
            'Secondary Initiator': '',
            'Three Jobs Rule (Bypass/Leave Blank)': '',
            'Bot Status': '',
            'Bot Timestamp': '',
            'Bot Comments': '',
            'Student ID': app.student_number,
            'Hire Date': app.start_date1,
            'Hire Reason': '',
            'Position Number': app.position_number,
            'Time Type': app.time_type,
            'Job Title': app.job_title,
            'Default Weekly Hours': app.default_weekly_hours,
            'Scheduled Weekly Hours': app.scheduled_weekly_hours,
            'Additional Job Classifications': app.job_class,
            'End Employment Date': app.end_date1,
            'Comments': '',
            'Attachment 1': '',
            'Attachment 1 Category': '',
            'SIN Number': '',
            'Expiration Date of SIN': app.sin_expiry_date,
            'Visa ID Type': app.visa_type,
            'Identification #': '',
            'Issued Date of Visa': '',
            'Expiration Date of Visa': app.study_permit_expiry_date,
            'Permit Validated': app.permit_validated,
            'Attachment (NHI)': '',
            'Description of Upload (NHI)': '',
            'Location': app.location,
            'Vacating Position': '',
            'Cost Centre': '',
            'Functional Unit Hierarchy': '',
            'Amount (Monthly)': app.monthly_salary,
            'Amount (Hourly)': '',
            'Comments for Costing allocation': '',
            'Costing Allocation Level': app.costing_alloc_level,
            'Start Date1': app.start_date1,
            'End Date1': app.end_date1,
            'Worktag1': app.worktag1,
            'Distribution Percent1': app.dist_per1,
            'Start Date2': app.start_date2,
            'End Date2': app.end_date2,
            'Worktag2': app.worktag2,
            'Distribution Percent2': app.dist_per2,
            'Start Date3': app.start_date3,
            'End Date3': app.end_date3,
            'Worktag3': app.worktag3,
            'Distribution Percent3': app.dist_per3,
            'Start Date4': app.start_date4,
            'End Date4': app.end_date4,
            'Worktag4': app.worktag4,
            'Distribution Percent4': app.dist_per4
        })
    
    return JsonResponse({ 'status': 'success', 'data': data })
    


@method_decorator([never_cache], name='dispatch')
class DeclinedApplications(LoginRequiredMixin, View):
    ''' Display applications declined by students '''

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        request = userApi.has_admin_access(request)

        app_list, info = adminApi.get_applications_filter_limit(request, 'declined')

        page = request.GET.get('page', 1)
        paginator = Paginator(app_list, utils.TABLE_PAGE_SIZE)

        try:
            apps = paginator.page(page)
        except PageNotAnInteger:
            apps = paginator.page(1)
        except EmptyPage:
            apps = paginator.page(paginator.num_pages)

        apps = adminApi.add_app_info_into_applications(apps, ['declined'])

        return render(request, 'administrators/applications/declined_applications.html', {
            'loggedin_user': request.user,
            'apps': apps,
            'num_filtered_apps': info['num_filtered_apps'],
            'admin_emails': adminApi.get_admin_emails(),
            'app_status': APP_STATUS,
            'new_next': adminApi.build_new_next(request)
        })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def email_history(request):
    ''' Display all of email sent by admins to let them know job offers '''
    request = userApi.has_admin_access(request)

    receiver_q = request.GET.get('receiver')
    title_q = request.GET.get('title')
    message_q = request.GET.get('message')
    type_q = request.GET.get('type')
    no_response_q = request.GET.get('no_response')

    email_list = adminApi.get_emails()
    if bool(receiver_q):
        email_list = email_list.filter(receiver__icontains=receiver_q)
    if bool(title_q):
        email_list = email_list.filter(title__icontains=title_q)
    if bool(message_q):
        email_list = email_list.filter(message__icontains=message_q)
    if bool(type_q):
        email_list = email_list.filter(type__icontains=type_q)
    if bool(no_response_q):
        email_list = email_list.filter(application__applicationstatus__assigned=ApplicationStatus.OFFERED).filter( ~Q(application__applicationstatus__assigned=ApplicationStatus.ACCEPTED) & ~Q(application__applicationstatus__assigned=ApplicationStatus.DECLINED) ).order_by('-id').distinct()

    page = request.GET.get('page', 1)
    paginator = Paginator(email_list, utils.TABLE_PAGE_SIZE)

    try:
        emails = paginator.page(page)
    except PageNotAnInteger:
        emails = paginator.page(1)
    except EmptyPage:
        emails = paginator.page(paginator.num_pages)

    for email in emails:
        email.application = adminApi.add_app_info_into_application(email.application, ['offered', 'accepted', 'declined'])

    return render(request, 'administrators/applications/email_history.html', {
        'loggedin_user': request.user,
        'emails': emails,
        'total': len(email_list),
        'new_next': adminApi.build_new_next(request)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def send_reminder(request, email_id):
    ''' Send a reminder email '''
    request = userApi.has_admin_access(request)
    adminApi.can_req_parameters_access(request, 'app', ['next', 'p'])

    email = None
    if request.method == 'POST':

        # Check whether a next url is valid or not
        adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

        form = ReminderForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            sent_email = adminApi.send_and_create_email(data['application'], data['sender'], data['receiver'], data['title'], data['message'], data['type'])
            if sent_email:
                messages.success(request, 'Success! Email has sent to {0}'.format(data['receiver']))
                return HttpResponseRedirect(request.POST.get('next'))
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect(request.get_full_path())

    else:
        email = adminApi.get_email(email_id)

    return render(request, 'administrators/applications/send_reminder.html', {
        'loggedin_user': request.user,
        'email': email,
        'form': ReminderForm(data=None, instance=email, initial={
            'title': 'REMINDER: ' + email.title
        }),
        'next': adminApi.get_next(request)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def decline_reassign(request):
    ''' Decline and reassign a job offer with new assigned hours '''
    request = userApi.has_admin_access(request)
    adminApi.can_req_parameters_access(request, 'none', ['next'])
    next = adminApi.get_next(request)
    if request.method == 'POST':
        app = adminApi.get_application( request.POST.get('application') )

        old_assigned_hours = request.POST.get('old_assigned_hours')
        new_assigned_hours = request.POST.get('new_assigned_hours')

        if adminApi.is_valid_float(old_assigned_hours) == False:
            messages.error(request, 'An error occurred. Please contact administrators. Your old assigned hours must be numerival value only.')
            return HttpResponseRedirect(next)

        if adminApi.is_valid_integer(old_assigned_hours) == False:
            messages.error(request, 'An error occurred. Please check assigned hours. Assign TA Hours must be non-negative integers.')
            return HttpResponseRedirect(next)

        if adminApi.is_valid_float(new_assigned_hours) == False:
            messages.error(request, 'An error occurred. Please check assigned hours. Your new assigned hours must be numerival value only.')
            return HttpResponseRedirect(next)

        if adminApi.is_valid_integer(new_assigned_hours) == False:
            messages.error(request, 'An error occurred. Please check assigned hours. Assign TA Hours must be non-negative integers.')
            return HttpResponseRedirect(next)

        old_assigned_hours = int( float(old_assigned_hours) )
        new_assigned_hours = int( float(new_assigned_hours) )

        if new_assigned_hours < 0:
            messages.error(request, 'An error occurred. Please check assigned hours. Your new assigned hours must be greater than 0.')
            return HttpResponseRedirect(next)

        if new_assigned_hours == 0 or new_assigned_hours > int(app.job.assigned_ta_hours):
            messages.error(request, 'An error occurred. Please check assigned hours. Valid assigned hours are between 0 and {0}'.format( int(app.job.assigned_ta_hours) ))
            return HttpResponseRedirect(next)

        request.session['decline_reassign_form_data'] = request.POST
        return HttpResponseRedirect( reverse('administrators:decline_reassign_confirmation') + '?next=' + next )

    return HttpResponseRedirect(next)


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def decline_reassign_confirmation(request):
    ''' Display currnt status and new status for reassigning confirmation '''
    request = userApi.has_admin_access(request)
    adminApi.can_req_parameters_access(request, 'none', ['next'])

    app = None
    old_assigned_hours = None
    new_assigned_hours = None
    new_ta_hours = None
    if request.method == 'POST':

        # Check whether a next url is valid or not
        adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

        if request.POST.get('is_declined_reassigned') == None:
            messages.error(request, 'An error occurred. Please click on the checkbox to decline and re-assign.')
            return HttpResponseRedirect(request.get_full_path())

        app_id = request.POST.get('application')
        old_assigned_hours = request.POST.get('old_assigned_hours')
        new_assigned_hours = request.POST.get('new_assigned_hours')
        app = adminApi.get_application(app_id)
        accepted_status = app.applicationstatus_set.filter(assigned=ApplicationStatus.ACCEPTED).last()

        status_form = ApplicationStatusReassignForm({
            'application': app_id,
            'assigned': ApplicationStatus.DECLINED,
            'assigned_hours': new_assigned_hours,
            'parent_id': accepted_status.id
        })

        reassign_form = ReassignApplicationForm(request.POST, instance=app)

        if status_form.is_valid() and reassign_form.is_valid():
            app_status = status_form.save()

            reaasigned_app = reassign_form.save(commit=False)
            reaasigned_app.updated_at = datetime.now()
            reaasigned_app.save()

            errors = []
            if not app_status: errors.append('An error occurred while saving a declined status.')
            if not reaasigned_app: errors.append('An error occurred. Failed to update a note in the application.')

            if len(errors) > 0:
                messages.error(request, 'An error occurred while sending a job offer. {0}'.format( ' '.join(errors) ))
                return HttpResponseRedirect(request.get_full_path())

            # admin documents updated
            if hasattr(reaasigned_app, 'admindocuments'):
                if reaasigned_app.admindocuments.processed == None:
                    messages.success(request, 'Success! The status of Application (ID: {0}) updated'.format(app_id))
                else:
                    old_processed = reaasigned_app.admindocuments.processed
                    reaasigned_app.admindocuments.processed = None
                    reaasigned_app.admindocuments.processing_note += "<p>Auto update: Processed - <strong class='text-primary'>{0}</strong> on {1}</p>".format(old_processed, datetime.today().strftime('%Y-%m-%d'))
                    reaasigned_app.admindocuments.save(update_fields=['processed', 'processing_note'])

                    if reaasigned_app.admindocuments.processing_note.find(old_processed) > -1:
                        messages.success(request, 'Success! The status of Application (ID: {0}) updated'.format(app_id))
                    else:
                        reaasigned_app.admindocuments.processed = old_processed
                        reaasigned_app.admindocuments.save(update_fields=['processed'])
                        messages.warning(request, 'Warning! The Processed data of Application (ID: {0}) is not updated into the processing note.'.format(app_id))
            else:
                messages.success(request, 'Success! The status of Application (ID: {0}) updated'.format(app_id))

            return HttpResponseRedirect(request.POST.get('next'))

        else:
            errors = [
                userApi.get_error_messages(status_form.errors.get_json_data()),
                userApi.get_error_messages(reassign_form.errors.get_json_data())
            ]
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format(', '.join(errors)))

        return HttpResponseRedirect(request.get_full_path())

    else:
        data = request.session.get('decline_reassign_form_data')
        if data:
            app_id = data.get('application')
            old_assigned_hours = data.get('old_assigned_hours')
            new_assigned_hours = data.get('new_assigned_hours')

            app = adminApi.get_application(app_id)
            ta_hours = app.job.accumulated_ta_hours
            new_ta_hours = float(ta_hours) - float(old_assigned_hours) + float(new_assigned_hours)

    return render(request, 'administrators/applications/decline_reassign_confirmation.html', {
        'loggedin_user': request.user,
        'app': app,
        'old_assigned_hours': old_assigned_hours,
        'new_assigned_hours': new_assigned_hours,
        'new_ta_hours': new_ta_hours,
        'form': ReassignApplicationForm(data=None, instance=app),
        'next': adminApi.get_next(request)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET','POST'])
def terminate(request, app_slug):
    ''' Terminate an application, then students can can their accepted jobs '''
    request = userApi.has_admin_access(request)
    adminApi.can_req_parameters_access(request, 'none', ['next'])

    app = adminApi.get_application(app_slug, 'slug')
    if app.is_terminated: raise Http404

    if request.method == 'POST':

        # Check whether a next url is valid or not
        adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

        if request.POST.get('is_terminated') == None:
            messages.error(request, 'An error occurred. Please click on the checkbox to terminate.')
            return HttpResponseRedirect(request.get_full_path())

        form = TerminateApplicationForm(request.POST, instance=app)
        if form.is_valid():
            terminated_app = form.save(commit=False)
            terminated_app.updated_at = datetime.now()
            terminated_app.save()
            if terminated_app:
                messages.success(request, 'Success! Application (ID: {0}) terminated.'.format(terminated_app.id))
                return HttpResponseRedirect(request.POST.get('next'))
            else:
                messages.error(request, 'An error occurred while termniating an application.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect(request.get_full_path())

    return render(request, 'administrators/applications/terminate.html', {
        'loggedin_user': request.user,
        'app': app,
        'form': TerminateApplicationForm(data=None, instance=app),
        'next': adminApi.get_next(request)
    })


@method_decorator([never_cache], name='dispatch')
class TerminatedApplications(LoginRequiredMixin, View):
    ''' Terminated applications '''

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        request = userApi.has_admin_access(request)

        app_list, info = adminApi.get_applications_filter_limit(request, 'terminated')

        page = request.GET.get('page', 1)
        paginator = Paginator(app_list, utils.TABLE_PAGE_SIZE)

        try:
            apps = paginator.page(page)
        except PageNotAnInteger:
            apps = paginator.page(1)
        except EmptyPage:
            apps = paginator.page(paginator.num_pages)

        return render(request, 'administrators/applications/terminated_applications.html', {
            'loggedin_user': request.user,
            'apps': apps,
            'num_filtered_apps': info['num_filtered_apps'],
            'admin_emails': adminApi.get_admin_emails(),
            'app_status': APP_STATUS,
            'new_next': adminApi.build_new_next(request)
        })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def applications_send_email(request):
    ''' Send an email for applications '''
    request = userApi.has_admin_access(request)
    adminApi.can_req_parameters_access(request, 'app', ['next', 'p'])

    if request.method == 'POST':
        applications = request.POST.getlist('application')
        if len(applications) > 0:
            type = request.POST.get('type')
            request.session['applications_form_data'] = {
                'applications': applications,
                'type': type
            }
            return HttpResponseRedirect(reverse('administrators:applications_send_email_confirmation') + '?next=' + adminApi.get_next(request) + '&p=' + request.GET.get('p'))
        else:
            messages.error(request, 'An error occurred. Please select applications, then try again.')

    return HttpResponseRedirect(adminApi.get_next(request))


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def applications_send_email_confirmation(request):
    ''' Display a list of email for offered applications '''
    request = userApi.has_admin_access(request)
    adminApi.can_req_parameters_access(request, 'app', ['next', 'p'])

    path = request.GET.get('p')

    applications = []
    receiver_list = []
    form = None
    type = None
    admin_email = None

    form_data = request.session.get('applications_form_data')
    if form_data:
        app_ids = form_data['applications']
        applications = adminApi.get_applications_with_multiple_ids_by_path(app_ids, path)
        receiver_list = [ app.applicant.email for app in applications ]

        if request.method == 'POST':

            # Check whether a next url is valid or not
            adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

            form = EmailForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data

                receivers = []
                count = 0
                for app in applications:
                    assigned_hours = None
                    if path == 'Offered Applications':
                        assigned_hours = app.offered.assigned_hours
                    elif path == 'Declined Applications':
                        assigned_hours = app.declined.assigned_hours
                    elif path == 'Terminated Applications':
                        assigned_hours = app.accepted.assigned_hours

                    instructors = []
                    for instructor in app.job.instructors.all():
                        instructors.append(instructor.get_full_name())

                    name = app.applicant.first_name + ' ' + app.applicant.last_name
                    message = data['message'].format(
                        name,
                        app.applicant.profile.student_number,
                        app.job.session.year + ' ' + app.job.session.term.code,
                        app.job.course.code.name + ' ' + app.job.course.number.name + ' ' + app.job.course.section.name,
                        ', '.join(instructors),
                        assigned_hours,
                        app.classification.name
                    )

                    receiver = '{0} <{1}>'.format(name, app.applicant.email)

                    email = adminApi.send_and_create_email(app, data['sender'], receiver, data['title'], message, data['type'])
                    if email:
                        receivers.append(app.applicant.email)
                        count += 1

                if count == len(applications):
                    messages.success(request, 'Success! Email has been sent to {0}'.format( data['receiver'] ))
                else:
                    if len(receivers) > 0:
                        messages.error( request, 'An error occurred. Email has been sent to {0}, but not all receivers. Please check a list of receivers.'.format(', '.join(receivers)) )
                    else:
                        messages.error(request, 'An error occurred. Failed to send emails')

                del request.session['applications_form_data']
                return HttpResponseRedirect(request.POST.get('next'))
            else:
                errors = form.errors.get_json_data()
                messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

            return HttpResponseRedirect(request.get_full_path())

        else:
            type = form_data['type']
            admin_email = adminApi.get_admin_email_by_slug(type)
            title = admin_email.title
            message = admin_email.message

            form = EmailForm(initial={
                'sender': settings.EMAIL_FROM,
                'receiver': receiver_list,
                'title': title,
                'message': message,
                'type': admin_email.type
            })

    return render(request, 'administrators/applications/applications_send_email_confirmation.html', {
        'loggedin_user': request.user,
        'applications': applications,
        'sender': settings.EMAIL_FROM,
        'receiver': receiver_list,
        'form': form,
        'admin_email': admin_email if admin_email else None,
        'path': path,
        'next': adminApi.get_next(request)
    })


@method_decorator([never_cache], name='dispatch')
class AcceptedAppsReportAdmin(LoginRequiredMixin, View):
    ''' Display a report of applications accepted by students for Admin '''

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        request = userApi.has_admin_access(request, Role.HR)

        apps, total_apps = adminApi.get_accepted_app_report(request)

        page = request.GET.get('page', 1)
        paginator = Paginator(apps, 10)

        try:
            apps = paginator.page(page)
        except PageNotAnInteger:
            apps = paginator.page(1)
        except EmptyPage:
            apps = paginator.page(paginator.num_pages)

        for app in apps:
            app = adminApi.add_app_info_into_application(app, ['accepted'])

            app.salary = adminApi.calculate_salary(app)
            pt_percentage = adminApi.calculate_pt_percentage(app)
            app.pt_percentage = pt_percentage
            app.weekly_hours = pt_percentage / 100 * 12

            prev_apps = app.applicant.application_set.filter(job__session__year__lt=app.job.session.year)
            app.prev_accepted_apps = None
            total_assigned_hours = 0
            if prev_apps.exists():
                prev_accepted_apps = adminApi.get_accepted_apps_not_terminated(prev_apps)
                prev_accepted_apps = adminApi.get_filtered_accepted_apps(prev_accepted_apps)
                for ap in prev_accepted_apps:
                    ap = adminApi.add_app_info_into_application(ap, ['accepted'])
                    total_assigned_hours += ap.accepted.assigned_hours

                app.prev_accepted_apps = prev_accepted_apps
                app.total_assigned_hours = total_assigned_hours

            prev_year_apps = app.applicant.application_set.filter(job__session__year=int(app.job.session.year)-1, job__session__term__code=app.job.session.term.code)
            app.prev_year_accepted_apps = None
            total_prev_year_assigned_hours = 0
            if prev_year_apps.exists():
                prev_year_accepted_apps = adminApi.get_accepted_apps_not_terminated(prev_year_apps)
                prev_year_accepted_apps = adminApi.get_filtered_accepted_apps(prev_year_accepted_apps)
                for ap in prev_year_accepted_apps:
                    ap = adminApi.add_app_info_into_application(ap, ['accepted'])
                    total_prev_year_assigned_hours += ap.accepted.assigned_hours

                app.prev_year_accepted_apps = prev_year_accepted_apps
                app.total_prev_year_assigned_hours = total_prev_year_assigned_hours

            lfs_grad_or_others = userApi.get_lfs_grad_or_others(app.applicant)
            app.lfs_grad_or_others = lfs_grad_or_others

            is_preferred_student = False
            if total_assigned_hours > 0 and lfs_grad_or_others == 'LFS GRAD':
                is_preferred_student = True

            app.is_preferred_student = is_preferred_student

            confi_info_expiry_status = { 'sin': None, 'study_permit': None }
            for st in userApi.get_confidential_info_expiry_status(app.applicant):
                if st['doc'] == 'SIN':
                    confi_info_expiry_status['sin'] = st['status'].upper()
                elif st['doc'] == 'Study Permit':
                    confi_info_expiry_status['study_permit'] = st['status'].upper()

            app.confi_info_expiry_status = confi_info_expiry_status

        return render(request, 'administrators/applications/accepted_apps_report_admin.html', context={
            'total_apps': total_apps,
            'apps': apps,
            'download_all_accepted_apps_report_admin_url': reverse('administrators:download_all_accepted_apps_report_admin')
        })


@method_decorator([never_cache], name='dispatch')
class AcceptedAppsReportObserver(LoginRequiredMixin, View, AcceptedAppsReportMixin):
    ''' Display a report of applications accepted by students for Observer '''
    pass


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def download_all_accepted_apps(request):
    ''' Download all accepted applications as CSV '''

    apps, info = adminApi.get_applications_filter_limit(request, 'accepted')
    apps = adminApi.add_app_info_into_applications(apps, ['accepted'])

    result = 'ID,Year,Term,Job,First Name,Last Name,CWL,Student Number,Employee Number,Classification,Monthly Salary,P/T (%),Positin Number,PIN,TASM,Processed,Worktag,Processing Note,Accepted on,Assigned Hours\n'
    for app in apps:
        year = app.job.session.year
        term = app.job.session.term.code
        job = '{0} {1} {2}'.format(app.job.course.code.name, app.job.course.number.name, app.job.course.section.name)
        first_name = app.applicant.first_name
        last_name = app.applicant.last_name
        cwl = app.applicant.username

        student_number = ''
        if userApi.profile_exists(app.applicant):
            student_number = app.applicant.profile.student_number

        employee_number = 'NEW'
        if userApi.confidentiality_exists(app.applicant):
            if app.applicant.confidentiality.employee_number:
                employee_number = app.applicant.confidentiality.employee_number

        classification = '{0} {1} (${2})'.format(app.classification.year, app.classification.name, format(round(app.classification.wage, 2), '.2f'))
        salary = '${0}'.format( format(adminApi.calculate_salary(app), '.2f') )
        pt = format( adminApi.calculate_pt_percentage(app), '.2f' )

        position_number = ''
        pin = ''
        tasm = ''
        processed = ''
        worktag = ''
        processing_note = ''
        if adminApi.has_admin_docs_created(app):
            if app.admindocuments.position_number:
                position_number = app.admindocuments.position_number
            if app.admindocuments.pin:
                pin = app.admindocuments.pin
            if app.admindocuments.tasm:
                tasm = 'YES'
            if app.admindocuments.processed:
                processed = app.admindocuments.processed
            if app.admindocuments.worktag:
                worktag = app.admindocuments.worktag
            if app.admindocuments.processing_note:
                processing_note = adminApi.strip_html_tags(app.admindocuments.processing_note)

        accepted_on = ''
        assigned_hours = ''
        if app.accepted:
            accepted_on = app.accepted.created_at
            assigned_hours = app.accepted.assigned_hours

        result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19}\n'.format(
            app.id,
            year,
            term,
            job,
            first_name,
            last_name,
            cwl,
            student_number,
            employee_number,
            classification,
            salary,
            pt,
            position_number,
            pin,
            tasm,
            processed,
            '\"' + worktag + '\"',
            '\"' + processing_note + '\"',
            accepted_on,
            assigned_hours
        )

    return JsonResponse({ 'status': 'success', 'data': result })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def download_all_accepted_apps_report_admin(request):
    ''' Download accepted applications as CSV for admin '''

    apps, total_apps = adminApi.get_accepted_app_report(request)
    apps = adminApi.add_app_info_into_applications(apps, ['accepted'])

    result = 'ID,Preferred Student,Year,Term,Job,Instructor(s),First Name,Last Name,CWL,Student Number,Employee Number,Domestic or International Student,Status,LFS Grad or Others,SIN Expiry Date,Study Permit Expiry Date,Accepted on,Assigned Hours,Classification,Monthly Salary,P/T (%),Weekly Hours,PIN,TASM,Processed,Worktag,Processing Note,Previous TA Experience Details,Previous TA Experience in UBC,Total Assigned Hours - Previous TA Experience in UBC,Previous Year TA Experience in Same Term,Total Previous Year Assigned Hours in Same Term\n'

    for app in apps:
        year = app.job.session.year
        term = app.job.session.term.code
        job = '{0} {1} {2}'.format(app.job.course.code.name, app.job.course.number.name, app.job.course.section.name)
        instructors = ''
        if app.job.instructors.count() > 0:
            for i, ins in enumerate(app.job.instructors.all()):
                instructors += ins.get_full_name()
                if i < app.job.instructors.count() - 1:
                    instructors += '\n'

        first_name = app.applicant.first_name
        last_name = app.applicant.last_name
        cwl = app.applicant.username

        student_number = ''
        status = ''
        ta_experience_details = ''
        if userApi.profile_exists(app.applicant):
            if app.applicant.profile.student_number:
                student_number = app.applicant.profile.student_number

            if app.applicant.profile.status:
                status = app.applicant.profile.status.name

            if app.applicant.profile.ta_experience_details:
                ta_experience_details = adminApi.strip_html_tags(app.applicant.profile.ta_experience_details)

        employee_number = 'NEW'
        nationality = ''
        lfs_grad_or_others = userApi.get_lfs_grad_or_others(app.applicant)

        sin_expiry_date = ''
        study_permit_expiry_date = ''
        if userApi.confidentiality_exists(app.applicant):
            if app.applicant.confidentiality.employee_number:
                employee_number = app.applicant.confidentiality.employee_number

            if app.applicant.confidentiality.nationality:
                nationality = app.applicant.confidentiality.get_nationality_display()

            if nationality == 'International Student':
                sin_expiry_date = app.applicant.confidentiality.sin_expiry_date
                study_permit_expiry_date = app.applicant.confidentiality.study_permit_expiry_date

        salary = '${0}'.format(format(adminApi.calculate_salary(app), '.2f'))
        pt = format(adminApi.calculate_pt_percentage(app), '.2f')
        weekly_hours = format(adminApi.calculate_weekly_hours(pt), '.2f')

        classification = '{0} {1} ({2})'.format(
            app.classification.year,
            app.classification.name,
            format(app.classification.wage, '.2f'),
        )

        pin = ''
        tasm = ''
        processed = ''
        worktag = ''
        processing_note = ''
        if adminApi.has_admin_docs_created(app):
            if app.admindocuments.pin:
                pin = app.admindocuments.pin

            if app.admindocuments.tasm:
                tasm = 'YES'

            if app.admindocuments.processed:
                processed = app.admindocuments.processed

            if app.admindocuments.worktag:
                worktag = app.admindocuments.worktag

            if app.admindocuments.processing_note:
                processing_note = adminApi.strip_html_tags(app.admindocuments.processing_note)

        accepted_on = ''
        assigned_hours = ''
        if app.accepted:
            accepted_on = app.accepted.created_at
            assigned_hours = app.accepted.assigned_hours

        prev_apps = app.applicant.application_set.filter(job__session__year__lt=app.job.session.year)
        total_assigned_hours = 0
        prev_accepted_apps_ubc = ''
        if prev_apps.exists():
            prev_accepted_apps = adminApi.get_accepted_apps_not_terminated(prev_apps)
            prev_accepted_apps = adminApi.get_filtered_accepted_apps(prev_accepted_apps)
            for ap in prev_accepted_apps:
                ap = adminApi.add_app_info_into_application(ap, ['accepted'])
                total_assigned_hours += ap.accepted.assigned_hours

                prev_accepted_apps_ubc += '{0} {1}, {2} {3} {4}, {5} {6} (${7}), {8} hours, {9}\n'.format(
                    ap.job.session.year,
                    ap.job.session.term.code,
                    ap.job.course.code.name,
                    ap.job.course.number.name,
                    ap.job.course.section.name,
                    ap.classification.year,
                    ap.classification.name,
                    format(ap.classification.wage, '.2f'),
                    ap.accepted.assigned_hours,
                    ap.accepted.created_at
                )

        prev_year_apps = app.applicant.application_set.filter(job__session__year=int(app.job.session.year)-1, job__session__term__code=app.job.session.term.code)
        total_prev_year_assigned_hours = 0
        prev_year_accepted_apps_ubc = ''
        if prev_year_apps.exists():
            prev_year_accepted_apps = adminApi.get_accepted_apps_not_terminated(prev_year_apps)
            prev_year_accepted_apps = adminApi.get_filtered_accepted_apps(prev_year_accepted_apps)
            for ap in prev_year_accepted_apps:
                ap = adminApi.add_app_info_into_application(ap, ['accepted'])
                total_prev_year_assigned_hours += ap.accepted.assigned_hours

                prev_year_accepted_apps_ubc += '{0} {1}, {2} {3} {4}, {5} {6} (${7}), {8} hours, {9}\n'.format(
                    ap.job.session.year,
                    ap.job.session.term.code,
                    ap.job.course.code.name,
                    ap.job.course.number.name,
                    ap.job.course.section.name,
                    ap.classification.year,
                    ap.classification.name,
                    format(ap.classification.wage, '.2f'),
                    ap.accepted.assigned_hours,
                    ap.accepted.created_at
                )

        preferred_student = ''
        if total_assigned_hours > 0 and lfs_grad_or_others == 'LFS GRAD':
            preferred_student = 'YES'

        result += '{0},{1},{2},{3},"{4}",{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19},{20},{21},{22},{23},{24},{25},{26},{27},{28},{29},{30},{31}\n'.format(
            app.id,
            preferred_student,
            year,
            term,
            job,
            '\"' + instructors + '\"',
            first_name,
            last_name,
            cwl,
            student_number,
            employee_number,
            nationality,
            status,
            lfs_grad_or_others,
            sin_expiry_date,
            study_permit_expiry_date,
            accepted_on,
            assigned_hours,
            classification,
            salary,
            pt,
            weekly_hours,
            pin,
            tasm,
            processed,
            '\"' + worktag + '\"',
            '\"' + processing_note + '\"',
            '\"' + ta_experience_details + '\"',
            '\"' + prev_accepted_apps_ubc + '\"',
            total_assigned_hours,
            '\"' + prev_year_accepted_apps_ubc + '\"',
            total_prev_year_assigned_hours
        )
    return JsonResponse({ 'status': 'success', 'data': result })


# HR


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def all_users(request):
    ''' Display all users'''
    request = userApi.has_admin_access(request)

    first_name_q = request.GET.get('first_name')
    last_name_q = request.GET.get('last_name')
    preferred_name_q = request.GET.get('preferred_name')
    cwl_q = request.GET.get('cwl')
    student_number_q = request.GET.get('student_number')
    employee_number_q = request.GET.get('employee_number')

    user_list = userApi.get_users()
    if bool(first_name_q):
        user_list = user_list.filter(first_name__icontains=first_name_q)
    if bool(last_name_q):
        user_list = user_list.filter(last_name__icontains=last_name_q)
    if bool(preferred_name_q):
        user_list = user_list.filter(profile__preferred_name__icontains=preferred_name_q)
    if bool(cwl_q):
        user_list = user_list.filter(username__icontains=cwl_q)
    if bool(student_number_q):
        user_list = user_list.filter(profile__student_number__icontains=student_number_q)
    if bool(employee_number_q):
        user_list = user_list.filter(confidentiality__employee_number__icontains=employee_number_q)


    page = request.GET.get('page', 1)
    paginator = Paginator(user_list, utils.TABLE_PAGE_SIZE)

    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)

    return render(request, 'administrators/hr/all_users.html', {
        'loggedin_user': request.user,
        'users': users,
        'total_users': len(user_list),
        'new_next': adminApi.build_new_next(request)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def create_user(request):
    ''' Create a user '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        validation = userApi.validate_post(request.POST, ['first_name', 'last_name', 'email', 'username'])
        if len(validation) > 0:
            messages.error(request, 'An error occurred while saving an User Form. {0}: This field is required.'.format( ', '.join(validation) ))
            return redirect('administrators:create_user')

        user_form = UserForm(request.POST)
        user_profile_form = UserProfileForm(request.POST)

        if user_form.is_valid() and user_profile_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password( userApi.password_generator() )
            user.save()

            profile = userApi.create_profile(user, user_profile_form.cleaned_data)

            errors = []
            if not user: errors.append('An error occurred while creating an user.')
            if not profile: errors.append('An error occurred while creating an user profile.')

            if len(errors) > 0:
                messages.error(request, 'An error occurred while saving an User Form. {0}'.format( ' '.join(errors) ))
                return redirect('administrators:create_user')

            confidentiality = userApi.has_user_confidentiality_created(user)

            data = {
                'user': user.id,
                'is_new_employee': False if request.POST.get('is_new_employee') == None else True,
                'employee_number': request.POST.get('employee_number')
            }
            employee_number_form = EmployeeNumberEditForm(data, instance=confidentiality)

            if employee_number_form.is_valid() == False:
                employee_number_errors = employee_number_form.errors.get_json_data()
                messages.error(request, 'An error occurred while creating an User Form. {0}'.format(employee_number_errors))

            employee_number = employee_number_form.save(commit=False)
            employee_number.created_at = datetime.now()
            employee_number.updated_at = datetime.now()
            employee_number.save()

            if not employee_number: errors.append('An error occurred while updating an employee number.')

            if len(errors) > 0:
                messages.error(request, 'An error occurred while saving an User Form. {0}'.format( ' '.join(errors) ))
                return redirect('administrators:create_user')

            messages.success(request, 'Success! {0} {1} (CWL: {2}) created'.format(user.first_name, user.last_name, user.username))
            return redirect('administrators:all_users')

        else:
            errors = []

            user_errors = user_form.errors.get_json_data()
            profile_errors = user_profile_form.errors.get_json_data()

            if user_errors: errors.append( userApi.get_error_messages(user_errors) )
            if profile_errors: errors.append( userApi.get_error_messages(profile_errors) )

            messages.error(request, 'An error occurred while creating an User Form. {0}'.format( ' '.join(errors) ))

        return redirect('administrators:create_user')

    return render(request, 'administrators/hr/create_user.html', {
        'loggedin_user': request.user,
        'users': userApi.get_users(),
        'user_form': UserForm(),
        'user_profile_form': UserProfileForm(),
        'employee_number_form': EmployeeNumberForm()
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_user(request, username):
    ''' Edit a user '''
    request = userApi.has_admin_access(request)
    adminApi.can_req_parameters_access(request, 'user', ['next', 'p'])

    user = userApi.get_user(username, 'username')
    confidentiality = userApi.has_user_confidentiality_created(user)

    # Create a confiential information if it's None
    if confidentiality == None:
        confidentiality = userApi.create_confidentiality(user)

    if request.method == 'POST':
        # Check whether a next url is valid or not
        adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

        validation = userApi.validate_post(request.POST, ['first_name', 'last_name', 'email', 'username'])
        if len(validation) > 0:
            messages.error(request, 'An error occurred while updating an User Edit Form. {0}: This field is required.'.format( ', '.join(validation) ))
            return HttpResponseRedirect(request.get_full_path())


        profile_roles = user.profile.roles.all()

        user_form = UserForm(request.POST, instance=user)
        user_profile_edit_form = UserProfileEditForm(request.POST, instance=user.profile)
        employee_number_form = EmployeeNumberEditForm(request.POST, instance=confidentiality)

        old_username = user.username
        new_username = request.POST.get('username')
        if user_form.is_valid() and user_profile_edit_form.is_valid() and employee_number_form.is_valid():
            updated_user = user_form.save()

            # Update the new username in the path of items - avatar image, resume, sin and study permit
            if request.POST.get('username') != old_username:
                new_dirpath = os.path.join( settings.MEDIA_ROOT, 'users', new_username )
                if os.path.exists(new_dirpath) == False:
                    try:
                        os.mkdir(new_dirpath) # Create a new directory
                    except OSError:
                        SuspiciousOperation

                # Resume
                if userApi.has_user_resume_created(user) and bool(user.resume.uploaded):
                    resume_path = os.path.join( settings.MEDIA_ROOT, 'users', new_username, 'resume' )
                    if os.path.exists(resume_path) == False:
                        try:
                            os.mkdir(resume_path) # Create a new resume directory
                        except OSError:
                            SuspiciousOperation

                    if os.path.exists(resume_path) and os.path.isdir(resume_path):
                        file_path = user.resume.uploaded.name
                        filename = file_path.replace(old_username, new_username)

                        initial_path = user.resume.uploaded.path
                        new_path = os.path.join(settings.MEDIA_ROOT, filename)
                        os.rename(initial_path, new_path)

                        user.resume.uploaded = filename
                        user.resume.save(update_fields=['uploaded'])

                        # Remove an old resume directory
                        try:
                            os.rmdir( os.path.join( settings.MEDIA_ROOT, 'users', old_username, 'resume' ) )
                        except OSError:
                            SuspiciousOperation

                # Avatar
                if userApi.has_user_avatar_created(user) and bool(user.avatar.uploaded):
                    avatar_path = os.path.join( settings.MEDIA_ROOT, 'users', new_username, 'avatar' )
                    if os.path.exists(avatar_path) == False:
                        try:
                            os.mkdir(avatar_path) # Create a new avatar directory
                        except OSError:
                            SuspiciousOperation

                    if os.path.exists(avatar_path) and os.path.isdir(avatar_path):
                        file_path = user.avatar.uploaded.name
                        filename = file_path.replace(old_username, new_username)

                        initial_path = user.avatar.uploaded.path
                        new_path = os.path.join(settings.MEDIA_ROOT, filename)
                        os.rename(initial_path, new_path)

                        user.avatar.uploaded = filename
                        user.avatar.save(update_fields=['uploaded'])

                        # Remove an old avatar directory
                        try:
                            os.rmdir( os.path.join( settings.MEDIA_ROOT, 'users', old_username, 'avatar' ) )
                        except OSError:
                            SuspiciousOperation

                if userApi.has_user_confidentiality_created(user):
                    update_fields = []
                    if bool(user.confidentiality.sin):
                        sin_path = os.path.join( settings.MEDIA_ROOT, 'users', new_username, 'sin' )
                        if os.path.exists(sin_path) == False:
                            try:
                                os.mkdir(sin_path) # Create a new sin directory
                            except OSError:
                                SuspiciousOperation

                        if os.path.exists(sin_path) and os.path.isdir(sin_path):
                            file_path = user.confidentiality.sin.name
                            filename = file_path.replace(old_username, new_username)

                            initial_path = user.confidentiality.sin.path
                            new_path = os.path.join(settings.MEDIA_ROOT, filename)
                            os.rename(initial_path, new_path)

                            user.confidentiality.sin = filename

                            # Remove an old sin directory
                            try:
                                os.rmdir( os.path.join( settings.MEDIA_ROOT, 'users', old_username, 'sin' ) )
                            except OSError:
                                SuspiciousOperation

                            update_fields.append('sin')

                    if bool(user.confidentiality.study_permit):
                        study_permit_path = os.path.join( settings.MEDIA_ROOT, 'users', new_username, 'study_permit' )
                        if os.path.exists(study_permit_path) == False:
                            try:
                                os.mkdir(study_permit_path) # Create a new study_permit directory
                            except OSError:
                                SuspiciousOperation

                        if os.path.exists(study_permit_path) and os.path.isdir(study_permit_path):
                            file_path = user.confidentiality.study_permit.name
                            filename = file_path.replace(old_username, new_username)

                            initial_path = user.confidentiality.study_permit.path
                            new_path = os.path.join(settings.MEDIA_ROOT, filename)
                            os.rename(initial_path, new_path)

                            user.confidentiality.study_permit = filename

                            # Remove an old sin directory
                            try:
                                os.rmdir( os.path.join( settings.MEDIA_ROOT, 'users', old_username, 'study_permit' ) )
                            except OSError:
                                SuspiciousOperation

                            update_fields.append('study_permit')

                    if len(update_fields) > 0:
                        user.confidentiality.save(update_fields=update_fields)

                # If an old folder is empty, delete it
                old_dirpath = os.path.join( settings.MEDIA_ROOT, 'users', old_username )
                if os.path.exists(old_dirpath) and os.path.isdir(old_dirpath) and len( os.listdir(old_dirpath) ) == 0:
                    try:
                        os.rmdir(old_dirpath)
                    except OSError:
                        print("The folder hasn't been deleted")

            updated_profile = user_profile_edit_form.save(commit=False)
            updated_profile.updated_at = datetime.now()
            updated_profile.save()

            errors = []

            updated_employee_number = employee_number_form.save(commit=False)
            updated_employee_number.updated_at = datetime.now()
            updated_employee_number.is_new_employee = employee_number_form.cleaned_data['is_new_employee']
            updated_employee_number.employee_number = employee_number_form.cleaned_data['employee_number']
            updated_employee_number.save(update_fields=['is_new_employee', 'employee_number', 'updated_at'])

            if not updated_user: errors.append('USER')
            if not updated_profile: errors.append('PROFILE')
            if not updated_employee_number: errors.append('EMPLOYEE NUMBER')

            updated = userApi.update_user_profile_roles(updated_profile, profile_roles, user_profile_edit_form.cleaned_data)
            if not updated: errors.append(request, 'An error occurred while updating profile roles.')

            if len(errors) > 0:
                messages.error(request, 'An error occurred while updating an User Edit Form. {0}'.format( ' '.join(errors) ))
                return HttpResponseRedirect(request.get_full_path())

            messages.success(request, 'Success! User information of {0} (CWL: {1}) updated'.format(user.get_full_name(), user.username))
            return HttpResponseRedirect(request.POST.get('next'))
        else:
            errors = []

            user_errors = user_form.errors.get_json_data()
            profile_errors = user_profile_edit_form.errors.get_json_data()
            confid_errors = employee_number_form.errors.get_json_data()

            if user_errors: errors.append( userApi.get_error_messages(user_errors) )
            if profile_errors: errors.append( userApi.get_error_messages(profile_errors) )
            if confid_errors: errors.append( userApi.get_error_messages(confid_errors) )

            messages.error(request, 'An error occurred while updating an User Form. {0}'.format( ' '.join(errors) ))

        return HttpResponseRedirect(request.get_full_path())

    else:
        profile = userApi.has_user_profile_created(user)
        if profile == None:
            profile = userApi.create_profile_init(user)
            user = userApi.get_user(username, 'username')
            messages.warning(request, 'This user (CWL: {0}) does not have any profile. Users must have at least one role. Please choose a role.'.format(user.username))

    return render(request, 'administrators/hr/edit_user.html', {
        'loggedin_user': request.user,
        'user': userApi.add_avatar(user),
        'roles': userApi.get_roles(),
        'user_form': UserForm(data=None, instance=user),
        'user_profile_form': UserProfileEditForm(data=None, instance=user.profile),
        'employee_number_form': EmployeeNumberEditForm(data=None, instance=confidentiality),
        'next': adminApi.get_next(request)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET','POST'])
def delete_user_confirmation(request, username):
    ''' Delete a user '''
    request = userApi.has_admin_access(request)
    adminApi.can_req_parameters_access(request, 'user', ['next', 'p'])

    user = userApi.get_user(username, 'username')
    apps = []
    if request.method == 'POST':
        user = userApi.get_user( request.POST.get('user') )

        sin = userApi.delete_user_sin(user.username)
        study_permit = userApi.delete_user_study_permit(user.username)

        if userApi.has_user_confidentiality_created(user) != None and sin and study_permit:
            user.confidentiality.delete()

        if userApi.confidentiality_exists(user) == False:
            messages.success(request, "Success! {0} ({1})'s Confidential Information deleted".format(user.get_full_name(), user.username))
        else:
            messages.error(request, 'An error occurred while deleting the Confidential Information of the user - {0}.'.format(user.get_full_name()))

        return HttpResponseRedirect(request.POST.get('next'))

    else:
        user = userApi.add_confidentiality_given_list(user, ['sin','study_permit'])

    return render(request, 'administrators/hr/delete_user_confirmation.html', {
        'loggedin_user': request.user,
        'user': userApi.add_resume(user),
        'users': userApi.get_users(),
        'next': adminApi.get_next(request),
        'undergrad_status_id': userApi.get_undergraduate_status_id()
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def destroy_user_contents(request):
    ''' Destroy users who have no actions for 3 years '''
    request = userApi.has_admin_access(request)

    users = None
    target_date = None
    if request.method == 'POST':
        if len(request.POST.getlist('user')) < 1:
            messages.error(request, 'An error occurred. Please select any user(s) to be destroyed from the list below.')
            return redirect('administrators:destroy_user_contents')

        deleted_users = []
        count = 0
        for user_id in request.POST.getlist('user'):
            user = userApi.get_user(user_id)

            userApi.delete_user_sin(user.username)
            userApi.delete_user_study_permit(user.username)

            if userApi.has_user_confidentiality_created(user):
                user.confidentiality.delete()

            resume = userApi.delete_user_resume(user.id)
            avatar = userApi.delete_user_avatar(user.id)
            profile = userApi.trim_profile(user)

            dirpath = os.path.join( settings.MEDIA_ROOT, 'users', user.username )
            if os.path.exists(dirpath) and os.path.isdir(dirpath):
                os.rmdir(dirpath)

            if profile and resume['status'] == 'success' and avatar['status'] == 'success' and userApi.resume_exists(user) == False and userApi.confidentiality_exists(user) == False:
                deleted_users.append(user.get_full_name())
                count += 1

        if count == len(deleted_users):
            messages.success(request, 'Success! The contents of users ({0}) are destroyed completely'.format( ', '.join(deleted_users) ))
        elif len(deleted_users)> 0:
            messages.warning(request, 'Warning! The contents of users ({0}) are destroyed partially'.format( ', '.join(deleted_users) ))
        else:
            messages.error(request, 'An error occurred. Form is invalid. {0}')

        return redirect('administrators:destroy_user_contents')

    else:
        user_list, target_date = userApi.get_users('destroy')
        users = []
        for user in user_list:
            user = userApi.add_confidentiality_given_list(user, ['sin','study_permit'])
            user = userApi.add_resume(user)
            users.append(user)

    return render(request, 'administrators/hr/destroy_user_contents.html', {
        'loggedin_user': request.user,
        'users': users,
        'target_date': target_date,
        'undergrad_status_id': userApi.get_undergraduate_status_id()
    })


# Courses


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def all_courses(request):
    ''' Display all courses and edit/delete a course '''
    request = userApi.has_admin_access(request)

    term_q = request.GET.get('term')
    code_q = request.GET.get('code')
    number_q = request.GET.get('number')
    section_q = request.GET.get('section')
    course_name_q = request.GET.get('course_name')

    course_list = adminApi.get_courses()
    if bool(term_q):
        course_list = course_list.filter(term__code__icontains=term_q)
    if bool(code_q):
        course_list = course_list.filter(code__name__icontains=code_q)
    if bool(number_q):
        course_list = course_list.filter(number__name__icontains=number_q)
    if bool(section_q):
        course_list = course_list.filter(section__name__icontains=section_q)
    if bool(course_name_q):
        course_list = course_list.filter(name__icontains=course_name_q)

    page = request.GET.get('page', 1)
    paginator = Paginator(course_list, utils.TABLE_PAGE_SIZE)

    try:
        courses = paginator.page(page)
    except PageNotAnInteger:
        courses = paginator.page(1)
    except EmptyPage:
        courses = paginator.page(paginator.num_pages)

    return render(request, 'administrators/courses/all_courses.html', {
        'loggedin_user': request.user,
        'courses': courses,
        'total_courses': len(course_list)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def create_course(request):
    ''' Create a course '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            if course:
                messages.success(request, 'Success! {0} {1} {2} {3} created'.format(course.code.name, course.number.name, course.section.name, course.term.code))
            else:
                messages.error(request, 'An error occurred while creating a course. Please contact administrators or try it again.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect(request.POST.get('next'))
    else:
        adminApi.can_req_parameters_access(request, 'none', ['next'])

    return render(request, 'administrators/courses/create_course.html', {
        'loggedin_user': request.user,
        'courses': adminApi.get_courses(),
        'form': CourseForm(),
        'next': adminApi.get_next(request)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_course(request, course_slug):
    ''' Edit a course '''
    request = userApi.has_admin_access(request)

    course = adminApi.get_course(course_slug, 'slug')
    if request.method == 'POST':

        # Check whether a next url is valid or not
        adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

        form = CourseEditForm(request.POST, instance=course)
        if form.is_valid():
            updated_course = form.save()
            if updated_course:
                messages.success(request, 'Success! {0} {1} {2} {3} updated'.format(updated_course.code.name, updated_course.number.name, updated_course.section.name, updated_course.term.code))
                return HttpResponseRedirect(request.POST.get('next'))
            else:
                messages.error(request, 'An error occurred while editing a course. Please contact administrators or try it again.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect(request.get_full_path())
    else:
        adminApi.can_req_parameters_access(request, 'none', ['next'])

    return render(request, 'administrators/courses/edit_course.html', {
        'loggedin_user': request.user,
        'course': course,
        'form': CourseEditForm(data=None, instance=course),
        'next': adminApi.get_next(request)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_course(request):
    ''' Delete a course '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        # Check whether a next url is valid or not
        adminApi.can_req_parameters_access(request, 'none', ['next'], 'POST')

        course_id = request.POST.get('course')
        deleted_course = adminApi.delete_course(course_id)
        if deleted_course:
            messages.success(request, 'Success! {0} {1} {2} {3} deleted'.format(deleted_course.code.name, deleted_course.number.name, deleted_course.section.name, deleted_course.term.code))
        else:
            messages.error(request, 'An error occurred while deleting a course. Please contact administrators or try it again.')

        return HttpResponseRedirect(request.POST.get('next'))

    return redirect("administrators:all_courses")


# ------------- Preparation -------------

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def preparation(request):
    request = userApi.has_admin_access(request)

    return render(request, 'administrators/preparation/preparation.html', {
        'loggedin_user': request.user
    })

# Terms
@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def terms(request):
    ''' Display all terms and create a term '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        form = TermForm(request.POST)
        if form.is_valid():
            term = form.save()
            if term:
                messages.success(request, 'Success! {0} ({1}) created'.format(term.name, term.code))
            else:
                messages.error(request, 'An error occurred while saving data.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return redirect('administrators:terms')

    return render(request, 'administrators/preparation/terms.html', {
        'loggedin_user': request.user,
        'terms': adminApi.get_terms(),
        'form': TermForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_term(request, term_id):
    ''' Edit a term '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        term = adminApi.get_term(term_id)
        form = TermForm(request.POST, instance=term)
        if form.is_valid():
            updated_term = form.save()
            if updated_term:
                messages.success(request, 'Success! {0} ({1}) updated'.format(updated_term.name, updated_term.code))
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))
    return redirect("administrators:terms")

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_term(request):
    ''' Delete a term '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        term_id = request.POST.get('term')
        result = adminApi.delete_term(term_id)
        if result['status'] == True:
            messages.success(request, 'Success! {0} ({1}) deleted'.format(result['term'].name, result['term'].code))
        else:
            messages.error(request, 'An error occurred. {0}'.format(result['error']))
    return redirect("administrators:terms")

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def course_codes(request):
    ''' Display all course codes and create a course code '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        form = CourseCodeForm(request.POST)
        if form.is_valid():
            course_code = form.save()
            if course_code:
                messages.success(request, 'Success! {0} created'.format(course_code.name))
            else:
                messages.error(request, 'An error occurred while saving data.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return redirect('administrators:course_codes')

    return render(request, 'administrators/preparation/course_codes.html', {
        'loggedin_user': request.user,
        'course_codes': adminApi.get_course_codes(),
        'form': CourseCodeForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_course_code(request, course_code_id):
    ''' Edit a course code '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        course_code = adminApi.get_course_code(course_code_id)
        form = CourseCodeForm(request.POST, instance=course_code)
        if form.is_valid():
            updated_course_code = form.save()
            if updated_course_code:
                messages.success(request, 'Success! {0} updated'.format(updated_course_code.name))
            else:
                messages.error(request, 'An error occurred.')
        else:
            messages.error(request, 'An error occurred.')
    return redirect('administrators:course_codes')

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_course_code(request):
    ''' Delete a course code '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        course_code_id = request.POST.get('course_code')
        result = adminApi.delete_course_code(course_code_id)
        if result['status'] == True:
            messages.success(request, 'Success! {0} deleted'.format(result['course_code'].name))
        else:
            messages.error(request, 'An error occurred. {0}'.format(result['error']))
    return redirect('administrators:course_codes')


# Course Number


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def course_numbers(request):
    ''' display course numbers'''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        form = CourseNumberForm(request.POST)
        if form.is_valid():
            course_number = form.save()
            if course_number:
                messages.success(request, 'Success! {0} created'.format(course_number.name))
            else:
                messages.error(request, 'An error occurred while saving data.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return redirect('administrators:course_numbers')

    return render(request, 'administrators/preparation/course_numbers.html', {
        'loggedin_user': request.user,
        'course_numbers': adminApi.get_course_numbers(),
        'form': CourseNumberForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_course_number(request, course_number_id):
    ''' edit a course number '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        course_number = adminApi.get_course_number(course_number_id)
        form = CourseNumberForm(request.POST, instance=course_number)
        if form.is_valid():
            updated_course_number = form.save()
            if updated_course_number:
                messages.success(request, 'Success! {0} updated'.format(updated_course_number.name))
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return redirect('administrators:course_numbers')

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_course_number(request):
    ''' delete a course number '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        course_number_id = request.POST.get('course_number')
        result = adminApi.delete_course_number(course_number_id)
        if result['status'] == True:
            messages.success(request, 'Success! {0} deleted'.format(result['course_number'].name))
        else:
            messages.error(request, 'An error occurred. {0}'.format(result['error']))
    return redirect('administrators:course_numbers')

# Course Section

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def course_sections(request):
    ''' display course sections '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        form = CourseSectionForm(request.POST)
        if form.is_valid():
            course_section = form.save()
            if course_section:
                messages.success(request, 'Success! {0} created'.format(course_section.name))
            else:
                messages.error(request, 'An error occurred while saving data.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return redirect('administrators:course_sections')

    return render(request, 'administrators/preparation/course_sections.html', {
        'loggedin_user': request.user,
        'course_sections': adminApi.get_course_sections(),
        'form': CourseSectionForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_course_section(request, course_section_id):
    ''' edit a course section '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        course_section = adminApi.get_course_section(course_section_id)
        form = CourseSectionForm(request.POST, instance=course_section)
        if form.is_valid():
            updated_course_section = form.save()
            if updated_course_section:
                messages.success(request, 'Success! {0} updated'.format(updated_course_section.name))
            else:
                messages.error(request, 'An error occurred.')
        else:
            messages.error(request, 'An error occurred.')
    return redirect('administrators:course_sections')

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_course_section(request):
    ''' delete a course section '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        course_section_id = request.POST.get('course_section')
        result = adminApi.delete_course_section(course_section_id)
        if result['status'] == True:
            messages.success(request, 'Success! {0} deleted'.format(result['course_section'].name))
        else:
            messages.error(request, 'An error occurred. {0}'.format(result['error']))
    return redirect('administrators:course_sections')


# Statuses

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def statuses(request):
    ''' Display all statuses and create a status '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        form = StatusForm(request.POST)
        if form.is_valid():
            status = form.save()
            if status:
                messages.success(request, 'Success! {0} created'.format(status.name))
            else:
                messages.error(request, 'An error occurred while saving data.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return redirect('administrators:statuses')

    return render(request, 'administrators/preparation/statuses.html', {
        'loggedin_user': request.user,
        'statuses': userApi.get_statuses(),
        'form': StatusForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_status(request, slug):
    ''' Edit a status '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        status = userApi.get_status_by_slug(slug)
        form = StatusForm(request.POST, instance=status)
        if form.is_valid():
            updated_status = form.save()
            if updated_status:
                messages.success(request, 'Success! {0} updated'.format(updated_status.name))
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))
    return redirect("administrators:statuses")

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_status(request):
    ''' Delete a status '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        status_id = request.POST.get('status')
        deleted_status = userApi.delete_status(status_id)
        if deleted_status:
            messages.success(request, 'Success! {0} deleted'.format(deleted_status.name))
        else:
            messages.error(request, 'An error occurred.')
    return redirect("administrators:statuses")


# Faculties


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def faculties(request):
    ''' Display all faculties and create a faculty '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        form = FacultyForm(request.POST)
        if form.is_valid():
            faculty = form.save()
            if faculty:
                messages.success(request, 'Success! {0} created'.format(faculty.name))
            else:
                messages.error(request, 'An error occurred while saving data.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return redirect('administrators:faculties')

    return render(request, 'administrators/preparation/faculties.html', {
        'loggedin_user': request.user,
        'faculties': userApi.get_faculties(),
        'form': FacultyForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_faculty(request, slug):
    ''' Edit a faculty '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        faculty = userApi.get_faculty_by_slug(slug)
        form = FacultyForm(request.POST, instance=faculty)
        if form.is_valid():
            updated_faculty = form.save()
            if updated_faculty:
                messages.success(request, 'Success! {0} updated'.format(updated_faculty.name))
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))
    return redirect("administrators:faculties")

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_faculty(request):
    ''' Delete a faculty '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        faculty_id = request.POST.get('faculty')
        deleted_faculty = userApi.delete_faculty(faculty_id)
        if deleted_faculty:
            messages.success(request, 'Success! {0} deleted'.format(deleted_faculty.name))
        else:
            messages.error(request, 'An error occurred.')
    return redirect("administrators:faculties")


# Programs


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def programs(request):
    ''' Display all programs and create a program '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        form = ProgramForm(request.POST)
        if form.is_valid():
            program = form.save()
            if program:
                messages.success(request, 'Success! {0} created'.format(program.name))
            else:
                messages.error(request, 'An error occurred while saving data.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return redirect('administrators:programs')

    return render(request, 'administrators/preparation/programs.html', {
        'loggedin_user': request.user,
        'programs': userApi.get_programs(),
        'form': ProgramForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_program(request, slug):
    ''' Edit a program '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        program = userApi.get_program_by_slug(slug)
        form = ProgramForm(request.POST, instance=program)
        if form.is_valid():
            updated_program = form.save()
            if updated_program:
                messages.success(request, 'Success! {0} updated'.format(updated_program.name))
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))
    return redirect("administrators:programs")

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_program(request):
    ''' Delete a program '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        program_id = request.POST.get('program')
        deleted_program = userApi.delete_program(program_id)
        if deleted_program:
            messages.success(request, 'Success! {0} deleted'.format(deleted_program.name))
        else:
            messages.error(request, 'An error occurred.')
    return redirect("administrators:programs")


# Degrees

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def degrees(request):
    ''' Display all degrees and create a degree '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        form = DegreeForm(request.POST)
        if form.is_valid():
            degree = form.save()
            if degree:
                messages.success(request, 'Success! {0} created'.format(degree.name))
            else:
                messages.error(request, 'An error occurred while saving data.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return redirect('administrators:degrees')

    return render(request, 'administrators/preparation/degrees.html', {
        'loggedin_user': request.user,
        'degrees': userApi.get_degrees(),
        'form': DegreeForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_degree(request, slug):
    ''' Edit a degree '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        degree = userApi.get_degree_by_slug(slug)
        form = DegreeForm(request.POST, instance=degree)
        if form.is_valid():
            updated_degree = form.save()
            if updated_degree:
                messages.success(request, 'Success! {0} updated'.format(updated_degree.name))
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return redirect("administrators:degrees")

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_degree(request):
    ''' Delete a degree '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        degree_id = request.POST.get('degree')
        deleted_degree = userApi.delete_degree(degree_id)
        if deleted_degree:
            messages.success(request, 'Success! {0} deleted'.format(deleted_degree.name))
        else:
            messages.error(request, 'An error occurred.')
    return redirect("administrators:degrees")


# Trainings

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def trainings(request):
    ''' Display all trainings and create a training '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        form = TrainingForm(request.POST)
        if form.is_valid():
            training = form.save()
            if training:
                messages.success(request, 'Success! {0} created'.format(training.name))
            else:
                messages.error(request, 'An error occurred while saving data.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return redirect('administrators:trainings')

    return render(request, 'administrators/preparation/trainings.html', {
        'loggedin_user': request.user,
        'trainings': userApi.get_trainings(),
        'form': TrainingForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_training(request, slug):
    ''' Edit a training '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        training = userApi.get_training_by_slug(slug)
        form = TrainingForm(request.POST, instance=training)
        if form.is_valid():
            updated_training = form.save()
            if updated_training:
                messages.success(request, 'Success! {0} updated'.format(updated_training.name))
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))
    return redirect("administrators:trainings")

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_training(request):
    ''' Delete a training '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        training_id = request.POST.get('training')
        deleted_training = userApi.delete_training(training_id)
        if deleted_training:
            messages.success(request, 'Success! {0} deleted'.format(deleted_training.name))
        else:
            messages.error(request, 'An error occurred.')
    return redirect("administrators:trainings")


# classification


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def classifications(request):
    ''' Display all classifications and create a classification '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        form = ClassificationForm(request.POST)
        if form.is_valid():
            classification = form.save()
            if classification:
                messages.success(request, 'Success! {0} {1} created'.format(classification.year, classification.name))
            else:
                messages.error(request, 'An error occurred while saving data.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return redirect('administrators:classifications')

    return render(request, 'administrators/preparation/classifications.html', {
        'loggedin_user': request.user,
        'classifications': adminApi.get_classifications('all'),
        'form': ClassificationForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_classification(request, slug):
    ''' Edit a classification '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        classification = adminApi.get_classification_by_slug(slug)
        form = ClassificationForm(request.POST, instance=classification)
        if form.is_valid():
            updated_classification = form.save()
            if updated_classification:
                messages.success(request, 'Success! {0} {1} updated'.format(updated_classification.year, updated_classification.name))
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

    return redirect("administrators:classifications")

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_classification(request):
    ''' Delete a classification '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        classification_id = request.POST.get('classification')
        deleted_classification = adminApi.delete_classification(classification_id)
        if deleted_classification:
            messages.success(request, 'Success! {0} deleted'.format(deleted_classification.name))
        else:
            messages.error(request, 'An error occurred.')
    return redirect("administrators:classifications")


# Roles

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def roles(request):
    ''' Display all roles and create a role '''
    request = userApi.has_superadmin_access(request)

    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            role = form.save()
            if role:
                messages.success(request, 'Success! {0} has been created'.format(role.name))
            else:
                messages.error(request, 'An error occurred while saving data.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return redirect('administrators:roles')

    return render(request, 'administrators/hr/roles.html', {
        'loggedin_user': request.user,
        'roles': userApi.get_roles(),
        'form': RoleForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def edit_role(request, slug):
    ''' Edit a role '''
    request = userApi.has_superadmin_access(request)

    if request.method == 'POST':
        role = userApi.get_role_by_slug(slug)
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            updated_role = form.save()
            if updated_role:
                messages.success(request, 'Success! {0} has been updated'.format(updated_role.name))
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))
    return redirect("administrators:roles")

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_role(request):
    ''' Delete a role '''
    request = userApi.has_superadmin_access(request)

    if request.method == 'POST':
        role_id = request.POST.get('role')
        deleted_role = userApi.delete_role(role_id)
        if deleted_role:
            messages.success(request, 'Success! {0} has been deleted'.format(deleted_role.name))
        else:
            messages.error(request, 'An error occurred.')
    return redirect("administrators:roles")


# Admin emails

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def admin_emails(request):
    ''' Display all roles and create a role '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        form = AdminEmailForm(request.POST)
        if form.is_valid():
            admin_email = form.save()
            if admin_email:
                messages.success(request, 'Success! {0} created'.format(admin_email.type))
            else:
                messages.error(request, 'An error occurred while saving data.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return redirect('administrators:admin_emails')

    return render(request, 'administrators/preparation/admin_emails.html', {
        'loggedin_user': request.user,
        'admin_emails': adminApi.get_admin_emails(),
        'form': AdminEmailForm()
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_admin_email(request, slug):
    ''' Edit a admin_email '''
    request = userApi.has_admin_access(request)

    admin_email = adminApi.get_admin_email_by_slug(slug)
    if request.method == 'POST':
        form = AdminEmailForm(request.POST, instance=admin_email)
        if form.is_valid():
            updated_admin_email = form.save(commit=False)
            updated_admin_email.updated_at = datetime.now()
            updated_admin_email.save()
            if updated_admin_email:
                messages.success(request, 'Success! {0} updated'.format(updated_admin_email.type))
                return redirect("administrators:admin_emails")
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect( reverse('administrators:edit_admin_email', args=[slug]) )

    return render(request, 'administrators/preparation/edit_admin_email.html', {
        'loggedin_user': request.user,
        'form': AdminEmailForm(data=None, instance=admin_email)
    })

@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_admin_email(request):
    ''' Delete a admin_email '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        admin_email_id = request.POST.get('admin_email')
        deleted_admin_email = adminApi.delete_admin_email(admin_email_id)
        if deleted_admin_email:
            messages.success(request, 'Success! {0} deleted'.format(deleted_admin_email.type))
        else:
            messages.error(request, 'An error occurred.')
    return redirect("administrators:admin_emails")


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def landing_pages(request):
    ''' View a landing page '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        form = LandingPageForm(request.POST)
        if form.is_valid():
            landing_page = form.save()
            if landing_page:
                messages.success(request, 'Success! New landing Page (ID: {0}) created.'.format(landing_page.id))
            else:
                messages.error(request, 'An error occurred while saving data.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return redirect('administrators:landing_pages')

    return render(request, 'administrators/preparation/landing_pages.html', {
        'loggedin_user': request.user,
        'landing_pages': adminApi.get_landing_pages(),
        'form': LandingPageForm()
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def edit_landing_page(request, landing_page_id):
    ''' Edit a landing page '''
    request = userApi.has_admin_access(request)

    landing_page = adminApi.get_landing_page(landing_page_id)
    if request.method == 'POST':
        form = LandingPageForm(request.POST, instance=landing_page)
        if form.is_valid():
            updated_landing_page = form.save(commit=False)
            updated_landing_page.updated_at = datetime.now()
            updated_landing_page.save()
            if updated_landing_page:
                messages.success(request, 'Success! Landing Page (ID: {0}) updated'.format(updated_landing_page.id))
                return redirect("administrators:landing_pages")
            else:
                messages.error(request, 'An error occurred.')
        else:
            errors = form.errors.get_json_data()
            messages.error(request, 'An error occurred. Form is invalid. {0}'.format( userApi.get_error_messages(errors) ))

        return HttpResponseRedirect( reverse('administrators:edit_landing_page', args=[landing_page_id]) )

    return render(request, 'administrators/preparation/edit_landing_page.html', {
        'loggedin_user': request.user,
        'form': LandingPageForm(data=None, instance=landing_page)
    })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['POST'])
def delete_landing_page(request):
    ''' Delete a landing page '''
    request = userApi.has_admin_access(request)

    if request.method == 'POST':
        landing_page = adminApi.get_landing_page( request.POST.get('landing_page') )
        landing_page.delete()

        if landing_page:
            messages.success(request, 'Success! Landing Page {0} deleted'.format(landing_page.title))
        else:
            messages.error(request, 'An error occurred.')
    return redirect("administrators:landing_pages")


# Utils

def valid_worktag_setting(request):
    valid_programs = [
        ('program1', 'Program 1'), 
        ('hours1', 'Program 1 Hours'), 
        ('program2', 'Program 2'), 
        ('hours2', 'Program 2 Hours'), 
        ('total_hours', 'Total Hours')
    ]
    for field in valid_programs:
        if not request.POST.get(field[0], None):
            messages.error(request, 'An error occurred. This <strong>{0}</strong> field is required. Please try again.'.format(field[1]))
            return False
    
    if request.POST['program1'] == request.POST['program2']:
        return False
    
    return True


def get_worktag(request):
    jid = request.POST['job']
    aid = request.POST.get('application', None)
    
    program1 = request.POST['program1'].split('-')
    code1 = program1[1]
    hours1 = request.POST['hours1']
    program2 = request.POST['program2'].split('-')
    code2 = program2[1]
    hours2 = request.POST['hours2']
    total_hours = request.POST['total_hours']
    program_info = {
        'name1': program1[0],
        'code1': program1[1],
        'hours1': hours1,
        'name2': program2[0],
        'code2': program2[1],
        'hours2': hours2,
        'total_hours': total_hours
    }

    p1_percentage = round(int(hours1) / int(total_hours) * 100, 1)
    p2_percentage = round(int(hours2) / int(total_hours) * 100, 1)
    worktag = '{0}% {1}, {2}% {3}'.format(p1_percentage, code1, p2_percentage, code2)
    
    return jid, aid, program_info, worktag
