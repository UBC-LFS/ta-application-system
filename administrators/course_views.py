from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from ta_app import utils
from administrators.forms import CourseForm, CourseEditForm
from administrators import api as adminApi
from users import api as userApi


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
