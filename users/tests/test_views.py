from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from urllib.parse import urlencode

from administrators.models import *
from users.models import *
from administrators import api as adminApi
from users import api as userApi

from administrators.tests.test_sessions import LOGIN_URL, ContentType, DATA, USERS, SESSION, JOB, APP, COURSE, PASSWORD
from django.core.files.uploadedfile import SimpleUploadedFile
import datetime


ADMINISTRATOR_NEXT = '?next=/administrators/'
INSTRUCTOR_NEXT = '?next=/instructors/'
STUDENT_NEXT = '?next=/students/'


class UserTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        cls.user = userApi.get_user(USERS[2], 'username')
        cls.testing_image = os.path.join(settings.BASE_DIR, 'users', 'tests', 'files', 'karsten-wurth-9qvZSH_NOQs-unsplash.jpg')

    def login(self, username=None, password=None):
        if username and password:
            self.client.post(LOGIN_URL, data={'username': username, 'password': password})
        else:
            self.client.post(LOGIN_URL, data={'username': self.user.username, 'password': PASSWORD})

    def messages(self, res):
        return [m.message for m in get_messages(res.wsgi_request)]

    def test_view_url_exists_at_desired_location(self):
        print('- Test: view url exists at desired location')

        self.login(USERS[2], 'password')

        response = self.client.get( reverse('users:upload_avatar') + STUDENT_NEXT )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('users:upload_avatar') + INSTRUCTOR_NEXT )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('users:upload_avatar') + ADMINISTRATOR_NEXT )
        self.assertEqual(response.status_code, 403)

        self.login(USERS[1], 'password')

        response = self.client.get( reverse('users:upload_avatar') + STUDENT_NEXT )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('users:upload_avatar') + INSTRUCTOR_NEXT )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('users:upload_avatar') + ADMINISTRATOR_NEXT )
        self.assertEqual(response.status_code, 403)

        self.login(USERS[0], 'password')

        response = self.client.get( reverse('users:upload_avatar') + STUDENT_NEXT )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('users:upload_avatar') + INSTRUCTOR_NEXT )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('users:upload_avatar') + ADMINISTRATOR_NEXT )
        self.assertEqual(response.status_code, 200)

    def test_upload_avatar_administrator(self):
        print('- Test: upload user avatar in an administrator view')
        self.login(USERS[0], 'password')
        user = userApi.get_user(USERS[0], 'username')

        self.assertIsNone(userApi.has_user_resume_created(user))
        data = {
            'user': user.id,
            'uploaded': SimpleUploadedFile('avatar.jpg', open(self.testing_image, 'rb').read(), content_type='image/jpeg'),
        }
        response = self.client.post( reverse('users:upload_avatar') + ADMINISTRATOR_NEXT, data=data, format='multipart')
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('users:upload_avatar') + ADMINISTRATOR_NEXT)
        self.assertRedirects(response, response.url)

        avatar = userApi.has_user_avatar_created(userApi.get_user(USERS[0], 'username'))
        self.assertIsNotNone(avatar)

        userApi.delete_user_avatar(USERS[0])


    def test_upload_avatar_instructor(self):
        print('- Test: upload user avatar in an instructor view')
        self.login(USERS[1], 'password')
        user = userApi.get_user(USERS[1], 'username')

        self.assertIsNone(userApi.has_user_resume_created(user))
        data = {
            'user': user.id,
            'uploaded': SimpleUploadedFile('avatar.jpg', open(self.testing_image, 'rb').read(), content_type='image/jpeg'),
        }
        response = self.client.post( reverse('users:upload_avatar') + INSTRUCTOR_NEXT, data=data, format='multipart')
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('users:upload_avatar') + INSTRUCTOR_NEXT)
        self.assertRedirects(response, response.url)

        avatar = userApi.has_user_avatar_created(userApi.get_user(USERS[1], 'username'))
        self.assertIsNotNone(avatar)

        userApi.delete_user_avatar(USERS[1])

    def test_upload_avatar_student(self):
        print('- Test: upload user avatar in a student view')
        self.login(USERS[2], 'password')
        user = userApi.get_user(USERS[2], 'username')

        self.assertIsNone(userApi.has_user_resume_created(user))
        data = {
            'user': user.id,
            'uploaded': SimpleUploadedFile('avatar.jpg', open(self.testing_image, 'rb').read(), content_type='image/jpeg'),
        }
        response = self.client.post( reverse('users:upload_avatar') + STUDENT_NEXT, data=data, format='multipart')
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('users:upload_avatar') + STUDENT_NEXT)
        self.assertRedirects(response, response.url)

        avatar = userApi.has_user_avatar_created(userApi.get_user(USERS[2], 'username'))
        self.assertIsNotNone(avatar)

        userApi.delete_user_avatar(USERS[2])


    def test_delete_avatar_administrator(self):
        print('- Test: delete user avatar in an administrator view')
        self.login(USERS[0], 'password')
        user = userApi.get_user(USERS[0], 'username')

        data = {
            'user': user.id,
            'uploaded': SimpleUploadedFile('avatar.jpg', open(self.testing_image, 'rb').read(), content_type='image/jpeg')
        }
        response = self.client.post( reverse('users:upload_avatar') + ADMINISTRATOR_NEXT, data=data, format='multipart' )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('users:upload_avatar') + ADMINISTRATOR_NEXT)
        self.assertRedirects(response, response.url)

        avatar = userApi.has_user_avatar_created(userApi.get_user(USERS[0], 'username'))
        self.assertIsNotNone(avatar)

        response = self.client.post( reverse('users:delete_avatar') + ADMINISTRATOR_NEXT, data=urlencode({ 'user': USERS[0] }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('users:upload_avatar') + ADMINISTRATOR_NEXT)
        self.assertRedirects(response, response.url)


    def test_delete_avatar_instructor(self):
        print('- Test: delete user avatar in an instructor view')
        self.login(USERS[1], 'password')
        user = userApi.get_user(USERS[1], 'username')

        data = {
            'user': user.id,
            'uploaded': SimpleUploadedFile('avatar.jpg', open(self.testing_image, 'rb').read(), content_type='image/jpeg')
        }
        response = self.client.post( reverse('users:upload_avatar') + INSTRUCTOR_NEXT, data=data, format='multipart' )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('users:upload_avatar') + INSTRUCTOR_NEXT)
        self.assertRedirects(response, response.url)

        avatar = userApi.has_user_avatar_created(userApi.get_user(USERS[1], 'username'))
        self.assertIsNotNone(avatar)

        response = self.client.post( reverse('users:delete_avatar') + INSTRUCTOR_NEXT, data=urlencode({ 'user': USERS[1] }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('users:upload_avatar') + INSTRUCTOR_NEXT)
        self.assertRedirects(response, response.url)


    def test_delete_avatar_student(self):
        print('- Test: delete user avatar in a student view')
        self.login(USERS[2], 'password')
        user = userApi.get_user(USERS[2], 'username')

        data = {
            'user': user.id,
            'uploaded': SimpleUploadedFile('avatar.jpg', open(self.testing_image, 'rb').read(), content_type='image/jpeg')
        }
        response = self.client.post( reverse('users:upload_avatar') + STUDENT_NEXT, data=data, format='multipart' )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('users:upload_avatar') + STUDENT_NEXT)
        self.assertRedirects(response, response.url)

        avatar = userApi.has_user_avatar_created(userApi.get_user(USERS[2], 'username'))
        self.assertIsNotNone(avatar)

        response = self.client.post( reverse('users:delete_avatar') + STUDENT_NEXT, data=urlencode({ 'user': USERS[2] }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('users:upload_avatar') + STUDENT_NEXT)
        self.assertRedirects(response, response.url)
