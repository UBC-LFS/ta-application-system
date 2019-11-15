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


USER = 'mcqueen.jenny'
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
            self.client.post(LOGIN_URL, data={'username': self.user.username, 'password': self.user.password})

    def messages(self, res):
        return [m.message for m in get_messages(res.wsgi_request)]

    def test_view_url_exists_at_desired_location(self):
        print('\n- Test: view url exists at desired location')
        self.login()

        response = self.client.get( reverse('instructors:index') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('instructors:show_profile') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('instructors:show_jobs') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('instructors:edit_job', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('instructors:show_applications', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 200)

    def test_show_profile(self):
        print('\n- Display an instructor profile')
        self.login()

        response = self.client.get( reverse('instructors:show_profile') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USER)
        self.assertEqual(response.context['loggedin_user'].roles, ['Instructor'])

    def test_show_user(self):
        print('\n- Display an user profile')
        self.login()

        response = self.client.get( reverse('instructors:show_user', args=[SESSION, JOB, STUDENT]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USER)
        self.assertEqual(response.context['loggedin_user'].roles, ['Instructor'])
        self.assertEqual(response.context['user'].username, STUDENT)

    def test_show_jobs(self):
        print('\n- Display jobs by instructors')
        self.login()

        response = self.client.get( reverse('instructors:show_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USER)
        self.assertEqual(response.context['loggedin_user'].roles, ['Instructor'])
        self.assertEqual( response.context['loggedin_user'].job_set.count(), 11)

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
        self.assertEqual( len(response.context['jobs']), 10 )

        data = {
            'title': 'job title',
            'description': 'job description',
            'qualification': 'job qualification',
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
        self.assertEqual(response.context['job'].title, data['title'])
        self.assertEqual(response.context['job'].description, data['description'])
        self.assertEqual(response.context['job'].qualification, data['qualification'])
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

        data = {
            'assigned': ApplicationStatus.OFFERED,
            'application': '6',
            'instructor_preference': Application.NONE,
            'assigned_hours': 0.0
        }
        response = self.client.post( reverse('instructors:show_applications', args=[SESSION, JOB]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/instructors/sessions/{0}/jobs/{1}/applications/'.format(SESSION, JOB))
        self.assertRedirects(response, response.url)

        data['instructor_preference'] = Application.NO_PREFERENCE
        data['assigned_hours'] = 10.0
        response = self.client.post( reverse('instructors:show_applications', args=[SESSION, JOB]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/instructors/sessions/{0}/jobs/{1}/applications/'.format(SESSION, JOB))
        self.assertRedirects(response, response.url)

        data['instructor_preference'] = Application.ACCEPTABLE
        data['assigned_hours'] = 0.0
        response = self.client.post( reverse('instructors:show_applications', args=[SESSION, JOB]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/instructors/sessions/{0}/jobs/{1}/applications/'.format(SESSION, JOB))
        self.assertRedirects(response, response.url)

        data['instructor_preference'] = Application.ACCEPTABLE
        data['assigned_hours'] = 201.0
        response = self.client.post( reverse('instructors:show_applications', args=[SESSION, JOB]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/instructors/sessions/{0}/jobs/{1}/applications/'.format(SESSION, JOB))
        self.assertRedirects(response, response.url)

        data['instructor_preference'] = Application.REQUESTED
        data['assigned_hours'] = 20.0
        response = self.client.post( reverse('instructors:show_applications', args=[SESSION, JOB]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('instructors:show_applications', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['job'].application_set.first().instructor_preference, Application.REQUESTED)
        self.assertEqual( len(response.context['apps']) , 4 )
