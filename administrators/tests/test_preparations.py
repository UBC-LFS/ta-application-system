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

class PreparationTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        print('\nPreparation testing has started ==>')
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

        response = self.client.get( reverse('administrators:terms') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:degrees') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:programs') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:trainings') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:statuses') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:course_codes') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:course_numbers') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:course_sections') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:classifications') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:admin_emails') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:landing_pages') )
        self.assertEqual(response.status_code, 200)


    def test_terms(self):
        print('- Test: Display all terms and create a term')
        self.login()

        response = self.client.get( reverse('administrators:terms') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['terms']), 11 )
        self.assertFalse(response.context['form'].is_bound)

        data = {
            'code': 'WG',
            'name': 'Winter G',
            'by_month': 4,
            'max_hours': 192
        }
        response = self.client.post( reverse('administrators:terms'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:terms') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['terms']), 12 )
        self.assertEqual(response.context['terms'].last().code, data['code'])
        self.assertEqual(response.context['terms'].last().name, data['name'])
        self.assertEqual(response.context['terms'].last().by_month, data['by_month'])
        self.assertEqual(response.context['terms'].last().max_hours, data['max_hours'])

    def test_edit_term(self):
        print('- Test: edit term details')
        self.login()

        term_id = 1

        data = {
            'code': 'WG',
            'name': 'Winter G',
            'by_month': 4,
            'max_hours': 192
        }
        response = self.client.post( reverse('administrators:edit_term', args=[term_id]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:terms') )
        self.assertEqual(response.status_code, 200)
        terms = response.context['terms']

        found = 0
        for term in terms:
            if term.id == term_id:
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_term(self):
        print('- Test: delete a term')
        self.login()

        total_terms = len(adminApi.get_terms())

        data = {
            'code': 'WG',
            'name': 'Winter G',
            'by_month': 4,
            'max_hours': 192
        }
        response = self.client.post( reverse('administrators:terms'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:terms') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['terms']), total_terms + 1 )

        term_id = total_terms + 1
        response = self.client.post( reverse('administrators:delete_term'), data=urlencode({ 'term': term_id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:terms'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['terms']), total_terms)

        found = False
        for term in response.context['terms']:
            if term.id == term_id: found = True
        self.assertFalse(found)


    def test_degrees(self):
        print('- Test: Display all degrees and create a degree')
        self.login()

        response = self.client.get( reverse('administrators:degrees') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['degrees']), 11 )
        self.assertFalse(response.context['form'].is_bound)

        data = { 'name': 'Diploma' }
        response = self.client.post( reverse('administrators:degrees'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:degrees') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['degrees']), 12 )
        self.assertEqual(response.context['degrees'].last().name, data['name'])

    def test_edit_degree(self):
        print('- Test: edit degree details')
        self.login()

        slug = 'bachelor-of-arts'

        data = { 'name': 'updated degree' }
        response = self.client.post( reverse('administrators:edit_degree', args=[slug]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:degrees') )
        self.assertEqual(response.status_code, 200)
        degrees = response.context['degrees']

        found = 0
        for degree in degrees:
            if degree.slug == 'updated-degree':
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_degree(self):
        print('- Test: delete a degree')
        self.login()

        total_degrees = len(userApi.get_degrees())

        degree_id = 1
        response = self.client.post( reverse('administrators:delete_degree'), data=urlencode({ 'degree': degree_id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:degrees'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['degrees']), total_degrees - 1)

        found = False
        for degree in response.context['degrees']:
            if degree.id == degree_id: found = True
        self.assertFalse(found)

    def test_programs(self):
        print('- Test: Display all programs and create a program')
        self.login()

        response = self.client.get( reverse('administrators:programs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['programs']), 16 )
        self.assertFalse(response.context['form'].is_bound)

        data = { 'name': 'Master of Science in Animal' }
        response = self.client.post( reverse('administrators:programs'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:programs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['programs']), 17 )
        self.assertEqual(response.context['programs'].last().name, data['name'])

    def test_edit_program(self):
        print('- Test: edit program details')
        self.login()

        slug = 'master-of-science-in-applied-animal-biology-msc'

        data = { 'name': 'updated program' }
        response = self.client.post( reverse('administrators:edit_program', args=[slug]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:programs') )
        self.assertEqual(response.status_code, 200)
        programs = response.context['programs']

        found = 0
        for program in programs:
            if program.slug == 'updated-program':
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_program(self):
        print('- Test: delete a program')
        self.login()

        total_programs = len(userApi.get_programs())

        program_id = 1
        response = self.client.post( reverse('administrators:delete_program'), data=urlencode({ 'program': program_id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:programs'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['programs']), total_programs - 1)

        found = False
        for program in response.context['programs']:
            if program.id == program_id: found = True
        self.assertFalse(found)

    def test_trainings(self):
        print('- Test: Display all trainings and create a training')
        self.login()

        response = self.client.get( reverse('administrators:trainings') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['trainings']), 4 )
        self.assertFalse(response.context['form'].is_bound)

        data = { 'name': 'new training' }
        response = self.client.post( reverse('administrators:trainings'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:trainings') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['trainings']), 5 )
        self.assertEqual(response.context['trainings'].last().name, data['name'])

    def test_edit_training(self):
        print('- Test: edit training details')
        self.login()

        slug = 'workplace-violence-prevention-training'

        data = { 'name': 'updated training' }
        response = self.client.post( reverse('administrators:edit_training', args=[slug]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:trainings') )
        self.assertEqual(response.status_code, 200)
        trainings = response.context['trainings']

        found = 0
        for training in trainings:
            if training.slug == 'updated-training':
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_training(self):
        print('- Test: delete a training')
        self.login()

        total_trainings = len(userApi.get_trainings())

        training_id = 1
        response = self.client.post( reverse('administrators:delete_training'), data=urlencode({ 'training': training_id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:trainings'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['trainings']), total_trainings - 1)

        found = False
        for training in response.context['trainings']:
            if training.id == training_id: found = True
        self.assertFalse(found)

    def test_statuses(self):
        print('- Test: Display all statuss and create a status')
        self.login()

        response = self.client.get( reverse('administrators:statuses') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['statuses']), 9 )
        self.assertFalse(response.context['form'].is_bound)

        data = { 'name': 'Full Professor' }
        response = self.client.post( reverse('administrators:statuses'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:statuses') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['statuses']), 10 )
        self.assertEqual(response.context['statuses'].last().name, data['name'])

    def test_edit_status(self):
        print('- Test: edit status details')
        self.login()

        slug = 'undergraduate-student'

        data = { 'name': 'updated status' }
        response = self.client.post( reverse('administrators:edit_status', args=[slug]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:statuses') )
        self.assertEqual(response.status_code, 200)
        statuss = response.context['statuses']

        found = 0
        for status in statuss:
            if status.slug == 'updated-status':
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_status(self):
        print('- Test: delete a status')
        self.login()

        total_statuses = len(userApi.get_statuses())

        status_id = 4
        response = self.client.post( reverse('administrators:delete_status'), data=urlencode({ 'status': status_id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:statuses'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['statuses']), total_statuses - 1)

        found = False
        for status in response.context['statuses']:
            if status.id == status_id: found = True
        self.assertFalse(found)

    def test_course_codes(self):
        print('- Test: Display all course_codes and create a course_code')
        self.login()

        response = self.client.get( reverse('administrators:course_codes') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['course_codes']), 6 )
        self.assertFalse(response.context['form'].is_bound)

        data = { 'name': 'ZBC' }
        response = self.client.post( reverse('administrators:course_codes'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:course_codes') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['course_codes']), 7 )
        self.assertEqual(response.context['course_codes'].last().name, data['name'])

    def test_edit_course_code(self):
        print('- Test: edit course_code details')
        self.login()

        course_code_id = 1

        data = { 'name': 'CSC' }
        response = self.client.post( reverse('administrators:edit_course_code', args=[course_code_id]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:course_codes') )
        self.assertEqual(response.status_code, 200)
        course_codes = response.context['course_codes']

        found = 0
        for course_code in course_codes:
            if course_code.name == 'CSC':
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_course_code(self):
        print('- Test: delete a course_code')
        self.login()

        data = { 'name': 'ZBC' }
        response = self.client.post( reverse('administrators:course_codes'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        course_code = adminApi.get_course_code_by_name(data['name'])
        response = self.client.post( reverse('administrators:delete_course_code'), data=urlencode({ 'course_code': course_code.id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:course_codes'))
        self.assertEqual(response.status_code, 200)

        found = False
        for c in response.context['course_codes']:
            if c.id == course_code.id: found = True
        self.assertFalse(found)

    def test_course_numbers(self):
        print('- Test: Display all course_numbers and create a course_number')
        self.login()

        response = self.client.get( reverse('administrators:course_numbers') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['course_numbers']), 74 )
        self.assertFalse(response.context['form'].is_bound)

        data = { 'name': '530' }
        response = self.client.post( reverse('administrators:course_numbers'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:course_numbers') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['course_numbers']), 75 )
        self.assertEqual(response.context['course_numbers'].last().name, data['name'])

    def test_edit_course_number(self):
        print('- Test: edit course_number details')
        self.login()

        course_number_id = 1

        data = { 'name': '111' }
        response = self.client.post( reverse('administrators:edit_course_number', args=[course_number_id]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:course_numbers') )
        self.assertEqual(response.status_code, 200)
        course_numbers = response.context['course_numbers']

        found = 0
        for course_number in course_numbers:
            if course_number.name == '111':
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_course_number(self):
        print('- Test: delete a course_number')
        self.login()


        data = { 'name': '530' }
        response = self.client.post( reverse('administrators:course_numbers'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        course_number = adminApi.get_course_number_by_name(data['name'])

        response = self.client.post( reverse('administrators:delete_course_number'), data=urlencode({ 'course_number': course_number.id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:course_numbers'))
        self.assertEqual(response.status_code, 200)

        found = False
        for c in response.context['course_numbers']:
            if c.id == course_number.id: found = True
        self.assertFalse(found)

    def test_course_sections(self):
        print('- Test: Display all course_sections and create a course_section')
        self.login()

        response = self.client.get( reverse('administrators:course_sections') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['course_sections']), 23 )
        self.assertFalse(response.context['form'].is_bound)

        data = { 'name': '99Z' }
        response = self.client.post( reverse('administrators:course_sections'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:course_sections') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['course_sections']), 24 )
        self.assertEqual(response.context['course_sections'].last().name, data['name'])

        data2 = { 'name': '002 & 003' }
        response = self.client.post( reverse('administrators:course_sections'), data=urlencode(data2), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:course_sections') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['course_sections']), 25 )
        self.assertEqual(response.context['course_sections'].last().name, data['name'])


    def test_create_course_section_failture(self):
        print('- Test: create a course section - failure')
        self.login()

        data = { 'name': '001 & 002 & 003' }
        response = self.client.post( reverse('administrators:course_sections'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertEquals(messages[0], 'An error occurred. Form is invalid. NAME: Ensure this value has at most 12 characters (it has 15).')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)
        self.assertEqual(response.url, reverse('administrators:course_sections'))


    def test_edit_course_section(self):
        print('- Test: edit course_section details')
        self.login()

        course_section_id = 1

        data = { 'name': '115' }
        response = self.client.post( reverse('administrators:edit_course_section', args=[course_section_id]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:course_sections') )
        self.assertEqual(response.status_code, 200)
        course_sections = response.context['course_sections']

        found = 0
        for course_section in course_sections:
            if course_section.name == '115':
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_course_section(self):
        print('- Test: delete a course_section')
        self.login()

        data = { 'name': '99Z' }
        response = self.client.post( reverse('administrators:course_sections'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        course_section = adminApi.get_course_section_by_name(data['name'])

        response = self.client.post( reverse('administrators:delete_course_section'), data=urlencode({ 'course_section': course_section.id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:course_sections'))
        self.assertEqual(response.status_code, 200)

        found = False
        for c in response.context['course_sections']:
            if c.id == course_section.id: found = True
        self.assertFalse(found)

    def test_classifications(self):
        print('- Test: Display all classifications and create a classification')
        self.login()

        response = self.client.get( reverse('administrators:classifications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['classifications']), 6 )
        self.assertFalse(response.context['form'].is_bound)

        data = {
            'year': '2020',
            'name': 'Marker 2',
            'wage': '16.05',
            'is_active': True
        }
        response = self.client.post( reverse('administrators:classifications'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:classifications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['classifications']), 7 )
        self.assertEqual(response.context['classifications'].latest('pk').name, data['name'])


    def test_edit_classification(self):
        print('- Test: edit classification details')
        self.login()

        slug = '2019-marker'

        data = {
            'year': '2020',
            'name': 'Marker 2',
            'wage': '16.05',
            'is_active': False
        }
        response = self.client.post( reverse('administrators:edit_classification', args=[slug]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:classifications') )
        self.assertEqual(response.status_code, 200)
        classifications = response.context['classifications']

        found = 0
        for classification in classifications:
            if classification.slug == '2020-marker-2':
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_classification(self):
        print('- Test: delete a classification')
        self.login()

        data = {
            'year': '2020',
            'name': 'Marker 2',
            'wage': '16.05',
            'is_active': True
        }
        response = self.client.post( reverse('administrators:classifications'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        classification = adminApi.get_classification_by_slug('2020-marker-2')

        response = self.client.post( reverse('administrators:delete_classification'), data=urlencode({ 'classification': classification.id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:classifications'))
        self.assertEqual(response.status_code, 200)

        found = False
        for c in response.context['classifications']:
            if c.id == classification.id: found = True
        self.assertFalse(found)


    def test_admin_emails(self):
        print('- Test: Display all admin emails and create an admin email')
        self.login()

        response = self.client.get( reverse('administrators:admin_emails') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['admin_emails']), 3 )
        self.assertFalse(response.context['form'].is_bound)

        data = {
            'title': 'Congratulations',
            'message': 'Hello',
            'type': 'offer'
        }
        response = self.client.post( reverse('administrators:admin_emails'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:admin_emails') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['admin_emails']), 4 )
        self.assertEqual(response.context['admin_emails'].latest('pk').title, data['title'])
        self.assertEqual(response.context['admin_emails'].latest('pk').message, data['message'])
        self.assertEqual(response.context['admin_emails'].latest('pk').type, data['type'])


    def test_edit_admin_email(self):
        print('- Test: edit admin email details')
        self.login()

        slug = 'offer-email'
        data = {
            'title': 'Congratulations',
            'message': 'Hello',
            'type': 'Type 111'
        }
        response = self.client.post( reverse('administrators:edit_admin_email', args=[slug]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertEqual(messages[0], 'Success! Type 111 updated')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:admin_emails') )
        self.assertEqual(response.status_code, 200)
        admin_emails = response.context['admin_emails']

        found = 0
        for email in admin_emails:
            if email.slug == 'type-111':
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_admin_email(self):
        print('- Test: delete a admin email')
        self.login()

        data = {
            'title': 'Congratulations',
            'message': 'Hello',
            'type': 'Offer 2'
        }
        response = self.client.post( reverse('administrators:admin_emails'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        admin_email = adminApi.get_admin_email_by_slug('offer-2')

        response = self.client.post( reverse('administrators:delete_admin_email'), data=urlencode({ 'admin_email': admin_email.id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:admin_emails'))
        self.assertEqual(response.status_code, 200)

        found = False
        for e in response.context['admin_emails']:
            if e.id == admin_email.id: found = True
        self.assertFalse(found)


    def test_landing_pages(self):
        print('- Test: Display all landin page contents and create a landing page content')
        self.login()

        response = self.client.get( reverse('administrators:landing_pages') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['landing_pages']), 1 )
        self.assertFalse(response.context['form'].is_bound)

        data = {
            'title': 'Title',
            'message': 'Message',
            'notice': 'Notice',
            'is_visible': False
        }
        response = self.client.post( reverse('administrators:landing_pages'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:landing_pages') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['landing_pages']), 2 )
        self.assertEqual(response.context['landing_pages'].latest('pk').title, data['title'])
        self.assertEqual(response.context['landing_pages'].latest('pk').message, data['message'])
        self.assertEqual(response.context['landing_pages'].latest('pk').notice, data['notice'])
        self.assertFalse(response.context['landing_pages'].latest('pk').is_visible)


    def test_edit_landing_page(self):
        print('- Test: edit landing page details')
        self.login()

        landing_page_id = 1
        data = {
            'title': 'Title 2',
            'message': 'Message 2',
            'notice': 'Notice 2',
            'is_visible': False
        }
        response = self.client.post( reverse('administrators:edit_landing_page', args=[landing_page_id]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:landing_pages') )
        self.assertEqual(response.status_code, 200)
        admin_emails = response.context['landing_pages']

        found = 0
        for email in admin_emails:
            if email.id == landing_page_id:
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_landing_page(self):
        print('- Test: delete a landing page')
        self.login()

        data = {
            'title': 'Title 2',
            'message': 'Message 2',
            'notice': 'Notice 2',
            'is_visible': False
        }
        response = self.client.post( reverse('administrators:landing_pages'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        landing_page = adminApi.get_landing_page(2)

        response = self.client.post( reverse('administrators:delete_landing_page'), data=urlencode({ 'landing_page': landing_page.id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:landing_pages'))
        self.assertEqual(response.status_code, 200)

        found = False
        for l in response.context['landing_pages']:
            if l.id == landing_page.id: found = True
        self.assertFalse(found)
