from django.test import TestCase
from django.urls import reverse
from django.contrib.messages import get_messages
from urllib.parse import urlencode

from administrators.models import *
from users.models import *
from administrators import api as adminApi
from users import api as userApi

ContentType='application/x-www-form-urlencoded'

DATA = [
    'administrators/fixtures/applications.json',
    'administrators/fixtures/applicationstatus.json',
    'administrators/fixtures/course_codes.json',
    'administrators/fixtures/course_numbers.json',
    'administrators/fixtures/course_sections.json',
    'administrators/fixtures/courses.json',
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

        response = self.client.get( reverse('administrators:view_confidentiality', args=['admin']) )
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
        for degree in adminApi.get_degrees():
            if degree.profile_set.filter(user_id=user.id ).exists():
                degree_found = True
        self.assertFalse(degree_found)

        training_found = False
        for training in adminApi.get_trainings():
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
