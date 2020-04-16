from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from urllib.parse import urlencode

from administrators.models import *
from users.models import *
from administrators import api as adminApi
from users import api as userApi

from administrators.tests.test_views import LOGIN_URL, ContentType, DATA, SESSION, PASSWORD, USERS
from django.core.files.uploadedfile import SimpleUploadedFile
import datetime

USER = 'User42.Ins'
JOB = 'apbi-200-002-introduction-to-soil-science-w1'
STUDENT = 'user66.test'

class InstructorTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        cls.user = userApi.get_user(USER, 'username')

    def login(self, username=None, password=None):
        if username and password:
            self.client.post(LOGIN_URL, data={'username': username, 'password': password})
        else:
            self.client.post(LOGIN_URL, data={'username': self.user.username, 'password': PASSWORD})

    def messages(self, res):
        return [m.message for m in get_messages(res.wsgi_request)]

    def test_view_url_exists_at_desired_location(self):
        print('\n- Test: view url exists at desired location')

        self.login(USERS[0], 'password')

        response = self.client.get( reverse('instructors:index') )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('instructors:show_jobs') )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('instructors:edit_job', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('instructors:show_applications', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 403)

        self.login(USERS[2], 'password')

        response = self.client.get( reverse('instructors:index') )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('instructors:show_jobs') )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('instructors:edit_job', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('instructors:show_applications', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 403)

        self.login('user3.admin', 'password')

        response = self.client.get( reverse('instructors:index') )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('instructors:show_jobs') )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('instructors:edit_job', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('instructors:show_applications', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 403)

        self.login()

        response = self.client.get( reverse('instructors:index') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('instructors:show_jobs') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('instructors:edit_job', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('instructors:show_applications', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 200)

    def test_index(self):
        print('\n- Display an index page')
        self.login()

        response = self.client.get( reverse('instructors:index') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USER)
        self.assertEqual(response.context['loggedin_user'].roles, ['Instructor'])

    def test_edit_user(self):
        print('\n- Test to edit the information of an user')
        self.login()

        user = userApi.get_user(USER, 'username')
        user_first_role = user.profile.roles.all()[0]
        self.assertEqual(user_first_role.name, Role.INSTRUCTOR)

        data = {
            'user': user.id,
            'first_name': 'firstname',
            'last_name': 'lastname',
            'email': 'new_email@example.com',
            'employee_number': '5554444'
        }
        response = self.client.post(reverse('instructors:edit_user'), data=urlencode(data), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/instructors/')
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('instructors:index') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USER)
        self.assertEqual(response.context['loggedin_user'].roles, ['Instructor'])
        self.assertEqual(response.context['loggedin_user'].first_name, data['first_name'])
        self.assertEqual(response.context['loggedin_user'].last_name, data['last_name'])
        self.assertEqual(response.context['loggedin_user'].email, data['email'])
        self.assertEqual(response.context['loggedin_user'].confidentiality.employee_number, data['employee_number'])


    def test_edit_user_missing_values(self):
        print('\n- Test to edit the information of an user with missing values')
        self.login()

        user = userApi.get_user(USER, 'username')
        user_first_role = user.profile.roles.all()[0]
        self.assertEqual(user_first_role.name, Role.INSTRUCTOR)

        data1 = {
            'user': user.id,
            'last_name': 'lastname',
            'email': 'new_email@example.com',
            'employee_number': '5554444'
        }
        response = self.client.post(reverse('instructors:edit_user'), data=urlencode(data1, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/instructors/users/edit/')
        self.assertRedirects(response, response.url)

        data2 = {
            'user': user.id,
            'first_name': 'first name',
            'email': 'new_email@example.com',
            'employee_number': '5554444'
        }
        response = self.client.post(reverse('instructors:edit_user'), data=urlencode(data2, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/instructors/users/edit/')
        self.assertRedirects(response, response.url)

        data3 = {
            'user': user.id,
            'first_name': 'first name',
            'last_name': 'last name',
            'employee_number': '5554444'
        }
        response = self.client.post(reverse('instructors:edit_user'), data=urlencode(data3, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/instructors/users/edit/')
        self.assertRedirects(response, response.url)

        data4 = {
            'user': user.id,
            'first_name': 'first name',
            'last_name': 'last name',
            'email': 'new_email',
            'employee_number': '5554444'
        }
        response = self.client.post(reverse('instructors:edit_user'), data=urlencode(data4, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/instructors/users/edit/')
        self.assertRedirects(response, response.url)

        data5 = {
            'user': user.id,
            'first_name': 'first name',
            'last_name': 'last name',
            'email': 'new_email@example.com',
            'employee_number': '55544448'
        }
        response = self.client.post(reverse('instructors:edit_user'), data=urlencode(data5, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/instructors/users/edit/')
        self.assertRedirects(response, response.url)

        data6 = {
            'user': user.id,
            'first_name': 'first name',
            'last_name': 'last name',
            'email': 'new_email@example.com',
            'employee_number': '555'
        }
        response = self.client.post(reverse('instructors:edit_user'), data=urlencode(data6, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/instructors/users/edit/')
        self.assertRedirects(response, response.url)


    def test_show_user(self):
        print('\n- Display an user details')
        self.login()

        SESSION = '2019-w1'
        
        next = '?next=/instructors/sessions/{0}/jobs/{1}/applications/&p={2}&t={3}'
        next_wrong = '?nex=/instructors/sessions/{0}/jobs/{1}/applications/&p={2}&t={3}'
        next_page_wrong = '?next=/instructors/sessions/{0}/jobs/{1}/applications/&a={2}&t={3}'
        next_tab_wrong = '?next=/instructors/sessions/{0}/jobs/{1}/applications/&p={2}&j={3}'

        response = self.client.get( reverse('users:show_user', args=[STUDENT]) + next_wrong.format(SESSION, JOB, 'Applications', 'basic') )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('users:show_user', args=[STUDENT]) + next_page_wrong.format(SESSION, JOB, 'Applications', 'basic') )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('users:show_user', args=[STUDENT]) + next_tab_wrong.format(SESSION, JOB, 'Applications', 'basic') )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('users:show_user', args=[STUDENT]) + next.format('2019-w11', JOB, 'Applications', 'basic') )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('users:show_user', args=[STUDENT]) + next.format(SESSION, 'apbi-200-002-introduction-to-soil-science-w', 'Applications', 'basic') )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('users:show_user', args=[STUDENT]) + next.format(SESSION, JOB, 'Application', 'basic') )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('users:show_user', args=[STUDENT]) + next.format(SESSION, JOB, 'Applications', 'basid') )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('users:show_user', args=[STUDENT]) + next.format(SESSION, JOB, 'Applications', 'basic') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('users:show_user', args=[STUDENT]) + next.format(SESSION, JOB, 'Applications', 'basic') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USER)
        self.assertEqual(response.context['loggedin_user'].roles, ['Instructor'])
        self.assertEqual(response.context['selected_user'].username, STUDENT)

    def test_show_jobs(self):
        print('\n- Display jobs by instructors')
        self.login()

        response = self.client.get( reverse('instructors:show_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USER)
        self.assertEqual(response.context['loggedin_user'].roles, ['Instructor'])
        self.assertEqual( response.context['loggedin_user'].job_set.count(), 11)
        jobs = response.context['loggedin_user'].job_set.all()
        for job in jobs:
            self.assertGreaterEqual(job.assigned_ta_hours, 0.0)
            self.assertGreaterEqual(job.accumulated_ta_hours, 0.0)


    def test_edit_job(self):
        print('\n- Display jobs by instructors')
        self.login()

        response = self.client.get( reverse('instructors:edit_job', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USER)
        self.assertEqual(response.context['loggedin_user'].roles, ['Instructor'])
        self.assertEqual(response.context['job'].course.slug, JOB)
        self.assertFalse(response.context['form'].is_bound)
        self.assertEqual(response.context['form'].instance, response.context['job'])
        self.assertEqual( len(response.context['jobs']), 6 )

        data = {
            'course_overview': 'course overview',
            'description': 'job description',
            'note': 'job note'
        }

        response = self.client.post( reverse('instructors:edit_job', args=[SESSION, JOB]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/instructors/jobs/')
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('instructors:edit_job', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['job'].course_overview, data['course_overview'])
        self.assertEqual(response.context['job'].description, data['description'])
        self.assertEqual(response.context['job'].note, data['note'])

    def test_show_job(self):
        print('\n- Test: display a job')
        self.login()

        response = self.client.get( reverse('instructors:show_job', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USER)
        self.assertEqual(response.context['loggedin_user'].roles, ['Instructor'])
        job = response.context['job']
        self.assertEqual(job.session.year, '2019')
        self.assertEqual(job.session.term.code, 'W1')
        self.assertEqual(job.session.slug, SESSION)
        self.assertEqual(job.course.slug, JOB)

    def test_show_applications(self):
        print('\n- Display applications applied by students')
        self.login()

        job = adminApi.get_job_by_session_slug_job_slug(SESSION, JOB)

        response = self.client.get( reverse('instructors:show_applications', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USER)
        self.assertEqual(response.context['loggedin_user'].roles, ['Instructor'])
        self.assertEqual(response.context['job'].course.slug, JOB)
        self.assertEqual( len(response.context['job'].application_set.all()), 4 )
        self.assertEqual(response.context['job'].application_set.first().instructor_preference, '0')
        self.assertEqual( len(response.context['instructor_preference_choices']), 5 )

        # Invalid assigned hours
        data = {
            'assigned': ApplicationStatus.OFFERED,
            'application': '6',
            'instructor_preference': Application.NONE,
            'assigned_hours': 'abcde'
        }
        response = self.client.post( reverse('instructors:show_applications', args=[SESSION, JOB]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/instructors/sessions/{0}/jobs/{1}/applications/'.format(SESSION, JOB))
        self.assertRedirects(response, response.url)

        # Minus assigned hours
        data = {
            'assigned': ApplicationStatus.OFFERED,
            'application': '6',
            'instructor_preference': Application.NONE,
            'assigned_hours': '-20.2'
        }
        response = self.client.post( reverse('instructors:show_applications', args=[SESSION, JOB]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/instructors/sessions/{0}/jobs/{1}/applications/'.format(SESSION, JOB))
        self.assertRedirects(response, response.url)

        data = {
            'assigned': ApplicationStatus.OFFERED,
            'application': '6',
            'instructor_preference': Application.NONE,
            'assigned_hours': '0.0'
        }
        response = self.client.post( reverse('instructors:show_applications', args=[SESSION, JOB]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/instructors/sessions/{0}/jobs/{1}/applications/'.format(SESSION, JOB))
        self.assertRedirects(response, response.url)

        data['instructor_preference'] = Application.NO_PREFERENCE
        data['assigned_hours'] = '10.0'
        response = self.client.post( reverse('instructors:show_applications', args=[SESSION, JOB]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/instructors/sessions/{0}/jobs/{1}/applications/'.format(SESSION, JOB))
        self.assertRedirects(response, response.url)

        data['instructor_preference'] = Application.ACCEPTABLE
        data['assigned_hours'] = '0.0'
        response = self.client.post( reverse('instructors:show_applications', args=[SESSION, JOB]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/instructors/sessions/{0}/jobs/{1}/applications/'.format(SESSION, JOB))
        self.assertRedirects(response, response.url)

        data['instructor_preference'] = Application.ACCEPTABLE
        data['assigned_hours'] = '201.0'
        response = self.client.post( reverse('instructors:show_applications', args=[SESSION, JOB]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/instructors/sessions/{0}/jobs/{1}/applications/'.format(SESSION, JOB))
        self.assertRedirects(response, response.url)

        data['instructor_preference'] = Application.REQUESTED
        data['assigned_hours'] = '20.0'
        response = self.client.post( reverse('instructors:show_applications', args=[SESSION, JOB]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('instructors:show_applications', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['job'].application_set.first().instructor_preference, Application.REQUESTED)

        apps = response.context['apps']
        self.assertEqual( len(apps) , 4 )

        second_app = None
        count = 0
        for app in apps:
            if count == 1: second_app = app
            count += 1

        self.assertEqual(second_app.id, 11)
        self.assertEqual(second_app.applicant.username, 'user70.test')
        self.assertEqual(second_app.applicationstatus_set.last().get_assigned_display(), 'Accepted')
        self.assertEqual(second_app.applicationstatus_set.last().assigned_hours, 65.5)
        self.assertEqual(second_app.applicationstatus_set.last().created_at, datetime.date(2019, 9, 20))


    def test_write_note(self):
        print('\n- Write a note')
        self.login()

        APP = SESSION + '-' + JOB + '-application-by-user66test'
        app = adminApi.get_application(APP, 'slug')
        self.assertIsNone(app.note)

        data = { 'note': 'new note' }
        response = self.client.post( reverse('instructors:write_note', args=[APP]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('instructors:show_applications', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 200)
        apps = response.context['apps']

        appl = None
        for a in apps:
            if app.id == a.id: appl = a

        self.assertIsNotNone(appl)
        self.assertEqual(app.id, appl.id)
        self.assertEqual(app.applicant, appl.applicant)
        self.assertEqual(app.job, appl.job)
        self.assertEqual(app.supervisor_approval, appl.supervisor_approval)
        self.assertEqual(app.how_qualified, appl.how_qualified)
        self.assertEqual(app.how_interested, appl.how_interested)
        self.assertEqual(app.availability, appl.availability)
        self.assertEqual(app.availability_note, appl.availability_note)
        self.assertEqual(app.classification, appl.classification)
        self.assertEqual(app.instructor_preference, appl.instructor_preference)
        self.assertEqual(app.is_declined_reassigned, appl.is_declined_reassigned)
        self.assertEqual(app.is_terminated, appl.is_terminated)
        self.assertIsNotNone(appl.note)
        self.assertEqual(appl.note, data['note'])
