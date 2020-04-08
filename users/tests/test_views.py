from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from urllib.parse import urlencode

from administrators.models import *
from users.models import *
from administrators import api as adminApi
from users import api as userApi

from administrators.tests.test_views import LOGIN_URL, ContentType, DATA, USERS, SESSION, JOB, APP, COURSE, PASSWORD
from django.core.files.uploadedfile import SimpleUploadedFile
import datetime


class UserTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        cls.user = userApi.get_user(USERS[2], 'username')

    def login(self, username=None, password=None):
        if username and password:
            self.client.post(LOGIN_URL, data={'username': username, 'password': password})
        else:
            self.client.post(LOGIN_URL, data={'username': self.user.username, 'password': PASSWORD})

    def messages(self, res):
        return [m.message for m in get_messages(res.wsgi_request)]

    def test_view_url_exists_at_desired_location(self):
        print('\n- Test: view url exists at desired location')

        self.login(USERS[2], '12')

        response = self.client.get( reverse('users:upload_avatar', args=['students']) )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('users:upload_avatar', args=['instructors']) )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('users:upload_avatar', args=['administrators']) )
        self.assertEqual(response.status_code, 403)

        self.login(USERS[1], '12')

        response = self.client.get( reverse('users:upload_avatar', args=['students']) )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('users:upload_avatar', args=['instructors']) )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('users:upload_avatar', args=['administrators']) )
        self.assertEqual(response.status_code, 403)

        self.login(USERS[0], '12')

        response = self.client.get( reverse('users:upload_avatar', args=['students']) )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('users:upload_avatar', args=['instructors']) )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('users:upload_avatar', args=['administrators']) )
        self.assertEqual(response.status_code, 200)

    def test_upload_avatar(self):
        print('\n- Test: upload user avatar')
        self.login(USERS[1], '12')
        user = userApi.get_user(USERS[1], 'username')

        self.assertIsNone(userApi.has_user_resume_created(user))
        data = {
            'user': user.id,
            'avatar': SimpleUploadedFile('avatar.jpg', b'file_content', content_type='image/jpeg')
        }
        response = self.client.post( reverse('users:upload_avatar', args=['instructors']), data=data, format='multipart')
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/users/r/instructors/profile/photo/upload/')
        self.assertRedirects(response, response.url)

        avatar = userApi.has_user_avatar_created(userApi.get_user(USERS[1], 'username'))
        self.assertIsNotNone(avatar)

    def test_delete_avatar(self):
        print('\n- Test: delete user avatar')
        self.login(USERS[1], '12')
        user = userApi.get_user(USERS[1], 'username')

        data = {
            'user': user.id,
            'avatar': SimpleUploadedFile('avatar.jpg', b'file_content', content_type='image/jpeg')
        }
        response = self.client.post( reverse('users:upload_avatar', args=['instructors']), data=data, format='multipart' )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/users/r/instructors/profile/photo/upload/')
        self.assertRedirects(response, response.url)

        avatar = userApi.has_user_avatar_created(userApi.get_user(USERS[1], 'username'))
        self.assertIsNotNone(avatar)

        response = self.client.post( reverse('users:delete_avatar', args=['instructors']), data=urlencode({ 'user': USERS[1] }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/users/r/instructors/profile/photo/upload/')
        self.assertRedirects(response, response.url)
