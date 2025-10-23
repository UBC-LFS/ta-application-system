from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET
from django.http import Http404
from django.core.exceptions import SuspiciousOperation
from django.db.models import Q, Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import resolve
from urllib.parse import urlparse

from ta_app import utils
from administrators import api as adminApi
from users import api as userApi


class SummaryApplicantsMixin:

    def setup(self, request, *args, **kwargs):
        setup = super().setup(request, *args, **kwargs)

        parsed = urlparse(request.get_full_path())
        resolved = resolve(parsed.path)

        if len(resolved.app_names) == 0:
            raise SuspiciousOperation

        session_slug = kwargs.get('session_slug', None)
        job_slug = kwargs.get('job_slug', None)
        if not session_slug or not job_slug:
            raise Http404

        self.app_name = resolved.app_names[0]
        self.session = adminApi.get_session(session_slug, 'slug')
        self.job = adminApi.get_job_by_session_slug_job_slug(session_slug, job_slug)

        return setup

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        if self.app_name == 'instructors':
            request = userApi.has_user_access(request, utils.INSTRUCTOR)
        elif self.app_name == 'administrators':
            request = userApi.has_admin_access(request)

        # session_term = session.year + '_' + session.term.code
        # course = job.course.code.name + '_' + job.course.number.name + '_' + job.course.section.name

        applicants = adminApi.get_applicants_in_session(self.session)
        total_applicants = applicants.count()

        if bool( request.GET.get('first_name') ):
            applicants = applicants.filter(first_name__icontains=request.GET.get('first_name'))
        if bool( request.GET.get('last_name') ):
            applicants = applicants.filter(last_name__icontains=request.GET.get('last_name'))
        if bool( request.GET.get('cwl') ):
            applicants = applicants.filter(username__icontains=request.GET.get('cwl'))
        if bool( request.GET.get('student_number') ):
            applicants = applicants.filter(profile__student_number__icontains=request.GET.get('student_number'))

        no_offers_applicants = []
        for applicant in applicants:
            appls = applicant.application_set.filter( Q(job__session__year=self.session.year) & Q(job__session__term__code=self.session.term.code) )

            count_offered_apps = Count('applicationstatus', filter=Q(applicationstatus__assigned=utils.OFFERED))
            offered_apps = appls.annotate(count_offered_apps=count_offered_apps).filter(count_offered_apps__gt=0)

            applicant.no_offers = False
            if len(offered_apps) == 0:
                no_offers_applicants.append(applicant)
                applicant.no_offers = True

        if bool( request.GET.get('no_offers') ):
            applicants = no_offers_applicants

        searched_total_applicants = len(applicants)

        page = request.GET.get('page', 1)
        paginator = Paginator(applicants, 25)

        try:
            applicants = paginator.page(page)
        except PageNotAnInteger:
            applicants = paginator.page(1)
        except EmptyPage:
            applicants = paginator.page(paginator.num_pages)

        for applicant in applicants:

            # To check whether an alert email has been sent to an applicant
            applicant.is_sent_alertemail = False
            is_sent_alertemail = request.user.alertemail_set.filter(
                Q(year = self.job.session.year) & Q(term = self.job.session.term.code) &
                Q(job_code = self.job.course.code.name) & Q(job_number = self.job.course.number.name) & Q(job_section = self.job.course.section.name) &
                Q(receiver_name = applicant.get_full_name()) & Q(receiver_email = applicant.email)
            )
            if is_sent_alertemail.count() > 0:
                applicant.is_sent_alertemail = True

            has_applied = False
            apps = applicant.application_set.filter( Q(job__session__year=self.session.year) & Q(job__session__term__code=self.session.term.code) )
            applicant.apps = []
            for app in apps:
                app = adminApi.add_app_info_into_application(app, ['applied', 'accepted', 'declined', 'cancelled'])
                app_obj = {
                    'course': app.job.course.code.name + ' ' + app.job.course.number.name + ' ' + app.job.course.section.name,
                    'applied': app.applied,
                    'accepted': None,
                    'has_applied': False
                }
                if adminApi.check_valid_accepted_app_or_not(app):
                    app_obj['accepted'] = app.accepted

                applicant.apps.append(app_obj)

                # To check whether an application of this user has been applied already
                if (app.job.course.code.name == self.job.course.code.name) and (app.job.course.number.name == self.job.course.number.name) and (app.job.course.section.name == self.job.course.section.name):
                    has_applied = True
                    app_obj['has_applied'] = True

                applicant.has_applied = has_applied

        template = '{0}/jobs/summary_applicants.html'.format(self.app_name)

        context = {
            'loggedin_user': request.user,
            'session': self.session,
            'job': self.job,
            'total_applicants': total_applicants,
            'total_no_offers_applicants': len(no_offers_applicants),
            'applicants': applicants,
            'searched_total_applicants': searched_total_applicants
        }

        if self.app_name == 'instructors':
            context['next_second'] = request.session.get('next_second', None)
            context['new_next'] = adminApi.build_new_next(request)

        elif self.app_name == 'administrators':
            context['next'] = request.session.get('summary_applicants_next')

        return render(request, template, context)
