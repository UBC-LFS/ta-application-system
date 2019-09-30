from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.contrib.messages import get_messages
from urllib.parse import urlencode
from django.core import mail

from administrators.models import *
from users.models import *
from administrators import api as adminApi
from users import api as userApi

ContentType='application/x-www-form-urlencoded'

DATA = [
    'administrators/fixtures/applications.json',
    'administrators/fixtures/applicationstatus.json',
    'administrators/fixtures/classifications.json',
    'administrators/fixtures/course_codes.json',
    'administrators/fixtures/course_numbers.json',
    'administrators/fixtures/course_sections.json',
    'administrators/fixtures/courses.json',
    'administrators/fixtures/emails.json',
    'administrators/fixtures/job_instructors.json',
    'administrators/fixtures/jobs.json',
    'administrators/fixtures/sessions.json',
    'administrators/fixtures/terms.json',
    'users/fixtures/degrees.json',
    'users/fixtures/profile_roles.json',
    'users/fixtures/profiles.json',
    'users/fixtures/programs.json',
    'users/fixtures/roles.json',
    'users/fixtures/statuses.json',
    'users/fixtures/trainings.json',
    'users/fixtures/users.json'
]

class HRTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        print('\nAdministrators:hr testing has started ==>')

    def login(self, username, password):
        self.client.post('/accounts/local_login/', data={'username': username, 'password': password})

    def messages(self, res):
        return [m.message for m in get_messages(res.wsgi_request)]

    def test_view_url_exists_at_desired_location(self):
        print('\n- Test: view url exists at desired location')
        self.login('admin', '12')

        response = self.client.get( reverse('administrators:hr') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:users') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:create_user') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:view_confidentiality', args=['admin', 'administrator']) )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:show_user', args=['admin', 'administrator']) )
        self.assertEqual(response.status_code, 200)

    def test_get_users(self):
        print('\n- Test: get all users')
        self.login('admin', '12')
        response = self.client.get(reverse('administrators:users'))
        self.assertEqual(len(response.context['users']), 30) # 30 users

    def test_create_user_with_no_profile_in_view(self):
        print('\n- Test: create a user with no profile')
        self.login('admin', '12')
        data = {
            'first_name': 'test',
            'last_name': 'user100',
            'email': 'test.user100@example.com',
            'username': 'test.user100',
            'password': '12'
        }

        self.assertFalse(userApi.username_exists(data['username']))
        self.assertFalse(userApi.profile_exists_by_username(data['username']))

        response = self.client.post(reverse('administrators:create_user'), data=urlencode(data), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

    def test_create_user_in_view(self):
        print('\n- Test: create a user')
        self.login('admin', '12')
        data = {
            'first_name': 'test',
            'last_name': 'user100',
            'email': 'test.user100@example.com',
            'username': 'test.user100',
            'password': '12',
            'preferred_name': None,
            'ubc_number': '12345678',
            'roles': ['1']
        }

        self.assertFalse(userApi.username_exists(data['username']))
        self.assertFalse(userApi.profile_exists_by_username(data['username']))

        response = self.client.post(reverse('administrators:create_user'), data=urlencode(data, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        user = userApi.get_user_by_username(data['username'])
        self.assertEqual(user.username, data['username'])
        self.assertTrue(userApi.profile_exists_by_username(user.username))

    def test_create_user_with_duplicates_in_view(self):
        print('\n- Test: create a user with duplicates')
        self.login('admin', '12')
        data = {
            'first_name': 'test',
            'last_name': 'user5',
            'email': 'test.user5@example.com',
            'username': 'test.user5',
            'password': '12',
            'preferred_name': None,
            'ubc_number': '12345678',
            'roles': ['1']
        }

        # Check username
        self.assertTrue(userApi.username_exists(data['username']))
        self.assertTrue(userApi.profile_exists_by_username(data['username']))

        response = self.client.post(reverse('administrators:create_user'), data=urlencode(data, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        # Check UBC number
        data = {
            'first_name': 'test555',
            'last_name': 'user555',
            'email': 'test.user555@example.com',
            'username': 'test.user555',
            'password': '12',
            'preferred_name': None,
            'ubc_number': '123456780',
            'roles': ['1']
        }
        self.assertFalse(userApi.username_exists(data['username']))
        self.assertFalse(userApi.profile_exists_by_username(data['username']))
        response = self.client.post(reverse('administrators:create_user'), data=urlencode(data, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

    def test_create_user_via_api(self):
        print('\n- Test: create a user via api when the function added in SAML')

        data = {
            'first_name': 'test5',
            'last_name': 'user55',
            'email': 'test.user55@example.com',
            'username': 'test.user55',
            'password': '12',
            'preferred_name': None,
            'ubc_number': '12345678',
            'roles': ['1']
        }
        self.assertFalse(userApi.username_exists(data['username']))
        self.assertFalse(userApi.profile_exists_by_username(data['username']))

        user, message = userApi.create_user(data)
        self.assertTrue(userApi.username_exists(data['username']))
        self.assertTrue(userApi.profile_exists_by_username(data['username']))

    def test_show_user(self):
        print('\n- Test: show a user')
        self.login('admin', '12')

        user = userApi.get_user('25')
        response = self.client.get(reverse('administrators:show_user', args=[user.username, 'administrator']))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['user'].username, user.username)
        self.assertEqual(response.context['previous_url'], None)
        self.assertEqual(response.context['role'], 'administrator')

    def test_show_user_not_exists(self):
        print('\n- Test: show no existing user ')
        self.login('admin', '12')

        response = self.client.get(reverse('administrators:show_user', args=['zzzzzz', 'administrator']))
        self.assertEqual(response.status_code, 404)

    def test_delete_user(self):
        print('\n- Test: delete a user')
        self.login('admin', '12')

        user = userApi.get_user('25')
        data = { 'user': user.id }
        response = self.client.post(reverse('administrators:delete_user'), data=urlencode(data), content_type=ContentType)

        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:show_user', args=[user.username, 'administrator']))
        self.assertEqual(response.status_code, 404)

        self.assertFalse(userApi.user_exists(user))
        self.assertFalse(userApi.resume_exists(user))
        self.assertFalse(userApi.confidentiality_exists(user))

        # Check user's profile, profile-degrees, profile-trainings
        self.assertFalse(userApi.profile_exists(user))
        degree_found = False
        for degree in userApi.get_degrees():
            if degree.profile_set.filter(user_id=user.id ).exists():
                degree_found = True
        self.assertFalse(degree_found)

        training_found = False
        for training in userApi.get_trainings():
            if training.profile_set.filter(user_id=user.id ).exists():
                training_found = True
        self.assertFalse(degree_found)

    def test_change_user_roles(self):
        print('\n- Test: change an user roles')
        self.login('admin', '12')

        user = userApi.get_user('25')
        user_first_role = user.profile.roles.all()[0]
        self.assertEqual(user_first_role.name, Role.STUDENT)

        response = self.client.post(reverse('administrators:users'), data=urlencode({ 'user': user.id, 'roles': ['2', '3'] }, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

    def test_change_user_roles_with_no_user_id(self):
        print('\n- Test: change an user roles with no user id')
        self.login('admin', '12')

        user = userApi.get_user('25')
        user_first_role = user.profile.roles.all()[0]
        self.assertEqual(user_first_role.name, Role.STUDENT)

        response = self.client.post(reverse('administrators:users'), data=urlencode({ 'roles': ['2', '3'] }, True), content_type=ContentType)
        self.assertEqual(response.status_code, 404)



class SessionTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        print('\nAdministrators:Session testing has started ==>')

    def login(self, username, password):
        self.client.post('/accounts/local_login/', data={'username': username, 'password': password})

    def test_view_url_exists_at_desired_location(self):
        self.login('admin', '12')
        response = self.client.get( reverse('administrators:sessions') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:current_sessions') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:archived_sessions') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:create_session') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:create_session_confirmation') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:show_session', args=['2019-w1', 'current']) )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:edit_session', args=['2019-w1', 'current']) )
        self.assertEqual(response.status_code, 200)

    def test_create_session(self):
        print('\n- Test: create a session')
        self.login('admin', '12')
        data = {
            'year': '2020',
            'term': '2',
            'title': 'New TA Application',
            'description': 'new description',
            'note': 'new note'
        }
        sessions = adminApi.get_sessions_by_year(data['year'])
        self.assertEqual( sessions.count(), 0 )

        response = self.client.post(reverse('administrators:create_session'), data=urlencode(data), content_type=ContentType)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(response.url)
        session = self.client.session
        self.assertEqual(session['session_form_data'], data)
        self.assertEqual(response.context['courses'].count(), 6)

        data['courses'] = [ str(course.id) for course in response.context['courses'] ]
        data['is_visible'] = False
        data['is_archived'] = False
        response = self.client.post(reverse('administrators:create_session_confirmation'), data=urlencode(data, True), content_type=ContentType)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        sessions = adminApi.get_sessions_by_year(data['year'])
        self.assertEqual( sessions.count(), 1 )
        self.assertEqual(sessions[0].year, data['year'])
        self.assertEqual(sessions[0].term.code, 'W1')
        self.assertEqual(sessions[0].term.name, 'Winter Term 1')
        self.assertEqual(sessions[0].title, data['title'])
        self.assertEqual(sessions[0].description, data['description'])
        self.assertEqual(sessions[0].is_visible, data['is_visible'])
        self.assertEqual(sessions[0].is_archived, data['is_archived'])
        self.assertEqual(sessions[0].job_set.count(), 6)


    def test_delete_session(self):
        print('\n- Test: delete a session')
        self.login('admin', '12')
        session_id = '6'
        data = { 'session': session_id }
        response = self.client.post(reverse('administrators:delete_session', args=['current']), data=urlencode(data), content_type=ContentType)

        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)
        self.assertFalse( adminApi.session_exists(session_id) )


    def test_edit_session(self):
        print('\n- Test: edit a session')
        self.login('admin', '12')
        session_id = '6'
        session = adminApi.get_session(session_id)
        courses = adminApi.get_courses_by_term('6')
        data = {
            'session': session_id,
            'year': '2019',
            'term': '6',
            'title': 'Edited TA Application',
            'description': 'Edited description',
            'note': 'Edited note',
            'is_visible': 'True',
            'courses': [ str(courses[0].id), str(courses[1].id) ]
        }

        response = self.client.post(reverse('administrators:edit_session', args=[session.slug, 'current']), data=urlencode(data, True), content_type=ContentType)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue('Success' in messages[0])

        updated_session = adminApi.get_session(session_id)
        self.assertEqual( updated_session.id, int(data['session']) )
        self.assertEqual( updated_session.year, data['year'] )
        self.assertEqual( updated_session.title, data['title'] )
        self.assertEqual( updated_session.description, data['description'] )
        self.assertEqual( updated_session.note, data['note'] )
        self.assertEqual( updated_session.is_visible, eval(data['is_visible']) )
        self.assertEqual( updated_session.job_set.count(), len(data['courses']) )


class JobTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        print('\nJob testing has started ==>')

    def login(self, username, password):
        self.client.post('/accounts/local_login/', data={'username': username, 'password': password})

    def messages(self, res):
        return [m.message for m in get_messages(res.wsgi_request)]

    def apply_jobs(self, user, active_sessions):
        ''' Students apply jobs '''
        num_applications = 0
        num = 0
        for session in active_sessions:
            for job in session.job_set.all():
                if num % 2 == 0:
                    data = {
                        'applicant': user.id,
                        'job': str(job.id),
                        'supervisor_approval': 'True',
                        'how_qualified': '4',
                        'how_interested': '4',
                        'availability': 'True',
                        'availability_note': 'good'
                    }
                    response = self.client.post(reverse('home:show_job', args=[session.slug, job.course.slug]), data=urlencode(data, True), content_type=ContentType)
                    self.assertEqual(response.status_code, 302) # Redirect to session details
                    #self.assertRedirects(response, response.url)
                    messages = [m.message for m in get_messages(response.wsgi_request)]
                    self.assertTrue('Success' in messages[num_applications]) # Check a success message
                    num_applications += 1
                num += 1
        return num_applications

    def offer_jobs(self, applications):
        ''' Admins send a job offer '''

        num = 0
        num_offers = 0
        for app in applications:
            if num % 2 == 1:
                data = {
                    'applicant': str(app.applicant.id),
                    'assigned': ApplicationStatus.OFFERED,
                    'assigned_hours': '30.0'
                }
                response = self.client.post(reverse('administrators:offer_job', args=[app.job.session.slug, app.job.course.slug]), data=urlencode(data), content_type=ContentType)
                self.assertEqual(response.status_code, 302)
                #self.assertRedirects(response, response.url)
                messages = [m.message for m in get_messages(response.wsgi_request)]
                self.assertTrue('Success' in messages[num_offers]) # Check a success message

                # Check status of the application
                for st in app.status.all():
                    if st.assigned == ApplicationStatus.OFFERED:
                        self.assertEqual(st.assigned, data['assigned'])
                        self.assertEqual(st.assigned_hours, float(data['assigned_hours']))
                num_offers += 1
            num += 1
        return num_offers


    def test_view_url_exists_at_desired_location(self):
        print('\n- Test: view url exists at desired location')
        self.login('admin', '12')
        session_slug = '2019-w1'
        job_slug = 'lfs-252-001-land-food-and-community-quantitative-data-analysis-w1'

        response = self.client.get( reverse('administrators:jobs') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:show_job', args=[session_slug, job_slug, 'prepare']) )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:prepare_jobs') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:progress_jobs') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:instructor_jobs') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:student_jobs') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:show_job_applications', args=[session_slug, job_slug]) )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:instructor_jobs_details', args=['test.user5']) )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:student_jobs_details', args=['test.user15']) )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:edit_job', args=[session_slug, job_slug]) )
        self.assertEqual(response.status_code, 200)


    def test_prepare_jobs(self):
        print('\n- Test: display all prepare jobs')
        self.login('admin', '12')

        response = self.client.get( reverse('administrators:prepare_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['jobs']), 21 )

    def test_progress_jobs(self):
        print('\n- Test: display all progress jobs')
        self.login('admin', '12')

        response = self.client.get( reverse('administrators:progress_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['jobs']), 21 )

    def test_instructor_jobs(self):
        print('\n- Test: display all instructor jobs')
        self.login('admin', '12')

        response = self.client.get( reverse('administrators:instructor_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['instructors']), 5 )

    def test_student_jobs(self):
        print('\n- Test: display all student jobs')
        self.login('admin', '12')

        response = self.client.get( reverse('administrators:student_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['students']), 22 )

    def test_show_job_applications(self):
        print('\n- Test: display a job applications')
        self.login('admin', '12')

        session_slug = '2019-w1'
        job_slug = 'lfs-252-001-land-food-and-community-quantitative-data-analysis-w1'

        response = self.client.get( reverse('administrators:show_job_applications', args=[session_slug, job_slug]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        job = response.context['job']
        self.assertEqual(job.session.year, '2019')
        self.assertEqual(job.session.term.code, 'W1')
        self.assertEqual(job.session.slug, session_slug)
        self.assertEqual(job.course.slug, job_slug)

    def test_instructor_jobs_details(self):
        print('\n- Test: display jobs that an instructor has')
        self.login('admin', '12')

        username = 'test.user5'
        response = self.client.get( reverse('administrators:instructor_jobs_details', args=[username]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        instructor = response.context['instructor']
        self.assertEqual(instructor.username, username)

    def test_student_jobs_details(self):
        print('\n- Test: display jobs that a student has')
        self.login('admin', '12')

        username = 'test.user15'
        response = self.client.get( reverse('administrators:student_jobs_details', args=[username]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        student = response.context['student']
        self.assertEqual(student.username, username)

    def test_edit_job(self):
        print('\n- Test: edit a job')
        self.login('admin', '12')

        session_slug = '2019-w1'
        job_slug = 'lfs-252-001-land-food-and-community-quantitative-data-analysis-w1'

        response = self.client.get( reverse('administrators:edit_job', args=[session_slug, job_slug]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        session = response.context['session']
        job = response.context['job']
        form = response.context['form']
        self.assertEqual(session.slug, session_slug)
        self.assertEqual(job.course.slug, job_slug)
        self.assertFalse(form.is_bound)
        self.assertEqual(form.instance.id, job.id)

        data = {
            'title': 'new title',
            'description': 'new description',
            'quallification': 'new quallification',
            'note': 'new note',
            'assigned_ta_hours': '180.00',
            'is_active': False,
            'instructors': ['4', '5', '6']
        }
        response = self.client.post( reverse('administrators:edit_job', args=[session_slug, job_slug]), data=urlencode(data, True), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        updated_job = adminApi.get_session_job_by_slug(session_slug, job_slug)
        self.assertEqual(updated_job.title, data['title'])
        self.assertEqual(updated_job.description, data['description'])
        self.assertEqual(updated_job.note, data['note'])
        self.assertEqual(updated_job.assigned_ta_hours, float(data['assigned_ta_hours']))
        self.assertEqual(updated_job.is_active, data['is_active'])
        self.assertEqual(len(updated_job.instructors.all()), len(data['instructors']))



class ApplicationTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        print('\nJob testing has started ==>')

    def login(self, username, password):
        self.client.post('/accounts/local_login/', data={'username': username, 'password': password})

    def messages(self, res):
        return [m.message for m in get_messages(res.wsgi_request)]

    def test_view_url_exists_at_desired_location(self):
        print('\n- Test: view url exists at desired location')
        self.login('admin', '12')
        app_slug = '2019-w1-lfs-250-001-land-food-and-community-i-introduction-to-food-systems-and-sustainability-w1-application-by-testuser10'

        response = self.client.get( reverse('administrators:applications') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:show_application', args=[app_slug, 'all']) )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:applications_dashboard') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:all_applications') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:selected_applications') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:offered_applications') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:accepted_applications') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:declined_applications') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:offered_applications_send_email_confirmation') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:email_history') )
        self.assertEqual(response.status_code, 200)

        #response = self.client.get( reverse('administrators:send_reminder', args=['1']) )
        #self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:decline_reassign_confirmation') )
        self.assertEqual(response.status_code, 200)

    def test_show_application(self):
        print('\n- Test: Display an application details')
        self.login('admin', '12')

        app_slug = '2019-w1-lfs-250-001-land-food-and-community-i-introduction-to-food-systems-and-sustainability-w1-application-by-testuser10'
        path = 'all'

        response = self.client.get( reverse('administrators:show_application', args=[app_slug, path]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual(response.context['app'].slug, app_slug)
        self.assertFalse(response.context['form'].is_bound)
        self.assertEqual(response.context['path'], path)

    def test_applications_dashboard(self):
        print('\n- Test: Display a dashboard to take a look at updates')
        self.login('admin', '12')

    def test_all_applications(self):
        print('\n- Test: Display all applications')
        self.login('admin', '12')

        response = self.client.get( reverse('administrators:all_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['applications']), 33)

    def test_selected_applications(self):
        print('\n- Test: Display applications selected by instructors')
        self.login('admin', '12')

        response = self.client.get( reverse('administrators:selected_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['selected_applications']), 23)
        self.assertFalse(response.context['admin_application_form'].is_bound)
        self.assertFalse(response.context['status_form'].is_bound)
        self.assertEqual( len(response.context['classification_choices']), 6)
        self.assertEqual(response.context['offer_status_code'], ApplicationStatus.OFFERED)

    def test_offered_applications(self):
        print('\n- Test: Display applications offered by admins')
        self.login('admin', '12')

        response = self.client.get( reverse('administrators:offered_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['offered_applications']), 15)

    def test_accepted_applications(self):
        print('\n- Test: Display applications accepted by students')
        self.login('admin', '12')

        response = self.client.get( reverse('administrators:accepted_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['accepted_applications']), 12)

    def test_declined_applications(self):
        print('\n- Test: Display applications declined by students')
        self.login('admin', '12')

        response = self.client.get( reverse('administrators:declined_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['declined_applications']), 3)

    def test_edit_job_application(self):
        print('\n- Test: Edit classification and note in select applications')
        self.login('admin', '12')

        app_id = '12'
        app = adminApi.get_application(app_id)

        data = {
            'application': app_id,
            'classification': '2',
            'note': 'This is a note.'
        }
        response = self.client.post(reverse('administrators:edit_job_application', args=[app.job.session.slug, app.job.course.slug]), data=urlencode(data), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        app = adminApi.get_application(app_id)
        self.assertEqual(app.classification.id, int(data['classification']))
        self.assertEqual(app.note, data['note'])

    def test_offer_job(self):
        print('\n- Test: Admin can offer a job to each job')
        self.login('admin', '12')

        app_id = '5'
        app = adminApi.get_application(app_id)
        self.assertFalse(adminApi.get_offered(app))
        data = {
            'applicant': '10',
            'application': app_id,
            'assigned': ApplicationStatus.OFFERED,
            'assigned_hours': '20.0'
        }
        response = self.client.post(reverse('administrators:offer_job', args=[app.job.session.slug, app.job.course.slug]), data=urlencode(data), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        app = adminApi.get_application(app_id)
        offered_app = adminApi.get_offered(app)[0]
        self.assertTrue(offered_app.assigned, ApplicationStatus.OFFERED)
        self.assertEqual(offered_app.assigned_hours, float(data['assigned_hours']))

    def test_offered_applications_send_email(self):
        print('\n- Test: Admin can offer a job to each job')
        self.login('admin', '12')

        curr_emails = adminApi.get_emails()
        self.assertEqual( len(curr_emails), 13 )

        data = {
            'application': ['25', '29'],
            'email_type': 'type2'
        }
        response = self.client.post(reverse('administrators:offered_applications_send_email'), data=urlencode(data, True), content_type=ContentType)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(response.url)
        session = self.client.session
        self.assertEqual(session['offered_applications_form_data']['applications'], data['application'])

        app_ids = []
        user_emails = []
        for app in response.context['applications']:
            app_ids.append( str(app.id) )
            user_emails.append(app.applicant.email)

        self.assertEqual(len(response.context['applications']), len(data['application']))
        self.assertEqual(response.context['sender'], settings.EMAIL_FROM)
        self.assertEqual(app_ids, data['application'])
        self.assertFalse(response.context['form'].is_bound)
        self.assertEqual(response.context['type'], data['email_type'])

        data = {
            'sender': settings.EMAIL_FROM,
            'receiver': user_emails,
            'title': 'Congratulations!',
            'message': 'You have got an job offer',
            'type': response.context['type']
        }
        response = self.client.post(reverse('administrators:offered_applications_send_email_confirmation'), data=urlencode(data, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual( len(adminApi.get_emails()), len(curr_emails) + len(user_emails) )

    def test_email_history(self):
        print('\n- Test: Display all of email sent by admins to let them know job offers')
        self.login('admin', '12')

        response = self.client.get(reverse('administrators:email_history'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['emails']), 13 )

    def test_send_reminder(self):
        print('\n- Test: Send a reminder email')
        self.login('admin', '12')

        total_emails = len(adminApi.get_emails())
        #print('emails ', len(emails))

        email_id = '1'
        response = self.client.get(reverse('administrators:send_reminder', args=[email_id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        email = response.context['form'].instance
        self.assertEqual( email.id, int(email_id) )

        data = {
            'application': email.application.id,
            'sender': email.sender,
            'receiver': email.receiver,
            'type': email.type,
            'title': email.title,
            'message': email.message
        }
        response = self.client.post( reverse('administrators:send_reminder', args=[email_id]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)
        self.assertEqual(adminApi.get_emails().first().application.id, data['application'])
        self.assertEqual(len(adminApi.get_emails()), total_emails + 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_decline_reassign(self):
        print('\n- Test: Decline and reassign a job offer with new assigned hours')
        self.login('admin', '12')

        app_id = 2

        response = self.client.get( reverse('administrators:accepted_applications') )
        self.assertEqual(response.status_code, 200)
        accepted_applications = response.context['accepted_applications']

        application = None
        for app in accepted_applications:
            if app.id == app_id:
                application = app
                break

        data = {
            'application': str(application.id),
            'new_assigned_hours': '70.0',
            'old_assigned_hours': str(application.has_accepted)
        }
        response = self.client.post(reverse('administrators:decline_reassign'), data=urlencode(data), content_type=ContentType)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(response.url)
        session = self.client.session
        self.assertEqual(session['decline_reassign_form_data'], data)

        response = self.client.post( reverse('administrators:decline_reassign_confirmation'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:accepted_applications'))
        self.assertEqual(response.status_code, 200)
        accepted_applications = response.context['accepted_applications']

        updated_app = None
        for app in accepted_applications:
            if app.id == app_id:
                updated_app = app
                break
        status = []
        for st in updated_app.applicationstatus_set.all():
            status.append({
                'id': st.id,
                'assigned': st.assigned,
                'assigned_hours': st.assigned_hours,
                'parent_id': st.parent_id
            })
        self.assertEqual(len(status), 7)
        self.assertEqual(status[2]['assigned'], ApplicationStatus.ACCEPTED)
        self.assertEqual(status[3]['assigned'], ApplicationStatus.DECLINED)
        self.assertEqual(status[3]['assigned_hours'], 0.0)
        self.assertEqual(status[3]['parent_id'], str(status[2]['id']))
        self.assertEqual(status[4]['assigned'], ApplicationStatus.ACCEPTED)
        self.assertEqual(status[4]['assigned_hours'], float(data['new_assigned_hours']))
