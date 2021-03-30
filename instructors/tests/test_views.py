from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from urllib.parse import urlencode

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

        response = self.client.get( reverse('instructors:show_jobs') + JOBS_NEXT )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('instructors:edit_job', args=[SESSION, JOB]) + JOBS_NEXT )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT )
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


    def test_edit_user_missing_values(self):
        print('- Test to edit the information of an user with missing values')
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
        self.assertEqual(response.url, reverse('instructors:edit_user'))
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
        self.assertEqual(response.url, reverse('instructors:edit_user'))
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
        self.assertEqual(response.url, reverse('instructors:edit_user'))
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
        self.assertEqual(response.url, reverse('instructors:edit_user'))
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
        self.assertEqual(response.url, reverse('instructors:edit_user'))
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

        response = self.client.get( reverse('instructors:edit_job', args=[SESSION, JOB]) + JOBS_WRONG_1 )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('instructors:edit_job', args=[SESSION, JOB]) + JOBS_WRONG_2 )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('instructors:edit_job', args=[SESSION, JOB]) + JOBS_WRONG_2 )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('instructors:edit_job', args=[SESSION, JOB]) + JOBS_NEXT )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USER)
        self.assertEqual(response.context['loggedin_user'].roles, ['Instructor'])
        self.assertEqual(response.context['job'].course.slug, JOB)
        self.assertFalse(response.context['form'].is_bound)
        self.assertEqual(response.context['form'].instance, response.context['job'])
        self.assertEqual( len(response.context['jobs']), 6 )

        data1 = {
            'course_overview': 'course overview',
            'description': 'job description',
            'note': 'job note',
            'next': '/instructors/jobS/?page=2'
        }
        response = self.client.post( reverse('instructors:edit_job', args=[SESSION, JOB]), data=urlencode(data1), content_type=ContentType )
        self.assertEqual(response.status_code, 404)

        data2 = {
            'course_overview': 'course overview',
            'description': 'job description',
            'note': 'job note',
            'next': reverse('instructors:show_jobs') + '?page=2'
        }
        response = self.client.post( reverse('instructors:edit_job', args=[SESSION, JOB]), data=urlencode(data2), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('instructors:show_jobs') + '?page=2')
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('instructors:edit_job', args=[SESSION, JOB]) + JOBS_NEXT )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['job'].course_overview, data2['course_overview'])
        self.assertEqual(response.context['job'].description, data2['description'])
        self.assertEqual(response.context['job'].note, data2['note'])

    def test_show_job(self):
        print('- Test: display a job')
        self.login()

        response = self.client.get( reverse('instructors:show_job', args=[SESSION, JOB]) + JOBS_WRONG_1 )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('instructors:show_job', args=[SESSION, JOB]) + JOBS_WRONG_2 )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('instructors:show_job', args=[SESSION, JOB]) + JOBS_WRONG_2 )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('instructors:show_job', args=[SESSION, JOB]) + JOBS_NEXT )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USER)
        self.assertEqual(response.context['loggedin_user'].roles, ['Instructor'])
        job = response.context['job']
        self.assertEqual(job.session.year, '2019')
        self.assertEqual(job.session.term.code, 'W1')
        self.assertEqual(job.session.slug, SESSION)
        self.assertEqual(job.course.slug, JOB)

    def test_show_applications(self):
        print('- Display applications applied by students')
        self.login()

        job = adminApi.get_job_by_session_slug_job_slug(SESSION, JOB)

        response = self.client.get( reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_WRONG_1 )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_WRONG_2 )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_WRONG_2 )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USER)
        self.assertEqual(response.context['loggedin_user'].roles, ['Instructor'])
        self.assertEqual(response.context['job'].course.slug, JOB)
        self.assertEqual( len(response.context['job'].application_set.all()), 4 )
        self.assertEqual(response.context['job'].application_set.first().instructor_preference, '0')
        self.assertEqual( len(response.context['instructor_preference_choices']), 5 )

        self.assertEqual(response.context['full_job_name'], 'APBI_200_002')
        self.assertEqual(response.context['app_status'], {'none': '0', 'applied': '0', 'selected': '1', 'offered': '2', 'accepted': '3', 'declined': '4', 'cancelled': '5'})
        self.assertEqual(response.context['next'], '/instructors/jobs/?page=2')

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

        response = self.client.get( reverse('instructors:write_note', args=[APP]) + '?nex=' + reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT)
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('instructors:write_note', args=[APP]) + '?next=' + reverse('instructors:show_applications', args=['2019-w11', JOB]) + JOBS_NEXT)
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('instructors:write_note', args=[APP]) + '?next=' + reverse('instructors:show_applications', args=[SESSION, 'apbi-200-002-introduct']) + JOBS_NEXT)
        self.assertEqual(response.status_code, 404)


        data1 = {
            'note': 'new note',
            'next': '?nex=/instructors/sessions/2019-w1/jobs/apbi-200-002-introduction-to-soil-science-w1/applications/?next=/instructors/jobs/'
        }
        response = self.client.post( reverse('instructors:write_note', args=[APP]) + '?next=' + reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT, data=urlencode(data1), content_type=ContentType )
        self.assertEqual(response.status_code, 404)

        data2 = {
            'note': 'new note',
            'next': '?next=/instructor/sessions/2019-w1/jobs/apbi-200-002-introduction-to-soil-science-w1/applications/?next=/instructors/jobs/'
        }
        response = self.client.post( reverse('instructors:write_note', args=[APP]) + '?next=' + reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT, data=urlencode(data2), content_type=ContentType )
        self.assertEqual(response.status_code, 404)

        data3 = {
            'note': 'new note',
            'next': '?next=/instructors/seSsions/2019-w1/jobs/apbi-200-002-introduction-to-soil-science-w1/applications/?next=/instructors/jobs/'
        }
        response = self.client.post( reverse('instructors:write_note', args=[APP]) + '?next=' + reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT, data=urlencode(data3), content_type=ContentType )
        self.assertEqual(response.status_code, 404)

        data4 = {
            'note': 'new note',
            'next': '?next=/instructors/seSsions/2019-w3/jobs/apbi-200-002-introduction-to-soil-science-w1/applications/?next=/instructors/jobs/'
        }
        response = self.client.post( reverse('instructors:write_note', args=[APP]) + '?next=' + reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT, data=urlencode(data4), content_type=ContentType )
        self.assertEqual(response.status_code, 404)

        data5 = {
            'note': 'new note',
            'next': '?next=/instructors/sessions/2019-w1/jobs/apbi-200-002-introduction-to-soil-science-w3/applications/?next=/instructors/jobs/'
        }
        response = self.client.post( reverse('instructors:write_note', args=[APP]) + '?next=' + reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT, data=urlencode(data5), content_type=ContentType )
        self.assertEqual(response.status_code, 404)

        data6 = {
            'note': 'new note',
            'next': APP_PATH
        }
        response = self.client.post( reverse('instructors:write_note', args=[APP]) + '?next=' + reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT, data=urlencode(data6), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, APP_PATH)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('instructors:show_applications', args=[SESSION, JOB]) + '?next=' + APP_PATH)
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
        self.assertEqual(appl.note, data6['note'])
