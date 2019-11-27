from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from urllib.parse import urlencode

from administrators.models import *
from users.models import *
from administrators import api as adminApi
from users import api as userApi

from administrators.tests.test_views import LOGIN_URL, ContentType, DATA, SESSION
from django.core.files.uploadedfile import SimpleUploadedFile


USER = 'user3.admin'
JOB = 'apbi-200-002-introduction-to-soil-science-w1'
STUDENT = 'user66.test'

class HumanResourceTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        cls.user = userApi.get_user(USER, 'username')

    def login(self, username=None, password=None):
        if username and password:
            self.client.post(LOGIN_URL, data={'username': username, 'password': password})
        else:
            self.client.post(LOGIN_URL, data={'username': self.user.username, 'password': self.user.password})

    def messages(self, res):
        return [m.message for m in get_messages(res.wsgi_request)]

    def test_view_url_exists_at_desired_location(self):
        print('\n- Test: view url exists at desired location')
        self.login()

        response = self.client.get( reverse('human_resources:index') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('human_resources:all_users') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('human_resources:show_user', args=[STUDENT]) )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('human_resources:view_confidentiality', args=[STUDENT]) )
        self.assertEqual(response.status_code, 200)

    def test_index(self):
        print('\n- Display an index page')
        self.login()

        response = self.client.get( reverse('human_resources:index') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USER)
        self.assertEqual(response.context['loggedin_user'].roles, ['HR'])

    def test_all_users(self):
        print('\n- Display all users')
        self.login()

        response = self.client.get( reverse('human_resources:all_users') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USER)
        self.assertEqual(response.context['loggedin_user'].roles, ['HR'])
        self.assertEqual( len(response.context['users']), 164)

    def test_show_user(self):
        print('\n- Display an user profile')
        self.login()

        response = self.client.get( reverse('human_resources:show_user', args=[STUDENT]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USER)
        self.assertEqual(response.context['loggedin_user'].roles, ['HR'])
        self.assertEqual(response.context['user'].username, STUDENT)

    def test_view_confidentiality(self):
        print('\n- Display confidentiality')
        self.login()

        response = self.client.get( reverse('human_resources:view_confidentiality', args=[STUDENT]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USER)
        self.assertEqual(response.context['loggedin_user'].roles, ['HR'])
        self.assertEqual(response.context['user'].username, STUDENT)
