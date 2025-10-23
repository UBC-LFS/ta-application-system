from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404
from django.views.decorators.cache import cache_control, never_cache
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import date, datetime
import copy

from ta_app import utils
from administrators.models import Session, Job
from administrators.forms import SessionForm, SessionConfirmationForm
from administrators import api as adminApi
from users import api as userApi


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
