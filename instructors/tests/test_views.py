from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from urllib.parse import urlencode
from django.core import mail

from administrators.models import *
from users.models import *
from administrators import api as adminApi
from users import api as userApi

from administrators.tests.test_sessions import LOGIN_URL, ContentType, DATA, SESSION, PASSWORD, USERS
from django.core.files.uploadedfile import SimpleUploadedFile
import datetime

USER = 'user42.ins'
JOB = 'apbi-200-002-introduction-to-soil-science-w1'
STUDENT = 'user66.test'

JOBS_NEXT = '?next=' + reverse('instructors:show_jobs') + '?page=2'
JOBS_WRONG_1 = '?nex=/instructors/jobs/?page=2'
JOBS_WRONG_2 = '?next=/Instructors/jobs/?page=2'
JOBS_WRONG_3 = '?next=/instructors/Jobs/?page=2'

APP_PATH = reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT

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
        print('- Test: view url exists at desired location')

        self.login(USERS[0], 'password')

        response = self.client.get( reverse('instructors:index') )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('instructors:show_jobs') + JOBS_NEXT )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('instructors:edit_job', args=[SESSION, JOB]) + JOBS_NEXT )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT )
        self.assertEqual(response.status_code, 403)

        self.login(USERS[2], 'password')

        response = self.client.get( reverse('instructors:index') )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('instructors:show_jobs') + JOBS_NEXT )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('instructors:edit_job', args=[SESSION, JOB]) + JOBS_NEXT )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT )
        self.assertEqual(response.status_code, 403)

        self.login('user3.admin', 'password')

        response = self.client.get( reverse('instructors:index') )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('instructors:show_jobs') + JOBS_NEXT )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('instructors:edit_job', args=[SESSION, JOB]) + JOBS_NEXT )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT )
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

        response = self.client.get( reverse('instructors:summary_applicants', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 200)


    def test_index(self):
        print('- Display an index page')
        self.login()

        response = self.client.get( reverse('instructors:index') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USER)
        self.assertEqual(response.context['loggedin_user'].roles, ['Instructor'])

    def test_edit_user(self):
        print('- Test to edit the information of an user')
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
        self.assertEqual(response.url, reverse('instructors:index'))
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('instructors:index') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USER)
        self.assertEqual(response.context['loggedin_user'].roles, ['Instructor'])
        self.assertEqual(response.context['loggedin_user'].first_name, data['first_name'])
        self.assertEqual(response.context['loggedin_user'].last_name, data['last_name'])
        self.assertEqual(response.context['loggedin_user'].email, data['email'])
        self.assertEqual(response.context['loggedin_user'].confidentiality.employee_number, data['employee_number'])


    def test_edit_user_missing_values1(self):
        print('- Test to edit the information of an user with missing values - first name')
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
        self.assertEqual(messages[0], 'An error occurred while updating an User Edit Form. FIRST NAME: This field is required.')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('instructors:edit_user'))
        self.assertRedirects(response, response.url)


    def test_edit_user_missing_values2(self):
        print('- Test to edit the information of an user with missing values - last name')
        self.login()

        user = userApi.get_user(USER, 'username')
        user_first_role = user.profile.roles.all()[0]
        self.assertEqual(user_first_role.name, Role.INSTRUCTOR)

        data2 = {
            'user': user.id,
            'first_name': 'first name',
            'email': 'new_email@example.com',
            'employee_number': '5554444'
        }
        response = self.client.post(reverse('instructors:edit_user'), data=urlencode(data2, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue(messages[0], 'An error occurred while updating an User Edit Form. LAST NAME: This field is required.')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('instructors:edit_user'))
        self.assertRedirects(response, response.url)

    def test_edit_user_missing_values3(self):
        print('- Test to edit the information of an user with missing values - email')
        self.login()

        user = userApi.get_user(USER, 'username')
        user_first_role = user.profile.roles.all()[0]
        self.assertEqual(user_first_role.name, Role.INSTRUCTOR)

        data3 = {
            'user': user.id,
            'first_name': 'first name',
            'last_name': 'last name',
            'employee_number': '5554444'
        }
        response = self.client.post(reverse('instructors:edit_user'), data=urlencode(data3, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue(messages[0], 'An error occurred while updating an User Edit Form. EMAIL: This field is required.')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('instructors:edit_user'))
        self.assertRedirects(response, response.url)


    def test_edit_user_missing_values4(self):
        print('- Test to edit the information of an user with missing values - valid email address')
        self.login()

        user = userApi.get_user(USER, 'username')
        user_first_role = user.profile.roles.all()[0]
        self.assertEqual(user_first_role.name, Role.INSTRUCTOR)

        data4 = {
            'user': user.id,
            'first_name': 'first name',
            'last_name': 'last name',
            'email': 'new_email',
            'employee_number': '5554444'
        }
        response = self.client.post(reverse('instructors:edit_user'), data=urlencode(data4, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue(messages[0], 'An error occurred while updating an User Form. EMAIL: Enter a valid email address.')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('instructors:edit_user'))
        self.assertRedirects(response, response.url)


    def test_edit_user_missing_values5(self):
        print('- Test to edit the information of an user with missing values - employee number')
        self.login()

        user = userApi.get_user(USER, 'username')
        user_first_role = user.profile.roles.all()[0]
        self.assertEqual(user_first_role.name, Role.INSTRUCTOR)

        data5 = {
            'user': user.id,
            'first_name': 'first name',
            'last_name': 'last name',
            'email': 'new_email@example.com',
            'employee_number': '55544448'
        }
        response = self.client.post(reverse('instructors:edit_user'), data=urlencode(data5, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue(messages[0], 'An error occurred while updating an User Form. EMPLOYEE NUMBER: Ensure this value has at most 7 characters (it has 8).')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('instructors:edit_user'))
        self.assertRedirects(response, response.url)


    def test_edit_user_missing_values6(self):
        print('- Test to edit the information of an user with missing values - employee number')
        self.login()

        user = userApi.get_user(USER, 'username')
        user_first_role = user.profile.roles.all()[0]
        self.assertEqual(user_first_role.name, Role.INSTRUCTOR)

        data6 = {
            'user': user.id,
            'first_name': 'first name',
            'last_name': 'last name',
            'email': 'new_email@example.com',
            'employee_number': '555'
        }
        response = self.client.post(reverse('instructors:edit_user'), data=urlencode(data6, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue(messages[0], 'An error occurred while updating an User Form. EMPLOYEE NUMBER: Ensure this value has at least 7 characters (it has 3).')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('instructors:edit_user'))
        self.assertRedirects(response, response.url)


    def test_show_user(self):
        print('- Display an user details')
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
        print('- Display jobs by instructors')
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
        print('- Display jobs by instructors')
        self.login()

        session = self.client.session
        session['next_first'] = reverse('instructors:show_jobs') + '?page=1'
        session.save()

        response = self.client.get( reverse('instructors:edit_job', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USER)
        self.assertEqual(response.context['loggedin_user'].roles, ['Instructor'])
        self.assertEqual(response.context['job'].course.slug, JOB)
        self.assertFalse(response.context['form'].is_bound)
        self.assertEqual(response.context['form'].instance, response.context['job'])
        self.assertEqual( len(response.context['jobs']), 6 )
        self.assertEqual(response.context['next_first'], '/instructors/jobs/?page=1')

        next_first = response.context['next_first']

        data = {
            'course_overview': 'course overview',
            'description': 'job description',
            'note': 'job note',
            'next_first': next_first
        }
        response = self.client.post( reverse('instructors:edit_job', args=[SESSION, JOB]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, next_first)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('instructors:edit_job', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['job'].course_overview, data['course_overview'])
        self.assertEqual(response.context['job'].description, data['description'])
        self.assertEqual(response.context['job'].note, data['note'])


    def test_show_job(self):
        print('- Test: display a job')
        self.login()

        session = self.client.session
        session['next_first'] = reverse('instructors:show_jobs') + '?page=1'
        session.save()

        response = self.client.get( reverse('instructors:show_job', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USER)
        self.assertEqual(response.context['loggedin_user'].roles, ['Instructor'])
        job = response.context['job']
        self.assertEqual(job.session.year, '2019')
        self.assertEqual(job.session.term.code, 'W1')
        self.assertEqual(job.session.slug, SESSION)
        self.assertEqual(job.course.slug, JOB)
        self.assertEqual(response.context['next_first'], '/instructors/jobs/?page=1')

    def test_show_applications(self):
        print('- Display applications applied by students')
        self.login()

        job = adminApi.get_job_by_session_slug_job_slug(SESSION, JOB)

        session = self.client.session
        session['next_first'] = reverse('instructors:show_jobs') + '?page=1'
        session.save()

        response = self.client.get( reverse('instructors:show_applications', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USER)
        self.assertEqual(response.context['loggedin_user'].roles, ['Instructor'])
        self.assertEqual(response.context['job'].course.slug, JOB)
        self.assertEqual( len(response.context['job'].application_set.all()), 4 )
        self.assertEqual(response.context['job'].application_set.first().instructor_preference, '0')
        self.assertEqual( len(response.context['instructor_preference_choices']), 5 )

        self.assertEqual(response.context['full_job_name'], 'APBI_200_002')
        self.assertEqual(response.context['app_status'], {'none': '0', 'applied': '0', 'selected': '1', 'offered': '2', 'accepted': '3', 'declined': '4', 'cancelled': '5'})
        self.assertEqual(response.context['next_first'], '/instructors/jobs/?page=1')

        applications = [
            { 'id': 6, 'accepted_apps': ['APBI 260 001 (45.0 hours)'] },
            { 'id': 11, 'accepted_apps': ['APBI 200 002 (65.0 hours)'] },
            { 'id': 16, 'accepted_apps': [] },
            { 'id': 21, 'accepted_apps': ['APBI 200 001 (30.0 hours)', 'APBI 260 001 (70.0 hours)'] }
        ]

        c = 0
        for app in response.context['apps']:
            self.assertEqual(app.id, applications[c]['id'])

            if len(app.applicant.accepted_apps) > 0:
                d = 0
                for accepted_app in app.applicant.accepted_apps:
                    self.assertEqual(accepted_app.job.course.code.name + ' ' + accepted_app.job.course.number.name + ' ' + accepted_app.job.course.section.name + ' ('+ str(accepted_app.accepted.assigned_hours) + ' hours)', applications[c]['accepted_apps'][d])
                    d += 1
            c += 1

    def test_select_instructor_preference_failure1(self):
        print('- select instructor preference failure 1 - Invalid assigned hours')
        self.login()

        data1 = {
            'assigned': ApplicationStatus.OFFERED,
            'application': '6',
            'has_contract_read': False,
            'instructor_preference': Application.NONE,
            'assigned_hours': 'abcde'
        }
        response = self.client.post( reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT, data=urlencode(data1), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred. Please check assigned hours. Assign TA Hours must be numerival value only' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT)
        self.assertRedirects(response, response.url)

    def test_select_instructor_preference_failure2(self):
        print('- select instructor preference failure 2 - Minus assigned hours')
        self.login()

        data2 = {
            'assigned': ApplicationStatus.OFFERED,
            'application': '6',
            'has_contract_read': False,
            'instructor_preference': Application.NONE,
            'assigned_hours': '-20'
        }
        response = self.client.post( reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT, data=urlencode(data2), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred. Please check assigned hours. Assign TA Hours must be greater than 0' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT)
        self.assertRedirects(response, response.url)

    def test_select_instructor_preference_failure3(self):
        print('- select instructor preference failure 3 - no select for a preference')
        self.login()

        data3 = {
            'assigned': ApplicationStatus.OFFERED,
            'application': '6',
            'has_contract_read': False,
            'instructor_preference': Application.NONE,
            'assigned_hours': '0'
        }
        response = self.client.post( reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT, data=urlencode(data3), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred. Please select your preference, then try again' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT)
        self.assertRedirects(response, response.url)


    def test_select_instructor_preference_failure4(self):
        print('- select instructor preference failure 4 - no preference')
        self.login()

        data4 = {
            'assigned': ApplicationStatus.OFFERED,
            'application': '6',
            'has_contract_read': False,
            'instructor_preference': Application.NO_PREFERENCE,
            'assigned_hours': '10'
        }
        response = self.client.post( reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT, data=urlencode(data4), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Please leave 0 for Assign TA Hours if you would like to select No Preference, then try again' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT)
        self.assertRedirects(response, response.url)

    def test_select_instructor_preference_failure5(self):
        print('- select instructor preference failure 5 - yes selection, 0 hours')
        self.login()

        data5 = {
            'assigned': ApplicationStatus.OFFERED,
            'application': '6',
            'has_contract_read': False,
            'instructor_preference': Application.ACCEPTABLE,
            'assigned_hours': '0'
        }
        response = self.client.post( reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT, data=urlencode(data5), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Please assign TA hours, then try again' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT)
        self.assertRedirects(response, response.url)


    def test_select_instructor_preference_failure6(self):
        print('- select instructor preference failure 6 - big assigned hours')
        self.login()

        data6 = {
            'assigned': ApplicationStatus.OFFERED,
            'application': '6',
            'has_contract_read': False,
            'instructor_preference': Application.ACCEPTABLE,
            'assigned_hours': '201'
        }
        response = self.client.post( reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT, data=urlencode(data6), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('You cannot assign 201 hours because Total Assigned TA Hours is 200. then try again' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT)
        self.assertRedirects(response, response.url)

    def test_select_instructor_preference_failure7(self):
        print('- select instructor preference failure 7 - floating point hours')
        self.login()

        data7 = {
            'assigned': ApplicationStatus.OFFERED,
            'application': '6',
            'has_contract_read': False,
            'instructor_preference': Application.ACCEPTABLE,
            'assigned_hours': '66.66'
        }
        response = self.client.post( reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT, data=urlencode(data7), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred. Please check assigned hours. Assign TA Hours must be non-negative integers' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT)
        self.assertRedirects(response, response.url)

    def test_select_instructor_preference_success(self):
        print('- select instructor preference success')
        self.login()

        data8 = {
            'assigned': ApplicationStatus.OFFERED,
            'application': '6',
            'has_contract_read': False,
            'instructor_preference': Application.REQUESTED,
            'assigned_hours': '20'
        }
        response = self.client.post( reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT, data=urlencode(data8), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT )
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
        self.assertEqual(second_app.applicationstatus_set.last().assigned_hours, 65.0)
        self.assertEqual(second_app.applicationstatus_set.last().created_at, datetime.date(2019, 9, 20))


    def test_write_note(self):
        print('- Write a note')
        self.login()

        APP = SESSION + '-' + JOB + '-application-by-user66test'
        app = adminApi.get_application(APP, 'slug')
        self.assertIsNone(app.note)

        next = '/instructors/sessions/2019-w1/jobs/apbi-200-002-introduction-to-soil-science-w1/applications/'

        response = self.client.get(reverse('instructors:write_note', args=[APP]) + '?next=' + next)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USER)
        self.assertEqual(response.context['loggedin_user'].roles, ['Instructor'])
        self.assertEqual(response.context['app'].job.course.slug, JOB)
        self.assertFalse(response.context['form'].is_bound)
        self.assertEqual(response.context['form'].instance, response.context['app'])
        self.assertEqual(response.context['app_status'], {'none': '0', 'applied': '0', 'selected': '1', 'offered': '2', 'accepted': '3', 'declined': '4', 'cancelled': '5'})
        self.assertEqual(response.context['next'], next)

        next1 = '?next=/instructors/sessions/2019-w11/jobs/apbi-200-002-introduction-to-soil-science-w1/applications/'
        next2 = '?next=/instructors/sessions/2019-w1/jobs/apbi-200-009-introduction-to-soil-science-w1/applications/'
        next3 = '?next=/instructors/sessions/2019-w1/jobs/apbi-200-002-introduction-to-soil-science-w1/applicationsss/'
        next4 = '?/instructors/sessions/2019-w1/jobs/apbi-200-002-introduction-to-soil-science-w1/applications/'

        response1 = self.client.get( reverse('instructors:write_note', args=[APP]) + next1 )
        self.assertEqual(response1.status_code, 404)
        response2 = self.client.get( reverse('instructors:write_note', args=[APP]) + next2 )
        self.assertEqual(response2.status_code, 404)
        response3 = self.client.get( reverse('instructors:write_note', args=[APP]) + next3 )
        self.assertEqual(response3.status_code, 404)
        response4 = self.client.get( reverse('instructors:write_note', args=[APP]) + next4 )
        self.assertEqual(response4.status_code, 404)


        data = {
            'note': 'new note',
            'next': next
        }
        response = self.client.post( reverse('instructors:write_note', args=[APP]) + '?next=' + next, data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('instructors:show_applications', args=[SESSION, JOB]))
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

    def test_summary_applicants(self):
        print('- Test: display a summary of applicants')
        self.login()

        next_second = '/instructors/sessions/2019-w1/jobs/apbi-200-002-introduction-to-soil-science-w1/applications/'
        session = self.client.session
        session['next_second'] = next_second
        session.save()

        response = self.client.get( reverse('instructors:summary_applicants', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USER)
        self.assertEqual(response.context['loggedin_user'].roles, ['Instructor'])

        session = response.context['session']
        self.assertEqual(session.year, '2019')
        self.assertEqual(session.term.code, 'W1')
        self.assertEqual(session.slug, SESSION)
        self.assertEqual(response.context['total_applicants'], 5)
        self.assertEqual(response.context['next_second'], next_second)
        applicants = response.context['applicants']

        applicant_list = [
            {
                'username': 'user100.test',
                'no_offers': False,
                'is_sent_alertemail': False,
                'has_applied': True
            },
            {
                'username': 'user65.test',
                'no_offers': False,
                'is_sent_alertemail': False,
                'has_applied': False
            },
            {
                'username': 'user66.test',
                'no_offers': False,
                'is_sent_alertemail': False,
                'has_applied': True
            },
            {
                'username': 'user70.test',
                'no_offers': False,
                'is_sent_alertemail': False,
                'has_applied': True
            },
            {
                'username': 'user80.test',
                'no_offers': True,
                'is_sent_alertemail': False,
                'has_applied': True
            }
        ]

        c = 0
        for applicant in applicants:
            self.assertEqual(applicant.username, applicant_list[c]['username'])
            self.assertEqual(applicant.no_offers, applicant_list[c]['no_offers'])
            self.assertEqual(applicant.is_sent_alertemail, applicant_list[c]['is_sent_alertemail'])
            self.assertEqual(applicant.has_applied, applicant_list[c]['has_applied'])
            c += 1

        del self.client.session['next_second']


    def test_summary_applicants2(self):
        print('- Test: display a summary of applicants 2')

        CURRENT_USER = 'user22.ins'
        CURRENT_JOB = 'apbi-265-001-sustainable-agriculture-and-food-systems-w1'

        self.login(CURRENT_USER, PASSWORD)

        next_second = '/instructors/sessions/2019-w1/jobs/apbi-265-001-sustainable-agriculture-and-food-systems-w1/applicants/'

        session = self.client.session
        session['next_second'] = next_second
        session.save()

        response = self.client.get( reverse('instructors:summary_applicants', args=[SESSION, CURRENT_JOB]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, CURRENT_USER)
        self.assertEqual(response.context['loggedin_user'].roles, ['Instructor'])

        session = response.context['session']
        self.assertEqual(session.year, '2019')
        self.assertEqual(session.term.code, 'W1')
        self.assertEqual(session.slug, SESSION)
        self.assertEqual(response.context['total_applicants'], 5)
        self.assertEqual(response.context['next_second'], next_second)
        applicants = response.context['applicants']


        applicant_list = [
            {
                'username': 'user100.test',
                'no_offers': False,
                'is_sent_alertemail': False,
                'has_applied': False
            },
            {
                'username': 'user65.test',
                'no_offers': False,
                'is_sent_alertemail': False,
                'has_applied': True
            },
            {
                'username': 'user66.test',
                'no_offers': False,
                'is_sent_alertemail': True,
                'has_applied': False
            },
            {
                'username': 'user70.test',
                'no_offers': False,
                'is_sent_alertemail': True,
                'has_applied': False
            },
            {
                'username': 'user80.test',
                'no_offers': True,
                'is_sent_alertemail': False,
                'has_applied': False
            }
        ]

        c = 0
        for applicant in applicants:
            self.assertEqual(applicant.username, applicant_list[c]['username'])
            self.assertEqual(applicant.no_offers, applicant_list[c]['no_offers'])
            self.assertEqual(applicant.is_sent_alertemail, applicant_list[c]['is_sent_alertemail'])
            self.assertEqual(applicant.has_applied, applicant_list[c]['has_applied'])
            c += 1

        del self.client.session['next_second']


    def test_send_email_to_students(self):
        print('- Test: send an email to students')

        CURRENT_USER = 'user22.ins'
        CURRENT_JOB = 'apbi-265-001-sustainable-agriculture-and-food-systems-w1'
        CURRENT_NEXT = '/instructors/sessions/2019-w1/jobs/' + CURRENT_JOB + '/applicants/summary-applicants/'

        self.login(CURRENT_USER, PASSWORD)

        curr_alertemails = userApi.get_alertemails()
        self.assertEqual( len(curr_alertemails), 3 )

        # empty applicants
        data1 = {
            'applicant': [],
            'next': CURRENT_NEXT
        }

        response = self.client.post(reverse('instructors:applicants_send_email') + '?next=' + CURRENT_NEXT, data=urlencode(data1, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertEqual(messages[0], 'An error occurred. Please select applicants, then try again.')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        data2 = {
            'applicant': ['100', '80'],
            'session_slug': SESSION,
            'job_slug': CURRENT_JOB,
            'next': CURRENT_NEXT
        }

        response = self.client.post(reverse('instructors:applicants_send_email') + '?next=' + CURRENT_NEXT, data=urlencode(data2, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)
        self.assertEqual(response.url, reverse('instructors:applicants_send_email_confirmation') + '?next=' + CURRENT_NEXT)

        response = self.client.get(response.url)
        session = self.client.session
        self.assertEqual(session['applicants_form_data']['applicants'], data2['applicant'])
        self.assertEqual(session['applicants_form_data']['session_slug'], SESSION)
        self.assertEqual(session['applicants_form_data']['job_slug'], CURRENT_JOB)

        next1 = '?next=/instructors/sessions/2019-w11/jobs/apbi-200-002-introduction-to-soil-science-w1/applicants/summary-applicants/'
        next2 = '?next=/instructors/sessions/2019-w1/jobs/apbi-200-009-introduction-to-soil-science-w1/applicants/summary-applicants/'
        next3 = '?next=/instructors/sessions/2019-w1/jobs/apbi-200-002-introduction-to-soil-science-w1/applicantsss/summary-applicants/'
        next4 = '?nex=//instructors/sessions/2019-w1/jobs/apbi-200-002-introduction-to-soil-science-w1/applicants/summary-applicantssss/'
        next5 = '?/instructors/sessions/2019-w1/jobs/apbi-200-002-introduction-to-soil-science-w1/applicants/summary-applicants/'

        response1 = self.client.get( reverse('instructors:applicants_send_email_confirmation') + next1 )
        self.assertEqual(response1.status_code, 404)
        response2 = self.client.get( reverse('instructors:applicants_send_email_confirmation') + next2 )
        self.assertEqual(response2.status_code, 404)
        response3 = self.client.get( reverse('instructors:applicants_send_email_confirmation') + next3 )
        self.assertEqual(response3.status_code, 404)
        response4 = self.client.get( reverse('instructors:applicants_send_email_confirmation') + next4 )
        self.assertEqual(response4.status_code, 404)
        response5 = self.client.get( reverse('instructors:applicants_send_email_confirmation') + next5 )
        self.assertEqual(response5.status_code, 404)

        applicant_ids = []
        user_emails = []
        for applicant in response.context['applicants']:
            applicant_ids.append( str(applicant.id) )
            user_emails.append(applicant.email)

        self.assertEqual(len(response.context['applicants']), len(data2['applicant']))
        self.assertEqual(response.context['sender'], settings.EMAIL_FROM)
        self.assertEqual(response.context['receiver'], ['user100.test@example.com', 'user80.test@example.com'])
        self.assertEqual(applicant_ids, data2['applicant'])
        self.assertEqual(response.context['email_form']['title'], 'Please contact {0} to explore potential TA role')
        self.assertEqual(response.context['email_form']['message'], '<div>\n        <p>Hello {5},</p>\n        <p>{0} {1} would like to discuss the possibility of a TA role with you, for {4} in {3}. Please email this instructor if you are interested:</p>\n        <ul>\n            <li>Full Name: {0} {1}</li>\n            <li>Email: {2}</li>\n        </ul>\n        <p><strong>Please do not reply directly to this email.</strong></p>\n        <p>Best regards,</p>\n        <p>LFS TA Application System</p>\n        </div>')
        self.assertEqual(response.context['sample_email']['title'], 'Please contact User22 to explore potential TA role')
        self.assertEqual(response.context['sample_email']['message'],  '<div>\n        <p>Hello User100 Test,</p>\n        <p>User22 Ins would like to discuss the possibility of a TA role with you, for APBI 265 001 in 2019 W1. Please email this instructor if you are interested:</p>\n        <ul>\n            <li>Full Name: User22 Ins</li>\n            <li>Email: user22.ins@example.com</li>\n        </ul>\n        <p><strong>Please do not reply directly to this email.</strong></p>\n        <p>Best regards,</p>\n        <p>LFS TA Application System</p>\n        </div>')

        self.assertEqual(response.context['next'], CURRENT_NEXT)

        data3 = {
            'next': CURRENT_NEXT
        }
        response = self.client.post(reverse('instructors:applicants_send_email_confirmation') + '?next=' + CURRENT_NEXT, data=urlencode(data3, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertEqual(messages[0], 'Success! Email has been sent to user100.test@example.com, user80.test@example.com')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual( len(userApi.get_alertemails()), len(curr_alertemails) + len(user_emails) )


    def test_email_history(self):
        print('- Test: Display all of alert email sent to students')

        CURRENT_USER = 'user22.ins'
        self.login(CURRENT_USER, PASSWORD)

        response = self.client.get(reverse('instructors:show_email_history'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, CURRENT_USER)
        self.assertEqual(response.context['loggedin_user'].roles, ['Instructor'])
        self.assertEqual( len(response.context['emails']), 3 )

        expect = [
            {
                'year': '2019',
                'term': 'W1',
                'job': 'APBI 428 99C',
                'receiver': 'User66 Test <user66.test@example.com>'
            },
            {
                'year': '2019',
                'term': 'W1',
                'job': 'APBI 265 001',
                'receiver': 'User70 Test <user70.test@example.com>'
            },
            {
                'year': '2019',
                'term': 'W1',
                'job': 'APBI 265 001',
                'receiver': 'User66 Test <user66.test@example.com>'
            }
        ]
        c = 0
        for email in response.context['emails']:
            self.assertEqual(email.year, expect[c]['year'])
            self.assertEqual(email.term, expect[c]['term'])
            self.assertEqual("{0} {1} {2}".format(email.job_code, email.job_number, email.job_section), expect[c]['job'])
            self.assertEqual(email.receiver, expect[c]['receiver'])
            c += 1
