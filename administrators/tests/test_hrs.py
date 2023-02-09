from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.contrib.messages import get_messages
from urllib.parse import urlencode
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
import json

from administrators.models import *
from users.models import *
from administrators import api as adminApi
from users import api as userApi

import datetime as dt
from datetime import datetime, timedelta
from django.utils.timezone import get_current_timezone

from administrators.tests.test_sessions import LOGIN_URL, ContentType, DATA, USERS, PASSWORD, SESSION, JOB, APP, COURSE
from students.tests.test_views import random_with_N_digits

ALL_USER = '?next=' + reverse('administrators:all_users') + '?page=2&p=All%20Users&t=basic'
DASHBOARD_USER = '?next=' + reverse('administrators:applications_dashboard') + '?page=2&p=Dashboard&t=basic'

STUDENT = 'user80.test'
OBSERVER = 'user120.test'


class HRTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        print('\nHR testing has started ==>')
        cls.user = userApi.get_user(USERS[0], 'username')
        cls.testing_resume = os.path.join(settings.BASE_DIR, 'users', 'tests', 'files', 'resumeguide200914341.pdf')
        cls.testing_sin = os.path.join(settings.BASE_DIR, 'users', 'tests', 'files', 'karsten-wurth-9qvZSH_NOQs-unsplash.jpg')
        cls.testing_study_permit = os.path.join(settings.BASE_DIR, 'users', 'tests', 'files', 'lucas-davies-3aubsNmGuLE-unsplash.jpg')

    def login(self, username=None, password=None):
        if username and password:
            self.client.post(LOGIN_URL, data={'username': username, 'password': password})
        else:
            self.client.post(LOGIN_URL, data={'username': self.user.username, 'password': PASSWORD})

    def messages(self, res):
        return [m.message for m in get_messages(res.wsgi_request)]

    def submit_resume(self, username):
        ''' Submit resume '''
        self.login(USERS[2], PASSWORD)

        RESUME = self.testing_resume

        user = userApi.get_user(username, 'username')
        data = {
            'user': user.id,
            'uploaded': SimpleUploadedFile('resume.pdf', open(RESUME, 'rb').read(), content_type='application/pdf')
        }
        response = self.client.post( reverse('students:upload_resume') + '?next=/students/&p=Edit%20Profile&t=resume', data=data, format='multipart')
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:show_profile') + '?next=/students/&p=Edit%20Profile&t=resume')
        self.assertRedirects(response, response.url)

        resume = userApi.has_user_resume_created(user)
        self.assertIsNotNone(resume)


    def submit_confiential_information_international_complete(self, username):
        ''' Submit confidential information '''
        self.login(USERS[2], PASSWORD)

        SIN = self.testing_sin
        STUDY_PERMIT = self.testing_study_permit

        user = userApi.get_user(username, 'username')
        data = {
            'user': user.id,
            'nationality': '1'
        }
        response = self.client.post( reverse('students:check_confidentiality'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Please submit your information' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)
        data = {
            'user': user.id,
            'nationality': data['nationality'],
            'date_of_birth': '2000-01-01',
            'employee_number': random_with_N_digits(7),
            'sin': SimpleUploadedFile('sin.jpg', open(SIN, 'rb').read(), content_type='image/jpeg'),
            'sin_expiry_date': '2030-01-01',
            'study_permit': SimpleUploadedFile('study_permit.jpg', open(STUDY_PERMIT, 'rb').read(), content_type='image/jpeg'),
            'study_permit_expiry_date': '2030-01-01'
        }
        response = self.client.post( reverse('students:submit_confidentiality'), data=data, format='multipart' )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

    def delete_document(self, user, list, option='domestic'):
        ''' Delete a list of document '''
        if 'resume' in list:
            userApi.delete_user_resume(user)

        if 'sin' in list:
            if option == 'international':
                userApi.delete_user_sin(user, '1')
            else:
                userApi.delete_user_sin(user)

        if 'study_permit' in list:
            if option == 'international':
                userApi.delete_user_study_permit(user, '1')
            else:
                userApi.delete_user_study_permit(user)

    def test_view_url_exists_at_desired_location(self):
        print('- Test: view url exists at desired location')

        response = self.client.get( reverse('administrators:all_users') )
        self.assertEqual(response.status_code, 302)

        response = self.client.get( reverse('administrators:create_user') )
        self.assertEqual(response.status_code, 302)

        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + ALL_USER )
        self.assertEqual(response.status_code, 302)

        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + DASHBOARD_USER )
        self.assertEqual(response.status_code, 302)

        self.login()

        response = self.client.get( reverse('administrators:all_users') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:create_user') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + ALL_USER )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + '?next=/administrators/hr/users/all/?page=2&p=all%20Users&t=basic' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + '?next=/administrators/hr/users/all/?page=2&p=All%20User&t=basic' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + '?next=/administrators/applications/dashboard/&p=Dashboardd&t=basic' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + '?next=/administrators/applications/dashboard/&p=Dashboard&t=basicd' )
        self.assertEqual(response.status_code, 404)

    def test_all_users(self):
        print('- Test: get all users')
        self.login()
        response = self.client.get(reverse('administrators:all_users'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['users']), settings.PAGE_SIZE )
        self.assertEqual( len(userApi.get_users()), 164 )

    def test_show_user(self):
        print('- Test: show a user')
        self.login()

        next = '?next=/administrators/{0}/&p={1}&t={2}'
        next_wrong = '?nex=/administrators/{0}/&p={1}&t={2}'
        next_page_wrong = '?next=/administrators/{0}/&a={1}&t={2}'
        next_tab_wrong = '?next=/administrators/{0}/&p={1}&j={2}'

        # Dashboard
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_wrong.format('applications/dashboard', 'Dashboard', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_page_wrong.format('applications/dashboard', 'Dashboard', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_tab_wrong.format('applications/dashboard', 'Dashboard', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/dashboarrd', 'Dashboard', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/dashboard', 'Dashboar', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/dashboard', 'Dashboard', 'basid') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/dashboard', 'Dashboard', 'basic') )
        self.assertEqual(response.status_code, 200)

        # All Applications
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_wrong.format('applications/all', 'All Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_page_wrong.format('applications/all', 'All Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_tab_wrong.format('applications/all', 'All Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/alll', 'All Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/all', 'All Application', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/all', 'All Applications', 'basid') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/all', 'All Applications', 'basic') )
        self.assertEqual(response.status_code, 200)

        # Selected Applications
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_wrong.format('applications/selected', 'Selected Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_page_wrong.format('applications/selected', 'Selected Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_tab_wrong.format('applications/selected', 'Selected Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/selectedd', 'Selected Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/selected', 'SelectedApplications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/selected', 'Selected Applications', 'basid') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/selected', 'Selected Applications', 'basic') )
        self.assertEqual(response.status_code, 200)

        # Offered Applications
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_wrong.format('applications/offered', 'Offered Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_page_wrong.format('applications/offered', 'Offered Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_tab_wrong.format('applications/offered', 'Offered Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/offere', 'Offered Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/offered', 'Offerd Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/offered', 'Offered Applications', 'basid') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/offered', 'Offered Applications', 'basic') )
        self.assertEqual(response.status_code, 200)

        # Accepted Applications
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_wrong.format('applications/accepted', 'Accepted Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_page_wrong.format('applications/accepted', 'Accepted Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_tab_wrong.format('applications/accepted', 'Accepted Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/acceped', 'Accepted Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/accepted', 'Accepted Applicatons', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/accepted', 'Accepted Applications', 'basid') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/accepted', 'Accepted Applications', 'basic') )
        self.assertEqual(response.status_code, 200)

        # Declined Applications
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_wrong.format('applications/declined', 'Declined Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_page_wrong.format('applications/declined', 'Declined Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_tab_wrong.format('applications/declined', 'Declined Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/dclined', 'Declined Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/declined', 'Decined Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/declined', 'Declined Applications', 'basid') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/declined', 'Declined Applications', 'basic') )
        self.assertEqual(response.status_code, 200)

        # Terminated Applications
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_wrong.format('applications/terminated', 'Terminated Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_page_wrong.format('applications/terminated', 'Terminated Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_tab_wrong.format('applications/terminated', 'Terminated Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/terminatedd', 'Terminated Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/terminated', 'Terminated Application', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/terminated', 'Terminated Applications', 'basid') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/terminated', 'Terminated Applications', 'basic') )
        self.assertEqual(response.status_code, 200)

        # All Users
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_wrong.format('hr/users/all', 'All Users', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_page_wrong.format('hr/users/all', 'All Users', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_tab_wrong.format('hr/users/all', 'All Users', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('hr/users/alll', 'All Users', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('hr/users/all', 'All User', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('hr/users/all', 'All Users', 'basid') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('hr/users/all', 'All Users', 'basic') )
        self.assertEqual(response.status_code, 200)

        # Jobs by Instructor
        response = self.client.get( reverse('users:show_user', args=[USERS[1]]) + next_wrong.format('jobs/instructor', 'Jobs by Instructor', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[1]]) + next_page_wrong.format('jobs/instructor', 'Jobs by Instructor', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[1]]) + next_tab_wrong.format('jobs/instructor', 'Jobs by Instructor', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[1]]) + next.format('jobs/instructorr', 'Jobs by Instructor', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[1]]) + next.format('jobs/instructor', 'Jobs byInstructor', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[1]]) + next.format('jobs/instructor', 'Jobs by Instructor', 'basid') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[1]]) + next.format('jobs/instructor', 'Jobs by Instructor', 'basic') )
        self.assertEqual(response.status_code, 200)
        response = self.client.get( reverse('users:show_user', args=[USERS[1]]) + next.format('jobs/instructor', 'Jobs by Instructor', 'additional') )
        self.assertEqual(response.status_code, 200)
        response = self.client.get( reverse('users:show_user', args=[USERS[1]]) + next.format('jobs/instructor', 'Jobs by Instructor', 'confidential') )
        self.assertEqual(response.status_code, 200)
        response = self.client.get( reverse('users:show_user', args=[USERS[1]]) + next.format('jobs/instructor', 'Jobs by Instructor', 'resume') )
        self.assertEqual(response.status_code, 404)

        # Jobs by Student
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_wrong.format('jobs/student', 'Jobs by Student', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_page_wrong.format('jobs/student', 'Jobs by Student', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_tab_wrong.format('jobs/student', 'Jobs by Student', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('job/student', 'Jobs by Student', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('jobs/student', 'Jobs by tudent', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('jobs/student', 'Jobs by Student', 'basid') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('jobs/student', 'Jobs by Student', 'basic') )
        self.assertEqual(response.status_code, 200)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('jobs/student', 'Jobs by Student', 'additional') )
        self.assertEqual(response.status_code, 200)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('jobs/student', 'Jobs by Student', 'confidential') )
        self.assertEqual(response.status_code, 200)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('jobs/student', 'Jobs by Student', 'resume') )
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse('users:show_user', args=[USERS[2]]) + ALL_USER)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['selected_user'].username, USERS[2])

    def test_show_user_not_exists(self):
        print('- Test: show no existing user ')
        self.login()

        response = self.client.get(reverse('users:show_user', args=['user10000.test']) + ALL_USER)
        self.assertEqual(response.status_code, 404)


    def test_edit_user_role_change(self):
        print('- Test: edit a user with role change')
        self.login()

        user = userApi.get_user(USERS[2], 'username')
        user_first_role = user.profile.roles.all()[0]
        self.assertEqual(user_first_role.name, Role.STUDENT)

        data1 = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'username': user.username,
            'user': user.id,
            'roles': [],
            'next': reverse('administrators:all_users') + '?page=2'
        }
        response = self.client.post(reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER, data=urlencode(data1, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER)
        self.assertRedirects(response, response.url)

        data2 = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'username': user.username,
            'user': user.id,
            'roles': ['2', '3'],
            'next': reverse('administrators:all_users') + '?page=2'
        }

        response = self.client.post(reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER, data=urlencode(data2, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:all_users') + '?page=2')
        self.assertRedirects(response, response.url)

    def test_edit_user(self):
        print('- Test: edit an user')
        self.login()

        user = userApi.get_user(USERS[2], 'username')
        user_first_role = user.profile.roles.all()[0]
        self.assertEqual(user_first_role.name, Role.STUDENT)

        # Missing first name, last name, email, username
        data0 = {
            'user': user.id,
            'student_number': '12222222',
            'employee_number': '12345678',
            'is_superuser': False,
            'preferred_name': 'new name',
            'roles': ['4'],
            'next': '/administrators/hr/user/all/?page=2'
        }
        response = self.client.post(reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER, data=urlencode(data0, True), content_type=ContentType)
        self.assertEqual(response.status_code, 404)


    def test_edit_user1(self):
        print('- Test: edit an user1')
        self.login()

        user = userApi.get_user(USERS[2], 'username')
        user_first_role = user.profile.roles.all()[0]
        self.assertEqual(user_first_role.name, Role.STUDENT)

        # Missing first name, last name, email, username
        data1 = {
            'user': user.id,
            'student_number': '12222222',
            'employee_number': '12345678',
            'is_superuser': False,
            'preferred_name': 'new name',
            'roles': ['4'],
            'next': reverse('administrators:all_users') + '?page=2'
        }
        response = self.client.post(reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER, data=urlencode(data1, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER)
        self.assertRedirects(response, response.url)


    def test_edit_user2(self):
        print('- Test: edit an user2')
        self.login()

        user = userApi.get_user(USERS[2], 'username')
        user_first_role = user.profile.roles.all()[0]
        self.assertEqual(user_first_role.name, Role.STUDENT)

        # Missing last name, username, email
        data2 = {
            'user': user.id,
            'first_name': 'change first name',
            'student_number': '12222222',
            'is_new_employee': True,
            'employee_number': '12345678',
            'is_superuser': False,
            'preferred_name': 'new name',
            'roles': ['4'],
            'next': reverse('administrators:all_users') + '?page=2'
        }
        response = self.client.post(reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER, data=urlencode(data2, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER)
        self.assertRedirects(response, response.url)

    def test_edit_user3(self):
        print('- Test: edit an user3')
        self.login()

        user = userApi.get_user(USERS[2], 'username')
        user_first_role = user.profile.roles.all()[0]
        self.assertEqual(user_first_role.name, Role.STUDENT)

        # Missing email and username
        data3 = {
            'user': user.id,
            'first_name': 'change first name',
            'last_name': 'change last name',
            'student_number': '12222222',
            'is_new_employee': True,
            'employee_number': '12345678',
            'is_superuser': False,
            'preferred_name': 'new name',
            'roles': ['4'],
            'next': reverse('administrators:all_users') + '?page=2'
        }
        response = self.client.post(reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER, data=urlencode(data3, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER)
        self.assertRedirects(response, response.url)

    def test_edit_user4(self):
        print('- Test: edit an user4')
        self.login()

        user = userApi.get_user(USERS[2], 'username')
        user_first_role = user.profile.roles.all()[0]
        self.assertEqual(user_first_role.name, Role.STUDENT)

        # Missing username
        data4 = {
            'user': user.id,
            'first_name': 'change first name',
            'last_name': 'change last name',
            'email': 'new.email@example.com',
            'student_number': '12222222',
            'is_new_employee': True,
            'employee_number': '12345678',
            'is_superuser': False,
            'preferred_name': 'new name',
            'roles': ['4'],
            'next': reverse('administrators:all_users') + '?page=2'
        }
        response = self.client.post(reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER, data=urlencode(data4, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER)
        self.assertRedirects(response, response.url)


    def test_edit_user5(self):
        print('- Test: edit an user5')
        self.login()

        user = userApi.get_user(USERS[2], 'username')
        user_first_role = user.profile.roles.all()[0]
        self.assertEqual(user_first_role.name, Role.STUDENT)

        # Wrong employee number
        data5 = {
            'user': user.id,
            'first_name': 'change first name',
            'last_name': 'change last name',
            'email': 'new.email@example.com',
            'username': 'new.username',
            'student_number': '12222222',
            'is_new_employee': True,
            'employee_number': '12345678',
            'is_superuser': False,
            'preferred_name': 'new name',
            'roles': ['4'],
            'next': reverse('administrators:all_users') + '?page=2'
        }
        response = self.client.post(reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER, data=urlencode(data5, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER)
        self.assertRedirects(response, response.url)


    def test_edit_user6(self):
        print('- Test: edit an user6')
        self.login()

        user = userApi.get_user(USERS[2], 'username')
        user_first_role = user.profile.roles.all()[0]
        self.assertEqual(user_first_role.name, Role.STUDENT)

        # Wrong employee number
        data6 = {
            'user': user.id,
            'first_name': 'change first name',
            'last_name': 'change last name',
            'email': 'new.email@example.com',
            'username': 'new.username',
            'student_number': '12222222',
            'is_new_employee': True,
            'employee_number': 'new.employee',
            'is_superuser': False,
            'preferred_name': 'new name',
            'roles': ['4'],
            'next': reverse('administrators:all_users') + '?page=2'
        }
        response = self.client.post(reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER, data=urlencode(data6, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER)
        self.assertRedirects(response, response.url)


    def test_edit_user7(self):
        print('- Test: edit an user7')
        self.login()

        user = userApi.get_user(USERS[2], 'username')
        user_first_role = user.profile.roles.all()[0]
        self.assertEqual(user_first_role.name, Role.STUDENT)

        # Wrong employee number
        data7 = {
            'user': user.id,
            'first_name': 'change first name',
            'last_name': 'change last name',
            'email': 'new.email@example.com',
            'username': 'new.username',
            'student_number': '12222222',
            'is_new_employee': True,
            'employee_number': '123',
            'is_superuser': False,
            'preferred_name': 'new name',
            'roles': ['4'],
            'next': reverse('administrators:all_users') + '?page=2'
        }
        response = self.client.post(reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER, data=urlencode(data7, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER)
        self.assertRedirects(response, response.url)


    def test_edit_user8(self):
        print('- Test: edit an user8')
        self.login()

        user = userApi.get_user(USERS[2], 'username')
        user_first_role = user.profile.roles.all()[0]
        self.assertEqual(user_first_role.name, Role.STUDENT)

        # Wrong student number
        data8 = {
            'user': user.id,
            'first_name': 'change first name',
            'last_name': 'change last name',
            'email': 'new.email@example.com',
            'username': 'new.username',
            'student_number': 'new.student',
            'is_new_employee': True,
            'employee_number': '1234777',
            'is_superuser': False,
            'preferred_name': 'new name',
            'roles': ['4'],
            'next': reverse('administrators:all_users') + '?page=2'
        }
        response = self.client.post(reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER, data=urlencode(data8, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER)
        self.assertRedirects(response, response.url)


    def test_edit_user9(self):
        print('- Test: edit an user9')
        self.login()

        user = userApi.get_user(USERS[2], 'username')
        user_first_role = user.profile.roles.all()[0]
        self.assertEqual(user_first_role.name, Role.STUDENT)

        # Wrong student number
        data9 = {
            'user': user.id,
            'first_name': 'change first name',
            'last_name': 'change last name',
            'email': 'new.email@example.com',
            'username': 'new.username',
            'student_number': '123',
            'is_new_employee': True,
            'employee_number': '1234777',
            'is_superuser': False,
            'preferred_name': 'new name',
            'roles': ['4'],
            'next': reverse('administrators:all_users') + '?page=2'
        }
        response = self.client.post(reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER, data=urlencode(data9, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER)
        self.assertRedirects(response, response.url)


    def test_edit_user10(self):
        print('- Test: edit an user10')
        self.login()

        user = userApi.get_user(USERS[2], 'username')
        user_first_role = user.profile.roles.all()[0]
        self.assertEqual(user_first_role.name, Role.STUDENT)

        data10 = {
            'user': user.id,
            'first_name': 'change first name',
            'last_name': 'change last name',
            'email': 'new.email@example.com',
            'username': 'new.username',
            'student_number': '12345670',
            'is_new_employee': False,
            'employee_number': '1234567',
            'is_superuser': False,
            'preferred_name': 'new name',
            'roles': ['4'],
            'next': reverse('administrators:all_users') + '?page=2'
        }
        response = self.client.post(reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER, data=urlencode(data10, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:all_users') + '?page=2')
        self.assertRedirects(response, response.url)

        u = userApi.get_user(user.id)
        self.assertEqual(u.id, data10['user'])
        self.assertEqual(u.first_name, data10['first_name'])
        self.assertEqual(u.last_name, data10['last_name'])
        self.assertEqual(u.email, data10['email'])
        self.assertEqual(u.username, data10['username'])
        self.assertEqual(u.profile.student_number, data10['student_number'])
        self.assertFalse(u.confidentiality.is_new_employee)
        self.assertEqual(u.confidentiality.employee_number, data10['employee_number'])
        self.assertFalse(u.is_superuser)
        self.assertEqual(u.profile.preferred_name, data10['preferred_name'])
        self.assertEqual(u.profile.roles.all()[0].name, Role.INSTRUCTOR)
        self.assertIsNotNone( userApi.has_user_confidentiality_created(u) )


    def test_delete_user(self):
        print('- Test: delete an user')
        self.login()

        user = userApi.get_user(USERS[2], 'username')

        response = self.client.get(reverse('administrators:delete_user_confirmation', args=[USERS[2]]) + ALL_USER)
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['users']), 164 )

        data = {
            'user': user.id,
            'next': reverse('administrators:all_users') + '?page=2'
        }
        response = self.client.post(reverse('administrators:delete_user_confirmation', args=[USERS[2]]) + ALL_USER, data=urlencode(data), content_type=ContentType)

        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('users:show_user', args=[USERS[2]]) + ALL_USER)
        self.assertEqual(response.status_code, 200)

        self.assertIsNotNone(userApi.user_exists_username(user.username))
        self.assertFalse(userApi.resume_exists(user))
        self.assertFalse(userApi.confidentiality_exists(user))
        self.assertIsNone( userApi.has_user_confidentiality_created(user) )

    def test_destroy_user_contents(self):
        print('- Test: destroy user contents')

        self.submit_resume(USERS[2])
        self.submit_confiential_information_international_complete(USERS[2])

        self.login()

        user = userApi.get_user(USERS[2], 'username')
        user.last_login = dt.datetime(2000, 1, 1, 0, 0, 0, 0, tzinfo=get_current_timezone())
        user.save(update_fields=['last_login'])

        self.assertTrue(userApi.resume_exists(user))
        self.assertTrue(userApi.confidentiality_exists(user))
        self.assertIsNotNone( userApi.has_user_confidentiality_created(user) )

        self.assertTrue( bool(user.confidentiality.sin) )
        self.assertTrue( bool(user.confidentiality.study_permit) )

        self.assertEqual(user.last_login.strftime('%Y-%m-%d'), dt.date(2000, 1, 1).strftime('%Y-%m-%d'))

        response = self.client.get(reverse('administrators:destroy_user_contents'))
        self.assertEqual(response.status_code, 200)

        target_date = datetime.now(tz=get_current_timezone()) - timedelta(days=3*365)
        self.assertEqual(response.context['target_date'], target_date.strftime('%Y-%m-%d'))
        self.assertEqual(response.context['users'][0].id, 100)
        self.assertEqual(response.context['users'][0].username, 'user100.test')

        data = {
            'user': [str(response.context['users'][0].id)]
        }

        response = self.client.post(reverse('administrators:destroy_user_contents'), data=urlencode(data, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue(messages[0], "Success! The contents of User IDs ['100'] are deleted")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:destroy_user_contents'))
        self.assertRedirects(response, response.url)

        user = userApi.get_user(100)
        self.assertIsNotNone(userApi.user_exists_username(user.username))
        self.assertTrue(userApi.profile_exists(user))

        self.assertIsNone(user.profile.qualifications)
        self.assertIsNone(user.profile.prior_employment)
        self.assertIsNone(user.profile.special_considerations)
        self.assertIsNone(user.profile.status)
        self.assertIsNone(user.profile.program)
        self.assertIsNone(user.profile.program_others)
        self.assertIsNone(user.profile.graduation_date)
        self.assertIsNone(user.profile.degree_details)
        self.assertIsNone(user.profile.training_details)
        self.assertIsNone(user.profile.lfs_ta_training)
        self.assertIsNone(user.profile.lfs_ta_training_details)
        self.assertIsNone(user.profile.ta_experience)
        self.assertIsNone(user.profile.ta_experience_details)
        self.assertTrue(user.profile.is_trimmed)

        self.assertFalse(userApi.resume_exists(user))
        self.assertFalse(userApi.confidentiality_exists(user))
        self.assertIsNone( userApi.has_user_confidentiality_created(user) )

        self.delete_document(USERS[2], ['sin', 'study_permit'], 'international')


    def test_create_user(self):
        print('- Test: create an user')
        self.login()

        data = {
            'first_name': 'firstname',
            'last_name': 'lastname',
            'email': 'email@example.com',
            'username': 'firstname_lastname',
            'is_new_employee': True,
            'employee_number': '1233344',
            'student_number': '12345667',
            #'puid': '',
            'is_superuser': False,
            'preferred_name': 'preferredname',
            'roles': ['5']
        }

        response = self.client.post(reverse('administrators:create_user'), data=urlencode(data, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        u = userApi.get_user(data['username'], 'username')
        self.assertEqual(u.username, data['username'])
        self.assertTrue(userApi.profile_exists_by_username(u.username))
        self.assertEqual(u.first_name, data['first_name'])
        self.assertEqual(u.last_name, data['last_name'])
        self.assertEqual(u.email, data['email'])
        self.assertEqual(u.username, data['username'])
        self.assertEqual(u.profile.student_number, data['student_number'])
        #self.assertIsNone(u.profile.puid, data['puid'])
        self.assertTrue(u.confidentiality.is_new_employee)
        self.assertEqual(u.confidentiality.employee_number, data['employee_number'])
        self.assertFalse(u.is_superuser)
        self.assertEqual(u.profile.preferred_name, data['preferred_name'])
        self.assertEqual(u.profile.roles.all()[0].name, Role.STUDENT)
        self.assertIsNotNone( userApi.has_user_confidentiality_created(u) )


    def test_create_user_missing_values1(self):
        print('- Test: create an user with missing values 1')
        self.login()

        data = {
            'student_number': '923423434',
            'preferred_name': 'new preferred name'
        }
        response = self.client.post(reverse('administrators:create_user'), data=urlencode(data, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:create_user'))
        self.assertRedirects(response, response.url)


    def test_create_user_missing_values2(self):
        print('- Test: create an user with missing values 2')
        self.login()

        data2 = {
            'student_number': 'abcdefg',
            'preferred_name': 'new preferred name'
        }
        response = self.client.post(reverse('administrators:create_user'), data=urlencode(data2, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:create_user'))
        self.assertRedirects(response, response.url)


    def test_create_user_missing_values3(self):
        print('- Test: create an user with missing values 3')
        self.login()

        data3 = {
            'student_number': '92342343',
            'preferred_name': 'new preferred name',
            'first_name': 'new first name'
        }
        response = self.client.post(reverse('administrators:create_user'), data=urlencode(data3, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:create_user'))
        self.assertRedirects(response, response.url)


    def test_create_user_missing_values4(self):
        print('- Test: create an user with missing values 4')
        self.login()

        data4 = {
            'student_number': '92342343',
            'preferred_name': 'new preferred name',
            'first_name': 'new first name',
            'last_name': 'new last name'
        }
        response = self.client.post(reverse('administrators:create_user'), data=urlencode(data4, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:create_user'))
        self.assertRedirects(response, response.url)


    def test_create_user_missing_values5(self):
        print('- Test: create an user with missing values 5')
        self.login()

        data5 = {
            'student_number': '92342343',
            'preferred_name': 'new preferred name',
            'first_name': 'new first name',
            'last_name': 'new last name',
            'email': 'new.email@example.com'
        }
        response = self.client.post(reverse('administrators:create_user'), data=urlencode(data5, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:create_user'))
        self.assertRedirects(response, response.url)


    def test_create_user_missing_values6(self):
        print('- Test: create an user with missing values 6')
        self.login()

        data6 = {
            'student_number': '92342343',
            'preferred_name': 'new preferred name',
            'first_name': 'new first name',
            'last_name': 'new last name',
            'email': 'new.email@example.com',
            'roles': ['5']
        }
        response = self.client.post(reverse('administrators:create_user'), data=urlencode(data6, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:create_user'))
        self.assertRedirects(response, response.url)


    def test_create_user_missing_values7(self):
        print('- Test: create an user with missing values 7')
        self.login()

        data7 = {
            'student_number': '92342343',
            'preferred_name': 'new preferred name',
            'first_name': 'new first name',
            'last_name': 'new last name',
            'email': 'new.email@example.com',
            'roles': ['5'],
            'employee_number': '5'
        }
        response = self.client.post(reverse('administrators:create_user'), data=urlencode(data7, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:create_user'))
        self.assertRedirects(response, response.url)


    def test_create_user_missing_values8(self):
        print('- Test: create an user with missing values 8')
        self.login()

        data8 = {
            'student_number': '92342343',
            'preferred_name': 'new preferred name',
            'first_name': 'new first name',
            'last_name': 'new last name',
            'email': 'new.email@example.com',
            'roles': ['5'],
            'employee_number': 'gdsddfds',
            'is_new_employee': True
        }
        response = self.client.post(reverse('administrators:create_user'), data=urlencode(data8, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:create_user'))
        self.assertRedirects(response, response.url)


    def test_create_user_with_duplicates_username(self):
        print('- Test: create a user with duplicates - username')
        self.login()

        data = {
            'first_name': 'user101',
            'last_name': 'test',
            'email': 'user101.test@example.com',
            'username': STUDENT,
            'roles': ['5'],
            'student_number': None,
            #'puid': '',
            'employee_number': None,
            'is_new_employee': True
        }

        self.assertIsNotNone(userApi.user_exists_username(data['username']))
        self.assertTrue(userApi.profile_exists_by_username(data['username']))

        response = self.client.post(reverse('administrators:create_user'), data=urlencode(data, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)


    def test_create_user_with_duplicates_student_number(self):
        print('- Test: create a user with duplicates - student number')
        self.login()

        data = {
            'first_name': 'test555',
            'last_name': 'user555',
            'email': 'test.user555@example.com',
            'username': 'test.user555',
            'preferred_name': None,
            'student_number': 'AJWUGNUE',
            #'puid': '',
            'employee_number': '1234567',
            'is_new_employee': True,
            'roles': ['5']
        }
        self.assertIsNone(userApi.user_exists_username(data['username']))
        self.assertFalse(userApi.profile_exists_by_username(data['username']))
        response = self.client.post(reverse('administrators:create_user'), data=urlencode(data, True), content_type=ContentType)
        messages = self.messages(response)

        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)


    def test_create_user_with_duplicates_employee_number(self):
        print('- Test: create a user with duplicates - employee number')
        self.login()

        data = {
            'first_name': 'test555',
            'last_name': 'user555',
            'email': 'test.user555@example.com',
            'username': 'test.user555',
            'preferred_name': None,
            'student_number': '1JWUGNU0',
            #'puid': '',
            'employee_number': 'test100',
            'is_new_employee': True,
            'roles': ['5']
        }
        self.assertIsNone(userApi.user_exists_username(data['username']))
        self.assertFalse(userApi.profile_exists_by_username(data['username']))
        response = self.client.post(reverse('administrators:create_user'), data=urlencode(data, True), content_type=ContentType)
        messages = self.messages(response)

        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)


    def test_create_user_via_api(self):
        print('- Test: create a user via api when the function added in SAML')

        data = {
            'first_name': 'test5',
            'last_name': 'user55',
            'email': 'test.user55@example.com',
            'username': 'test.user55',
            'preferred_name': '',
            'student_number': '12345678',
            #'puid': 'TEST00000555',
            'employee_number': '9876521',
            'roles': ['5']
        }
        self.assertIsNone(userApi.user_exists_username(data['username']))
        self.assertFalse(userApi.profile_exists_by_username(data['username']))

        u = userApi.create_user(data)
        self.assertIsNotNone(userApi.user_exists_username(u.username))
        self.assertTrue(userApi.profile_exists_by_username(u.username))
        self.assertEqual(u.username, data['username'])
        self.assertEqual(u.first_name, data['first_name'])
        self.assertEqual(u.last_name, data['last_name'])
        self.assertEqual(u.email, data['email'])
        self.assertEqual(u.username, data['username'])
        self.assertEqual(u.profile.student_number, data['student_number'])
        #self.assertEqual(u.profile.puid, data['puid'])
        self.assertFalse(u.confidentiality.is_new_employee)
        self.assertEqual(u.confidentiality.employee_number, data['employee_number'])
        self.assertFalse(u.is_superuser)
        self.assertIsNone(u.profile.preferred_name)
        self.assertEqual(u.profile.roles.all()[0].name, Role.STUDENT)
        self.assertIsNotNone( userApi.has_user_confidentiality_created(u) )


    def test_create_user_via_api2(self):
        print('- Test: create a user via api when the function added in SAML - if employee number is none, is_new_employee = false')

        data = {
            'first_name': 'test6',
            'last_name': 'user66',
            'email': 'test.user66@example.com',
            'username': 'test.user66',
            'password': 'password',
            'preferred_name': '',
            'student_number': '12345655',
            #'puid': 'TEST00000555',
            'employee_number': None,
            'roles': ['5']
        }
        self.assertIsNone(userApi.user_exists_username(data['username']))
        self.assertFalse(userApi.profile_exists_by_username(data['username']))

        user = userApi.create_user(data)
        self.assertIsNotNone(userApi.user_exists_username(user.username))
        self.assertTrue(userApi.profile_exists_by_username(user.username))
        self.assertEqual(user.username, data['username'])
        self.assertEqual(user.first_name, data['first_name'])
        self.assertEqual(user.last_name, data['last_name'])
        self.assertEqual(user.email, data['email'])
        self.assertEqual(user.username, data['username'])
        self.assertEqual(user.profile.student_number, data['student_number'])
        #self.assertEqual(user.profile.puid, data['puid'])
        self.assertTrue(user.confidentiality.is_new_employee)
        self.assertEqual(user.confidentiality.employee_number, data['employee_number'])
        self.assertFalse(user.is_superuser)
        self.assertIsNone(user.profile.preferred_name)
        self.assertEqual(user.profile.roles.all()[0].name, Role.STUDENT)
        self.assertIsNotNone( userApi.has_user_confidentiality_created(user) )


    def test_change_user_role_success(self):
        print("- Test: change user's role - success")
        self.login()

        user = userApi.get_user(STUDENT, 'username')

        data = {
            'user': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'username': user.username,
            'student_number': '00000001',
            #'puid': user.profile.puid,
            'employee_number': user.confidentiality.employee_number,
            'roles': ['4'],
            'is_new_employee': 'true',
            'next': reverse('administrators:all_users') + '?page=2'
        }
        response = self.client.post(reverse('administrators:edit_user', args=[ data['username'] ]) + ALL_USER, data=urlencode(data, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertEqual(messages[0], 'Success! User information of User80 Test (CWL: user80.test) updated')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:all_users') + '?page=2')
        self.assertRedirects(response, response.url)

        roles = userApi.get_user_roles(user)
        self.assertEqual(roles, ['Instructor'])
        self.assertFalse(user.confidentiality.is_new_employee)


    def test_change_user_role_success_multiples(self):
        print("- Test: change user's role - success - multiple roles")
        self.login()

        user = userApi.get_user(STUDENT, 'username')

        data = {
            'user': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'username': user.username,
            'student_number': '00000001',
            #'puid': user.profile.puid,
            'employee_number': user.confidentiality.employee_number,
            'roles': ['3', '4'],
            'is_new_employee': 'true',
            'next': reverse('administrators:all_users') + '?page=2'
        }
        response = self.client.post(reverse('administrators:edit_user', args=[ data['username'] ]) + ALL_USER, data=urlencode(data, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertEqual(messages[0], 'Success! User information of User80 Test (CWL: user80.test) updated')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:all_users') + '?page=2')
        self.assertRedirects(response, response.url)

        roles = userApi.get_user_roles(user)
        self.assertEqual(roles, ['HR', 'Instructor'])
        self.assertFalse(user.confidentiality.is_new_employee)


    def test_change_user_role_error(self):
        print("- Test: change user's role - error")
        self.login()

        user = userApi.get_user(STUDENT, 'username')

        data = {
            'user': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'username': user.username,
            'student_number': '00000001',
            #'puid': user.profile.puid,
            'employee_number': user.confidentiality.employee_number,
            'roles': [],
            'is_new_employee': 'true',
            'next': reverse('administrators:all_users') + '?page=2'
        }
        response = self.client.post(reverse('administrators:edit_user', args=[ data['username'] ]) + ALL_USER, data=urlencode(data, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertEqual(messages[0], 'An error occurred while updating an User Form. ROLES: This field is required.')


    def test_roles(self):
        print('- Test: Display all roles and create a role')
        self.login()

        response = self.client.get( reverse('administrators:roles') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['roles']), 6 )
        self.assertFalse(response.context['form'].is_bound)

        data = { 'name': 'new role' }
        response = self.client.post( reverse('administrators:roles'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:roles') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['roles']), 7 )
        self.assertEqual(response.context['roles'].last().name, data['name'])

    def test_edit_role(self):
        print('- Test: edit role details')
        self.login()

        slug = 'student'

        data = { 'name': 'updated student' }
        response = self.client.post( reverse('administrators:edit_role', args=[slug]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:roles') )
        self.assertEqual(response.status_code, 200)
        roles = response.context['roles']

        found = 0
        for role in roles:
            if role.slug == 'updated-student':
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_role(self):
        print('- Test: delete a role')
        self.login()

        total_roles = len(userApi.get_roles())

        role_id = 1
        response = self.client.post( reverse('administrators:delete_role'), data=urlencode({ 'role': role_id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:roles'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['roles']), total_roles - 1)

        found = False
        for role in response.context['roles']:
            if role.id == role_id: found = True
        self.assertFalse(found)
