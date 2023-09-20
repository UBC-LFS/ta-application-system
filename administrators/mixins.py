from django.conf import settings
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import SuspiciousOperation
from django.urls import resolve
from urllib.parse import urlparse

from users.models import Role

from administrators import api as adminApi
from users import api as userApi

from datetime import date


class AcceptedAppsReportMixin:

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        parsed = urlparse(request.get_full_path())
        url_name = resolve(parsed.path).url_name

        template = 'administrators/applications/accepted_app_report_{0}.html'
        
        if url_name == 'accepted_apps_report_admin':
            template = template.format('admin')
        elif url_name == 'accepted_apps_report_observer':
            template = template.format('observer')
        else:
            raise SuspiciousOperation

        request = userApi.has_admin_access(request, Role.HR)
        
        apps, total_apps = adminApi.get_accepted_app_report(request)
        
        page = request.GET.get('page', 1)
        #paginator = Paginator(apps, settings.PAGE_SIZE)
        paginator = Paginator(apps, 20)

        try:
            apps = paginator.page(page)
        except PageNotAnInteger:
            apps = paginator.page(1)
        except EmptyPage:
            apps = paginator.page(paginator.num_pages)

        for app in apps:
            if url_name == 'accepted_apps_report_admin':
                app = adminApi.add_app_info_into_application(app, ['accepted'])
                app.salary = adminApi.calcualte_salary(app)
                pt_percentage = adminApi.calculate_pt_percentage(app)
                app.pt_percentage = pt_percentage
                app.weekly_hours = pt_percentage / 100 * 12

                app.prev_accepted_apps = None
                prev_apps = app.applicant.application_set.filter(job__session__year__lt=app.job.session.year).exclude(id=app.id)
                total_assigned_hours = 0
                if prev_apps.exists():
                    prev_accepted_apps = adminApi.get_accepted_apps_not_terminated(prev_apps)
                    prev_accepted_apps = adminApi.get_filtered_accepted_apps(prev_accepted_apps)
                    for ap in prev_accepted_apps:
                        ap = adminApi.add_app_info_into_application(ap, ['accepted'])
                        total_assigned_hours += ap.accepted.assigned_hours
                    
                    app.prev_accepted_apps = prev_accepted_apps
                    app.total_assigned_hours = total_assigned_hours
                
                lfs_grad_or_others = userApi.get_lfs_grad_or_others(app.applicant)
                app.lfs_grad_or_others = lfs_grad_or_others

                is_preferred_student = False
                if total_assigned_hours > 0 and lfs_grad_or_others == 'LFS GRAD':
                    is_preferred_student = True
                
                app.is_preferred_student = is_preferred_student


                status = { 'sin': None, 'study_permit': None }
                for st in userApi.get_confidential_info_expiry_status(app.applicant):
                    if st['doc'] == 'SIN':
                        status['sin'] = st['status'].upper()
                    elif st['doc'] == 'Study Permit':
                        status['study_permit'] = st['status'].upper()
                
                app.confi_info_expiry_status = status
        
        context= {
            'total_apps': total_apps,
            'apps': apps
        }

        if url_name == 'accepted_apps_report_admin':
            context['download_all_accepted_apps_report_admin_url'] = reverse('administrators:download_all_accepted_apps_report_admin')
        
        return render(request, template, context=context)

