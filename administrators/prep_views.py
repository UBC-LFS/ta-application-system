from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_http_methods
from datetime import datetime

from administrators.forms import (
    TermForm,
    CourseCodeForm,
    CourseNumberForm,
    CourseSectionForm,
    ClassificationForm,
    AdminEmailForm,
    LandingPageForm
)
from administrators import api as adminApi
from users.forms import (
    StatusForm,
    FacultyForm,
    ProgramForm,
    DegreeForm,
    TrainingForm
)
from users import api as userApi


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

