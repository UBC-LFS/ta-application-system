import os
from django.conf import settings
from django.shortcuts import render
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.views.decorators.cache import cache_control, never_cache
from io import StringIO
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.html import strip_tags
from datetime import datetime

from ta_app import utils
from administrators.models import Application, ApplicationStatus, ApplicationReset, WorktagSetting
from administrators.forms import (
    InstructorApplicationForm,
    ApplicationStatusForm,
    AdminApplicationForm,
    AdminDocumentsForm,
    ReminderForm,
    ApplicationStatusReassignForm,
    ReassignApplicationForm,
    TerminateApplicationForm,
    EmailForm
)
from administrators import api as adminApi
from users import api as userApi
from observers.mixins import AcceptedAppsReportMixin


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
        request = userApi.has_admin_access(request, utils.HR)
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
            'app_status': utils.APP_STATUS,
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
            # app.applicant.gta = userApi.get_gta_flag(app.applicant)
            app.can_reset = adminApi.app_can_reset(app)
            app.confi_info_expiry_status = userApi.get_confidential_info_expiry_status(app.applicant)

        return render(request, 'administrators/applications/all_applications.html', {
            'loggedin_user': request.user,
            'apps': apps,
            'num_filtered_apps': info['num_filtered_apps'],
            'app_status': utils.APP_STATUS,
            'new_next': adminApi.build_new_next(request),
            'this_year': utils.THIS_YEAR,
            'download_preferred_candidates_url': reverse('administrators:download_preferred_candidates')
        })


@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET'])
def download_preferred_candidates(request):
    app_list, _ = adminApi.get_applications_filter_limit(request, 'all')

    apps = []
    usernames = []
    for app in app_list:
        if userApi.get_preferred_candidate(app.applicant, app.job.session.year) and app.applicant.username not in usernames:
            apps.append(app)
            usernames.append(app.applicant.username)

    result = 'Year,First Name,Last Name,CWL,Student Number,Status,LFS Grad or Others,Program,Other Program,Faculty,Student Year,Previous Year - Accepted Hours\n'

    sorted_apps = sorted(apps, key=lambda x: x.applicant.first_name)
    for app in sorted_apps:
        student_number = ''
        status = ''
        student_year = ''
        program = ''
        program_others = ''
        if userApi.profile_exists(app.applicant):
            if app.applicant.profile.student_number:
                student_number = app.applicant.profile.student_number

            if app.applicant.profile.status:
                status = app.applicant.profile.status.name

            if app.applicant.profile.student_year:
                student_year = app.applicant.profile.student_year

            if app.applicant.profile.program:
                program = app.applicant.profile.program.name

            if app.applicant.profile.program_others:
                program_others = app.applicant.profile.program_others.replace('&nbsp;', ' ').replace(',', "")
                program_others = strip_tags(program_others)

            if app.applicant.profile.faculty:
                faculty = app.applicant.profile.faculty.name

        lfs_grad_or_others = userApi.get_lfs_grad_or_others(app.applicant)
        prev_year_accepted_hours = adminApi.get_accepted_hours_from_previous_year(app.applicant, app.job.session.year)

        result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11}\n'.format(
            app.job.session.year,
            app.applicant.first_name,
            app.applicant.last_name,
            app.applicant.username,
            student_number,
            status,
            lfs_grad_or_others,
            program,
            program_others,
            faculty,
            student_year,
            float(prev_year_accepted_hours)
        )

    return JsonResponse({ 'status': 'success', 'data': result })


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
        app_status_form = ApplicationStatusForm({ 'application': app_id, 'assigned': utils.NONE, 'assigned_hours': '0', 'has_contract_read': False })
        if app_status_form:
            updated_app = adminApi.update_reset_application(app_id, instructor_preference)
            if updated_app:
                if app_status_form.save():
                    app_reset = ApplicationReset.objects.create(application=app, user=request.user.get_full_name())
                    if app_reset:
                        messages.success(request, 'Success! {0} - the following information (ID: {1}, {2} {3} - {4} {5} {6}) have been reset. <ul><li>Instructor Preference</li><li>Assigned Status</li><li>Assigned Hours</li><li>STA option</li></ul>'.format(updated_app.applicant.get_full_name(), updated_app.id, updated_app.job.session.year, updated_app.job.session.term.code, updated_app.job.course.code.name, updated_app.job.course.number.name, updated_app.job.course.section.name))
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
            num_offers = app.applicationstatus_set.filter(assigned=utils.OFFERED).count()

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
            'app_status': utils.APP_STATUS,
            'new_next': adminApi.build_new_next(request),
            'this_year': utils.THIS_YEAR,
            'worktags': settings.WORKTAGS,
            'save_worktag_setting_url': request.get_full_path(),
            'delete_worktag_setting_url': reverse('administrators:delete_app_worktag_setting')
        })

    @method_decorator(require_POST)
    def post(self, request, *args, **kwargs):
        is_valid = adminApi.valid_worktag_setting(request)
        if is_valid:
            jid, aid, program_info, worktag = adminApi.get_worktag(request)
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
        request = userApi.has_admin_access(request, utils.HR)

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
        request = userApi.has_admin_access(request, utils.HR)

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
def download_accepted_apps_workday(request):
    ''' Download accepted applications for Workday '''

    apps, total_apps = adminApi.get_accepted_app_report(request)
    data = []
    for app in apps:
        app = adminApi.make_workday_data(app)

        instructors = ''
        if app.job.instructors.count() > 0:
            for i, ins in enumerate(app.job.instructors.all()):
                instructors += ins.get_full_name()
                if i < app.job.instructors.count() - 1:
                    instructors += ', '

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
            'Instructor(s)': instructors,
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
            'app_status': utils.APP_STATUS,
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
        email_list = email_list.filter(application__applicationstatus__assigned=utils.OFFERED).filter( ~Q(application__applicationstatus__assigned=utils.ACCEPTED) & ~Q(application__applicationstatus__assigned=utils.DECLINED) ).order_by('-id').distinct()

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
        accepted_status = app.applicationstatus_set.filter(assigned=utils.ACCEPTED).last()

        status_form = ApplicationStatusReassignForm({
            'application': app_id,
            'assigned': utils.DECLINED,
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
            'app_status': utils.APP_STATUS,
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
        request = userApi.has_admin_access(request, utils.HR)

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
            app.weekly_hours = adminApi.calculate_weekly_hours(pt_percentage)

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

            prev_year_apps = app.applicant.application_set.filter(
                job__session__year = int(app.job.session.year) - 1,
                job__session__term__code = app.job.session.term.code
            )

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

    result = 'ID,Year,Term,Job,First Name,Last Name,Full Name,CWL,Email,Student Number,Employee Number,Classification,Monthly Salary,P/T (%),Positin Number,PIN,TASM,Processed,Worktag,Processing Note,Accepted on,Assigned Hours\n'
    for app in apps:
        year = app.job.session.year
        term = app.job.session.term.code
        job = '{0} {1} {2}'.format(app.job.course.code.name, app.job.course.number.name, app.job.course.section.name)
        first_name = app.applicant.first_name
        last_name = app.applicant.last_name
        full_name = f'{app.applicant.first_name} {app.applicant.last_name}'
        cwl = app.applicant.username
        email = app.applicant.email

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

        result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19},{20},{21}\n'.format(
            app.id,
            year,
            term,
            job,
            first_name,
            last_name,
            full_name,
            cwl,
            email,
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

    apps, _ = adminApi.get_accepted_app_report(request)
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
