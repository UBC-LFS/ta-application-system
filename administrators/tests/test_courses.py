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

from administrators.tests.test_sessions import LOGIN_URL, ContentType, DATA, PASSWORD, USERS

COURSE = 'apbi-200-001-introduction-to-soil-science-w'

class CourseTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        print('\nCourse testing has started ==>')
        cls.user = userApi.get_user(USERS[0], 'username')

    def login(self, username=None, password=None):
        if username and password:
            self.client.post(LOGIN_URL, data={'username': username, 'password': password})
        else:
            self.client.post(LOGIN_URL, data={'username': self.user.username, 'password': PASSWORD})

    def messages(self, res):
        return [m.message for m in get_messages(res.wsgi_request)]

    def test_view_url_exists_at_desired_location(self):
        print('- Test: view url exists at desired location')
        self.login()

        response = self.client.get( reverse('administrators:all_courses') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:create_course') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:edit_course', args=[COURSE]) + '?next=' + reverse('administrators:all_users') + '?page=2' )
        self.assertEqual(response.status_code, 200)


    def test_all_courses(self):
        print('- Test: Display all courses and edit/delete a course')
        self.login()

        response = self.client.get(reverse('administrators:all_courses'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['courses']), settings.PAGE_SIZE )
        self.assertEqual( len(adminApi.get_courses()), 709 )

    def test_create_course(self):
        print('- Test: Create a course')
        self.login()

        total_courses = len(adminApi.get_courses())

        data = {
            'code': '2',
            'number': '1',
            'section': '1',
            'name': 'new course',
            'term': '2',
            'overview': 'overview',
            'job_description': 'description',
            'job_note': 'note'
        }
        response = self.client.post( reverse('administrators:create_course'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)
        self.assertEqual(response.url, reverse('administrators:all_courses'))

        response = self.client.get(reverse('administrators:all_courses'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['courses']), settings.PAGE_SIZE )
        self.assertEqual( len(adminApi.get_courses()), total_courses + 1 )

        # create the same data for checking duplicated data
        response = self.client.post( reverse('administrators:create_course'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)
        self.assertEqual(response.url, reverse('administrators:create_course'))

    def test_edit_course(self):
        print('- Test: Edit a course')
        self.login()

        FULL_PATH = reverse('administrators:all_users') + '?page=2'
        NEXT = '?next=' + FULL_PATH

        response = self.client.get(reverse('administrators:edit_course', args=[COURSE]) + NEXT)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual(response.context['course'].slug, COURSE)
        self.assertFalse(response.context['form'].is_bound)

        course = response.context['course']

        data1 = {
            'name': 'edit course',
            'overview': 'new overview',
            'job_description': 'new job description',
            'job_note': 'new job note',
            'next': '/administrators/hr/user/all/?page=2'
        }
        response = self.client.post( reverse('administrators:edit_course', args=[COURSE]) + NEXT, data=urlencode(data1), content_type=ContentType )
        self.assertEqual(response.status_code, 404)

        data2 = {
            'name': 'edit course',
            'overview': 'new overview',
            'job_description': 'new job description',
            'job_note': 'new job note',
            'next': FULL_PATH
        }
        response = self.client.post( reverse('administrators:edit_course', args=[COURSE]) + NEXT, data=urlencode(data2), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        new_course = adminApi.get_course(course.id)

        self.assertEqual(new_course.id, course.id)
        self.assertEqual(new_course.code.id, course.code.id)
        self.assertEqual(new_course.number.id, course.number.id)
        self.assertEqual(new_course.section.id, course.section.id)
        self.assertEqual(new_course.term.id, course.term.id)
        self.assertEqual(new_course.name, data2['name'])
        self.assertEqual(new_course.job_description, data2['job_description'])
        self.assertEqual(new_course.job_note, data2['job_note'])

    def test_delete_course(self):
        print('- Test: delete a course')
        self.login()

        total_courses = len(adminApi.get_courses())

        course_id = 61

        FULL_PATH = reverse('administrators:all_courses') + '?page=2'
        NEXT = '?next=' + FULL_PATH
        data1 = {
            'course': course_id,
            'next': '/administrators/courses/al/?page=2'
        }
        response = self.client.post( reverse('administrators:delete_course'), data=urlencode(data1), content_type=ContentType )
        self.assertEqual(response.status_code, 404)

        data2 = {
            'course': course_id,
            'next': FULL_PATH
        }
        response = self.client.post( reverse('administrators:delete_course'), data=urlencode(data2), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        #self.assertIsNone(adminApi.get_course(course_id))
        self.assertEqual( len(adminApi.get_courses()), total_courses - 1 )

    def test_delete_not_existing_course(self):
        print('- Test: delete a not existing course')
        self.login()

        response = self.client.post( reverse('administrators:delete_course'), data=urlencode({ 'course': 1000 }), content_type=ContentType )
        self.assertEqual(response.status_code, 404)

    def test_create_new_course_with_zero_base(self):
        print('- Test: create a new course with zero base')
        self.login()

        response = self.client.post( reverse('administrators:course_codes'), data=urlencode({ 'name': 'ABC' }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.post( reverse('administrators:course_numbers'), data=urlencode({ 'name': '111' }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.post( reverse('administrators:course_sections'), data=urlencode({ 'name': '501' }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.post( reverse('administrators:terms'), data=urlencode({ 'code': 'N', 'name': 'New Term', 'by_month': 4, 'max_hours': 192 }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        course_code = adminApi.get_course_code_by_name('ABC')
        course_number = adminApi.get_course_number_by_name('111')
        course_section = adminApi.get_course_section_by_name('501')
        term = adminApi.get_term_by_code('N')

        data = {
            'code': course_code.id,
            'number': course_number.id,
            'section': course_section.id,
            'name': 'New Course',
            'term': term.id
        }
        response = self.client.post( reverse('administrators:create_course'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)