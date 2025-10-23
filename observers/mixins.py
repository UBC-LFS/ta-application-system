from django.conf import settings
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.urls import resolve
from urllib.parse import urlparse
from django.http import Http404
from datetime import date
from users.models import Role

from administrators import api as adminApi
from users import api as userApi


class AcceptedAppsReportMixin:
    ''' Display a report of applications accepted by students for Observer '''

    @method_decorator(require_GET)
    def get(self, request, *args, **kwargs):
        parsed_full_path = urlparse(request.get_full_path())
        app_name = resolve(parsed_full_path.path).app_names[0]

        template = '/accepted_apps_report_observer.html'
        if app_name == 'observers':
            request = userApi.has_user_access(request, utils.OBSERVER)
            template = app_name + template
        elif app_name == 'administrators':
            request = userApi.has_admin_access(request, utils.HR)
            template = app_name + '/applications' + template

        app_list = adminApi.get_filtered_accepted_apps()

        year_term = request.GET.get('year_term')
        course = request.GET.get('course', '').strip()
        instructor = request.GET.get('instructor', '').strip()
        first_name = request.GET.get('first_name', '').strip()
        last_name = request.GET.get('last_name', '').strip()
        student_number = request.GET.get('student_number', '').strip()
        
        sort_column = request.GET.get('sort_column', None)
        sort_order = request.GET.get('sort_order', None)
    
        if bool(year_term):
            year_term_sp = year_term.split('_')
            app_list = app_list.filter(job__session__year__iexact=year_term_sp[0], job__session__term__code__iexact=year_term_sp[1])

        if bool(course):
            course_sp = course.split(' ')
            if len(course_sp) == 1:
                app_list = app_list.filter( Q(job__course__code__name__icontains=course) | Q(job__course__number__name__icontains=course) | Q(job__course__section__name__icontains=course))
            elif len(course_sp) == 2:
                app_list = app_list.filter( Q(job__course__code__name__icontains=course_sp[0]) & Q(job__course__number__name__icontains=course_sp[1]))
            elif len(course_sp) == 3:
                app_list = app_list.filter( Q(job__course__code__name__icontains=course_sp[0]) & Q(job__course__number__name__icontains=course_sp[1]) & Q(job__course__section__name__icontains=course_sp[2]))
            else:
                app_list = []
        
        if bool(instructor):
            instructor_sp = instructor.split(' ')    
            if len(instructor_sp) == 1:
                app_list = app_list.filter( Q(job__instructors__first_name__icontains=instructor) | Q(job__instructors__last_name__icontains=instructor) )
            elif len(instructor_sp) == 2:
                app_list = app_list.filter( Q(job__instructors__first_name__icontains=instructor_sp[0]) & Q(job__instructors__last_name__icontains=instructor_sp[1]) )
            else:
                app_list = []
        
        if bool(first_name):
            app_list = app_list.filter(applicant__first_name__icontains=first_name)
        if bool(last_name):
            app_list = app_list.filter(applicant__last_name__icontains=last_name)
        if bool(student_number):
            app_list = app_list.filter(applicant__profile__student_number__icontains=student_number)
        
        total_apps = len(app_list)
        
        if sort_column and sort_order:
            if sort_column == 'instructors':
                if sort_order == 'asc':
                    app_list = app_list.order_by('job__instructors__first_name', 'job__instructors__last_name', 'id')
                elif sort_order == 'desc':
                    app_list = app_list.order_by('-job__instructors__first_name', '-job__instructors__last_name', '-id')
            else:
                field = 'applicant__' + sort_column
                if sort_column == 'year' or sort_column == 'term':
                    field = 'job__session__' + sort_column
                elif sort_column == 'course':
                    field = 'job__' + sort_column
                elif sort_column == 'student_number':
                    field = 'applicant__profile__' + sort_column
                
                if sort_order == 'desc':
                    field = '-' + field

                if sort_order == 'asc':
                    app_list = app_list.order_by(field, 'id')
                elif sort_order == 'desc':
                    app_list = app_list.order_by(field, '-id')

        page = request.GET.get('page', 1)
        paginator = Paginator(app_list, settings.PAGE_SIZE)

        try:
            apps = paginator.page(page)
        except PageNotAnInteger:
            apps = paginator.page(1)
        except EmptyPage:
            apps = paginator.page(paginator.num_pages)

        table_columns = [
            {'name': 'Year', 'sort_name': 'year'},
            {'name': 'Term', 'sort_name': 'term'},
            {'name': 'Course (Job)', 'sort_name': 'course'},
            {'name': 'Instructors', 'sort_name': 'instructors'},
            {'name': 'First Name', 'sort_name': 'first_name'},
            {'name': 'Last Name', 'sort_name': 'last_name'},
            {'name': 'CWL', 'sort_name': 'username'},
            {'name': 'Student Number', 'sort_name': 'student_number'},
            {'name': 'Email', 'sort_name': 'email'}
        ]

        for col in table_columns:
            order = None
            if sort_column == col['sort_name']:
                if sort_order:
                    order = 'desc' if sort_order == 'asc' else 'asc'
                else:
                    order = 'asc'
            else:
                order = 'asc'
            col['sort_order'] = order
        
        sessions = adminApi.get_sessions().filter(year__gte=date.today().year - 5)
        for session in sessions:
            session.year_term = '{0}_{1}'.format(session.year, session.term.code)

        query_sp = parsed_full_path.query.split('&sort_column=')
        if len(query_sp) == 0:
            raise Http404
        
        return render(request, template, context={
            'total_apps': total_apps,
            'apps': apps,
            'table_columns': table_columns,
            'sort_order': sort_order,
            'sessions': sessions,
            'url': '{0}?{1}'.format(parsed_full_path.path, query_sp[0])
        })