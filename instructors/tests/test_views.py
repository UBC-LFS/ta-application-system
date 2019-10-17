from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from urllib.parse import urlencode

from administrators.models import *
from users.models import *
from administrators import api as adminApi
from users import api as userApi

from administrators.tests.test_views import DATA, ContentType
from django.core.files.uploadedfile import SimpleUploadedFile

from django.utils.crypto import get_random_string



class JobTest(TestCase):
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
        self.login('test.user4', '12')

        session_slug = '2019-w1'
        job_slug = 'lfs-100-001-introduction-to-land-food-and-community-w1'

        response = self.client.get( reverse('instructors:index') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('instructors:profile') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('instructors:my_jobs') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('instructors:edit_job', args=[session_slug, job_slug]) )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('instructors:my_applications', args=[session_slug, job_slug]) )
        self.assertEqual(response.status_code, 200)

    def test_profile(self):
        print('\n- Display user profile')
        self.login('test.user4', '12')

        response = self.client.get( reverse('instructors:profile') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'test.user4')
        self.assertEqual(response.context['loggedin_user'].roles, ['Instructor'])
        self.assertEqual(response.context['user'].username, 'test.user4')

    def test_my_jobs(self):
        print('\n- Display jobs by instructors')
        self.login('test.user4', '12')

        response = self.client.get( reverse('instructors:my_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'test.user4')
        self.assertEqual(response.context['loggedin_user'].roles, ['Instructor'])
        self.assertEqual(response.context['user'].username, 'test.user4')

    def test_edit_job(self):
        print('\n- Display jobs by instructors')
        self.login('test.user4', '12')

        session_slug = '2019-w1'
        job_slug = 'lfs-100-001-introduction-to-land-food-and-community-w1'

        response = self.client.get( reverse('instructors:edit_job', args=[session_slug, job_slug]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'test.user4')
        self.assertEqual(response.context['loggedin_user'].roles, ['Instructor'])
        self.assertEqual(response.context['job'].course.slug, job_slug)
        self.assertFalse(response.context['form'].is_bound)
        self.assertEqual(response.context['form'].instance, response.context['job'])
        self.assertEqual( len(response.context['jobs']), 4 )

        data = {
            'title': 'job title',
            'description': 'job description',
            'qualification': 'job qualification',
            'note': 'job note'
        }

        response = self.client.post( reverse('instructors:edit_job', args=[session_slug, job_slug]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('instructors:edit_job', args=[session_slug, job_slug]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['job'].title, data['title'])
        self.assertEqual(response.context['job'].description, data['description'])
        self.assertEqual(response.context['job'].qualification, data['qualification'])
        self.assertEqual(response.context['job'].note, data['note'])

    def test_my_applications(self):
        print('\n- Display applications applied by students')
        self.login('test.user4', '12')

        session_slug = '2019-w1'
        job_slug = 'lfs-100-001-introduction-to-land-food-and-community-w1'

        response = self.client.get( reverse('instructors:my_applications', args=[session_slug, job_slug]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'test.user4')
        self.assertEqual(response.context['loggedin_user'].roles, ['Instructor'])
        self.assertEqual(response.context['job'].course.slug, job_slug)
        self.assertEqual( len(response.context['job'].application_set.all()), 4 )
        self.assertEqual(response.context['job'].application_set.first().instructor_preference, '1')
        self.assertEqual( len(response.context['instructor_preference_choices']), 5 )

        data = {
            'application': '1',
            'instructor_preference': '4'
        }
        response = self.client.post( reverse('instructors:my_applications', args=[session_slug, job_slug]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('instructors:my_applications', args=[session_slug, job_slug]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['job'].application_set.first().instructor_preference, '4')
