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
        cls.user = userApi.get_user_by_username('admin')

    def login(self, username=None, password=None):
        if username and password:
            self.client.post('/accounts/local_login/', data={'username': username, 'password': password})
        else:
            self.client.post('/accounts/local_login/', data={'username': self.user.username, 'password': self.user.password})

    def messages(self, res):
        return [m.message for m in get_messages(res.wsgi_request)]

    def test_view_url_exists_at_desired_location(self):
        print('\n- Test: view url exists at desired location')

        response = self.client.get( reverse('administrators:hr') )
        self.assertEqual(response.status_code, 302)

        response = self.client.get( reverse('administrators:users') )
        self.assertEqual(response.status_code, 302)

        response = self.client.get( reverse('administrators:create_user') )
        self.assertEqual(response.status_code, 302)

        response = self.client.get( reverse('administrators:view_confidentiality', args=['admin', 'administrator']) )
        self.assertEqual(response.status_code, 302)

        response = self.client.get( reverse('administrators:show_user', args=['admin', 'administrator']) )
        self.assertEqual(response.status_code, 302)

        self.login()

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
        self.login()
        response = self.client.get(reverse('administrators:users'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['users']), 30)

    def test_create_user_with_no_profile_in_view(self):
        print('\n- Test: create a user with no profile')
        self.login()

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
        self.login()

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
        self.login()
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
        self.login()

        user = userApi.get_user('25')
        response = self.client.get(reverse('administrators:show_user', args=[user.username, 'administrator']))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['user'].username, user.username)
        self.assertEqual(response.context['previous_url'], None)
        self.assertEqual(response.context['role'], 'administrator')

    def test_show_user_not_exists(self):
        print('\n- Test: show no existing user ')
        self.login()

        response = self.client.get(reverse('administrators:show_user', args=['zzzzzz', 'administrator']))
        self.assertEqual(response.status_code, 404)

    def test_delete_user(self):
        print('\n- Test: delete a user')
        self.login()

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
        self.login()

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
        self.login()

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
        cls.user = userApi.get_user_by_username('admin')

    def login(self, username=None, password=None):
        if username and password:
            self.client.post('/accounts/local_login/', data={'username': username, 'password': password})
        else:
            self.client.post('/accounts/local_login/', data={'username': self.user.username, 'password': self.user.password})

    def test_view_url_exists_at_desired_location(self):
        self.login()
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
        self.login()
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
        self.login()
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
        self.login()
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
        cls.user = userApi.get_user_by_username('admin')

    def login(self, username=None, password=None):
        if username and password:
            self.client.post('/accounts/local_login/', data={'username': username, 'password': password})
        else:
            self.client.post('/accounts/local_login/', data={'username': self.user.username, 'password': self.user.password})

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
        self.login()
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
        self.login()

        response = self.client.get( reverse('administrators:prepare_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['jobs']), 21 )

    def test_progress_jobs(self):
        print('\n- Test: display all progress jobs')
        self.login()

        response = self.client.get( reverse('administrators:progress_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['jobs']), 21 )

    def test_instructor_jobs(self):
        print('\n- Test: display all instructor jobs')
        self.login()

        response = self.client.get( reverse('administrators:instructor_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['instructors']), 5 )

    def test_student_jobs(self):
        print('\n- Test: display all student jobs')
        self.login()

        response = self.client.get( reverse('administrators:student_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['students']), 22 )

    def test_show_job_applications(self):
        print('\n- Test: display a job applications')
        self.login()

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
        self.login()

        username = 'test.user5'
        response = self.client.get( reverse('administrators:instructor_jobs_details', args=[username]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        instructor = response.context['instructor']
        self.assertEqual(instructor.username, username)

    def test_student_jobs_details(self):
        print('\n- Test: display jobs that a student has')
        self.login()

        username = 'test.user15'
        response = self.client.get( reverse('administrators:student_jobs_details', args=[username]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        student = response.context['student']
        self.assertEqual(student.username, username)

    def test_edit_job(self):
        print('\n- Test: edit a job')
        self.login()

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
        cls.user = userApi.get_user_by_username('admin')

    def login(self, username=None, password=None):
        if username and password:
            self.client.post('/accounts/local_login/', data={'username': username, 'password': password})
        else:
            self.client.post('/accounts/local_login/', data={'username': self.user.username, 'password': self.user.password})

    def messages(self, res):
        return [m.message for m in get_messages(res.wsgi_request)]

    def test_view_url_exists_at_desired_location(self):
        print('\n- Test: view url exists at desired location')
        self.login()
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
        self.login()

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
        self.login()

    def test_all_applications(self):
        print('\n- Test: Display all applications')
        self.login()

        response = self.client.get( reverse('administrators:all_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['applications']), 33)

    def test_selected_applications(self):
        print('\n- Test: Display applications selected by instructors')
        self.login()

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
        self.login()

        response = self.client.get( reverse('administrators:offered_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['offered_applications']), 15)

    def test_accepted_applications(self):
        print('\n- Test: Display applications accepted by students')
        self.login()

        response = self.client.get( reverse('administrators:accepted_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['accepted_applications']), 12)

    def test_declined_applications(self):
        print('\n- Test: Display applications declined by students')
        self.login()

        response = self.client.get( reverse('administrators:declined_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['declined_applications']), 3)

    def test_edit_job_application(self):
        print('\n- Test: Edit classification and note in select applications')
        self.login()

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
        self.login()

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
        self.login()

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
        self.login()

        response = self.client.get(reverse('administrators:email_history'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['emails']), 13 )

    def test_send_reminder(self):
        print('\n- Test: Send a reminder email')
        self.login()

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
        self.login()

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


class CourseTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        print('\nAdministators:Course testing has started ==>')
        cls.user = userApi.get_user_by_username('admin')

    def login(self, username=None, password=None):
        if username and password:
            self.client.post('/accounts/local_login/', data={'username': username, 'password': password})
        else:
            self.client.post('/accounts/local_login/', data={'username': self.user.username, 'password': self.user.password})

    def messages(self, res):
        return [m.message for m in get_messages(res.wsgi_request)]

    def test_view_url_exists_at_desired_location(self):
        print('\n- Test: view url exists at desired location')
        self.login()

        course_slug = 'lfs-100-001-introduction-to-land-food-and-community-w1'

        response = self.client.get( reverse('administrators:courses') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:all_courses') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:create_course') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:edit_course', args=[course_slug]) )
        self.assertEqual(response.status_code, 200)


    def test_all_courses(self):
        print('\n- Test: Display all courses and edit/delete a course')
        self.login()

        response = self.client.get(reverse('administrators:all_courses'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['courses']), 18 )


    def test_create_course(self):
        print('\n- Test: Create a course')
        self.login()

        total_courses = len(adminApi.get_courses())

        data = {
            'code': '2',
            'number': '1',
            'section': '1',
            'name': 'new course',
            'term': '2'
        }
        response = self.client.post( reverse('administrators:create_course'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:all_courses'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['courses']), total_courses + 1 )


    def test_edit_course(self):
        print('\n- Test: Edit a course')
        self.login()

        course_slug = 'lfs-100-001-introduction-to-land-food-and-community-w1'

        response = self.client.get(reverse('administrators:edit_course', args=[course_slug]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual(response.context['course'].slug, course_slug)
        self.assertFalse(response.context['form'].is_bound)

        course_id = response.context['course'].id

        data = {
            'code': 2,
            'number': 1,
            'section': 1,
            'name': 'edit course',
            'term': 2
        }

        response = self.client.post( reverse('administrators:edit_course', args=[course_slug]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        course = adminApi.get_course(course_id)

        response = self.client.get(reverse('administrators:edit_course', args=[course.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])

        self.assertEqual(response.context['course'].id, course_id)
        self.assertEqual(response.context['course'].code.id, data['code'])
        self.assertEqual(response.context['course'].number.id, data['number'])
        self.assertEqual(response.context['course'].section.id, data['section'])
        self.assertEqual(response.context['course'].term.id, data['term'])
        self.assertEqual(response.context['course'].name, data['name'])

    def test_delete_course(self):
        print('\n- Test: Edit a course')
        self.login()

        total_courses = len(adminApi.get_courses())

        course_id = 1

        response = self.client.post( reverse('administrators:delete_course'), data=urlencode({ 'course': course_id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:all_courses'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['courses']), total_courses - 1 )


class PreparationTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        print('\nAdministators:Preparation testing has started ==>')
        cls.user = userApi.get_user_by_username('admin')

    def login(self, username=None, password=None):
        if username and password:
            self.client.post('/accounts/local_login/', data={'username': username, 'password': password})
        else:
            self.client.post('/accounts/local_login/', data={'username': self.user.username, 'password': self.user.password})

    def messages(self, res):
        return [m.message for m in get_messages(res.wsgi_request)]

    def test_view_url_exists_at_desired_location(self):
        print('\n- Test: view url exists at desired location')
        self.login()

        response = self.client.get( reverse('administrators:preparation') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:degrees') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:programs') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:trainings') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:statuses') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:course_codes') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:course_numbers') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:course_sections') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:classifications') )
        self.assertEqual(response.status_code, 200)

    def test_degrees(self):
        print('\n- Test: Display all degrees and create a degree')
        self.login()

        response = self.client.get( reverse('administrators:degrees') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['degrees']), 11 )
        self.assertFalse(response.context['form'].is_bound)

        data = { 'name': 'Diploma' }
        response = self.client.post( reverse('administrators:degrees'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:degrees') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['degrees']), 12 )
        self.assertEqual(response.context['degrees'].last().name, data['name'])

    def test_edit_degree(self):
        print('\n- Test: edit degree details')
        self.login()

        slug = 'bachelor-of-arts'

        data = { 'name': 'updated degree' }
        response = self.client.post( reverse('administrators:edit_degree', args=[slug]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:degrees') )
        self.assertEqual(response.status_code, 200)
        degrees = response.context['degrees']

        found = 0
        for degree in degrees:
            if degree.slug == 'updated-degree':
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_degree(self):
        print('\n- Test: delete a degree')
        self.login()

        total_degrees = len(userApi.get_degrees())

        degree_id = 1
        response = self.client.post( reverse('administrators:delete_degree'), data=urlencode({ 'degree': degree_id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:degrees'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['degrees']), total_degrees - 1)

        found = False
        for degree in response.context['degrees']:
            if degree.id == degree_id: found = True
        self.assertFalse(found)

    def test_programs(self):
        print('\n- Test: Display all programs and create a program')
        self.login()

        response = self.client.get( reverse('administrators:programs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['programs']), 9 )
        self.assertFalse(response.context['form'].is_bound)

        data = { 'name': 'Master of Science in Animal' }
        response = self.client.post( reverse('administrators:programs'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:programs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['programs']), 10 )
        self.assertEqual(response.context['programs'].last().name, data['name'])

    def test_edit_program(self):
        print('\n- Test: edit program details')
        self.login()

        slug = 'master-of-science-in-applied-animal-biology-msc'

        data = { 'name': 'updated program' }
        response = self.client.post( reverse('administrators:edit_program', args=[slug]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:programs') )
        self.assertEqual(response.status_code, 200)
        programs = response.context['programs']

        found = 0
        for program in programs:
            if program.slug == 'updated-program':
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_program(self):
        print('\n- Test: delete a program')
        self.login()

        total_programs = len(userApi.get_programs())

        program_id = 1
        response = self.client.post( reverse('administrators:delete_program'), data=urlencode({ 'program': program_id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:programs'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['programs']), total_programs - 1)

        found = False
        for program in response.context['programs']:
            if program.id == program_id: found = True
        self.assertFalse(found)

    def test_trainings(self):
        print('\n- Test: Display all trainings and create a training')
        self.login()

        response = self.client.get( reverse('administrators:trainings') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['trainings']), 5 )
        self.assertFalse(response.context['form'].is_bound)

        data = { 'name': 'new training' }
        response = self.client.post( reverse('administrators:trainings'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:trainings') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['trainings']), 6 )
        self.assertEqual(response.context['trainings'].last().name, data['name'])

    def test_edit_training(self):
        print('\n- Test: edit training details')
        self.login()

        slug = 'instructional-skills-workshops-for-grad-students'

        data = { 'name': 'updated training' }
        response = self.client.post( reverse('administrators:edit_training', args=[slug]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:trainings') )
        self.assertEqual(response.status_code, 200)
        trainings = response.context['trainings']

        found = 0
        for training in trainings:
            if training.slug == 'updated-training':
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_training(self):
        print('\n- Test: delete a training')
        self.login()

        total_trainings = len(userApi.get_trainings())

        training_id = 1
        response = self.client.post( reverse('administrators:delete_training'), data=urlencode({ 'training': training_id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:trainings'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['trainings']), total_trainings - 1)

        found = False
        for training in response.context['trainings']:
            if training.id == training_id: found = True
        self.assertFalse(found)

    def test_statuses(self):
        print('\n- Test: Display all statuss and create a status')
        self.login()

        response = self.client.get( reverse('administrators:statuses') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['statuses']), 9 )
        self.assertFalse(response.context['form'].is_bound)

        data = { 'name': 'Full Professor' }
        response = self.client.post( reverse('administrators:statuses'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:statuses') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['statuses']), 10 )
        self.assertEqual(response.context['statuses'].last().name, data['name'])

    def test_edit_status(self):
        print('\n- Test: edit status details')
        self.login()

        slug = 'undergraduate-student'

        data = { 'name': 'updated status' }
        response = self.client.post( reverse('administrators:edit_status', args=[slug]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:statuses') )
        self.assertEqual(response.status_code, 200)
        statuss = response.context['statuses']

        found = 0
        for status in statuss:
            if status.slug == 'updated-status':
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_status(self):
        print('\n- Test: delete a status')
        self.login()

        total_statuses = len(userApi.get_statuses())

        status_id = 1
        response = self.client.post( reverse('administrators:delete_status'), data=urlencode({ 'status': status_id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:statuses'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['statuses']), total_statuses - 1)

        found = False
        for status in response.context['statuses']:
            if status.id == status_id: found = True
        self.assertFalse(found)

    def test_course_codes(self):
        print('\n- Test: Display all course_codes and create a course_code')
        self.login()

        response = self.client.get( reverse('administrators:course_codes') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['course_codes']), 5 )
        self.assertFalse(response.context['form'].is_bound)

        data = { 'name': 'ABC' }
        response = self.client.post( reverse('administrators:course_codes'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:course_codes') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['course_codes']), 6 )
        self.assertEqual(response.context['course_codes'].last().name, data['name'])

    def test_edit_course_code(self):
        print('\n- Test: edit course_code details')
        self.login()

        name = 'AANB'

        data = { 'name': 'CSC' }
        response = self.client.post( reverse('administrators:edit_course_code', args=[name]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:course_codes') )
        self.assertEqual(response.status_code, 200)
        course_codes = response.context['course_codes']

        found = 0
        for course_code in course_codes:
            if course_code.name == 'CSC':
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_course_code(self):
        print('\n- Test: delete a course_code')
        self.login()

        total_course_codes = len(adminApi.get_course_codes())

        course_code_id = 1
        response = self.client.post( reverse('administrators:delete_course_code'), data=urlencode({ 'course_code': course_code_id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:course_codes'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['course_codes']), total_course_codes - 1)

        found = False
        for course_code in response.context['course_codes']:
            if course_code.id == course_code_id: found = True
        self.assertFalse(found)

    def test_course_numbers(self):
        print('\n- Test: Display all course_numbers and create a course_number')
        self.login()

        response = self.client.get( reverse('administrators:course_numbers') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['course_numbers']), 10 )
        self.assertFalse(response.context['form'].is_bound)

        data = { 'name': '500' }
        response = self.client.post( reverse('administrators:course_numbers'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:course_numbers') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['course_numbers']), 11 )
        self.assertEqual(response.context['course_numbers'].last().name, data['name'])

    def test_edit_course_number(self):
        print('\n- Test: edit course_number details')
        self.login()

        name = '100'

        data = { 'name': '111' }
        response = self.client.post( reverse('administrators:edit_course_number', args=[name]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:course_numbers') )
        self.assertEqual(response.status_code, 200)
        course_numbers = response.context['course_numbers']

        found = 0
        for course_number in course_numbers:
            if course_number.name == '111':
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_course_number(self):
        print('\n- Test: delete a course_number')
        self.login()

        total_course_numbers = len(adminApi.get_course_numbers())

        course_number_id = 10
        response = self.client.post( reverse('administrators:delete_course_number'), data=urlencode({ 'course_number': course_number_id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:course_numbers'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['course_numbers']), total_course_numbers - 1)

        found = False
        for course_number in response.context['course_numbers']:
            if course_number.id == course_number_id: found = True
        self.assertFalse(found)

    def test_course_sections(self):
        print('\n- Test: Display all course_sections and create a course_section')
        self.login()

        response = self.client.get( reverse('administrators:course_sections') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['course_sections']), 5 )
        self.assertFalse(response.context['form'].is_bound)

        data = { 'name': '006' }
        response = self.client.post( reverse('administrators:course_sections'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:course_sections') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['course_sections']), 6 )
        self.assertEqual(response.context['course_sections'].last().name, data['name'])

    def test_edit_course_section(self):
        print('\n- Test: edit course_section details')
        self.login()

        name = '005'

        data = { 'name': '115' }
        response = self.client.post( reverse('administrators:edit_course_section', args=[name]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:course_sections') )
        self.assertEqual(response.status_code, 200)
        course_sections = response.context['course_sections']

        found = 0
        for course_section in course_sections:
            if course_section.name == '115':
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_course_section(self):
        print('\n- Test: delete a course_section')
        self.login()

        total_course_sections = len(adminApi.get_course_sections())

        course_section_id = 5
        response = self.client.post( reverse('administrators:delete_course_section'), data=urlencode({ 'course_section': course_section_id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:course_sections'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['course_sections']), total_course_sections - 1)

        found = False
        for course_section in response.context['course_sections']:
            if course_section.id == course_section_id: found = True
        self.assertFalse(found)

    def test_classifications(self):
        print('\n- Test: Display all classifications and create a classification')
        self.login()

        response = self.client.get( reverse('administrators:classifications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['classifications']), 6 )
        self.assertFalse(response.context['form'].is_bound)

        data = {
            'year': '2020',
            'name': 'Marker 2',
            'wage': '16.05',
            'is_active': True
        }
        response = self.client.post( reverse('administrators:classifications'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:classifications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['classifications']), 7 )
        self.assertEqual(response.context['classifications'].latest('pk').name, data['name'])


    def test_edit_classification(self):
        print('\n- Test: edit classification details')
        self.login()

        slug = '2019-marker'

        data = {
            'year': '2020',
            'name': 'Marker 2',
            'wage': '16.05',
            'is_active': False
        }
        response = self.client.post( reverse('administrators:edit_classification', args=[slug]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:classifications') )
        self.assertEqual(response.status_code, 200)
        classifications = response.context['classifications']

        found = 0
        for classification in classifications:
            if classification.slug == '2020-marker-2':
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_classification(self):
        print('\n- Test: delete a classification')
        self.login()

        total_classifications = len(adminApi.get_classifications())

        classification_id = 5
        response = self.client.post( reverse('administrators:delete_classification'), data=urlencode({ 'classification': classification_id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:classifications'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['classifications']), total_classifications - 1)

        found = False
        for classification in response.context['classifications']:
            if classification.id == classification_id: found = True
        self.assertFalse(found)
