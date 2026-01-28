import os
from django.conf import settings
from django.test import TestCase, tag
from django.urls import reverse
from django.contrib.messages import get_messages
from urllib.parse import urlencode
from django.core.files.uploadedfile import SimpleUploadedFile

import datetime
import json
from random import randint

from administrators.models import *
from users.models import *
from administrators import api as adminApi
from users import api as userApi

from administrators.tests.test_sessions import LOGIN_URL, ContentType, DATA, USERS, USER_IDS, SESSION, JOB, APP, COURSE, PASSWORD, random_with_N_digits


STUDENT = 'user65.test'
STUDENT_ID = 65
STUDENT_JOB = 'apbi-265-001-sustainable-agriculture-and-food-systems-w1'

STUDENT2 = 'user66.test'
STUDENT2_ID = 66

NEXT = '?next=/app/students/'
HOME_BASIC = '&p=Home&t=basic'
HOME_ADDITIONAL = '&p=Home&t=additional'
HOME_RESUME = '&p=Home&t=resume'

EDIT_PROFILE_BASIC = '&p=Edit%20Profile&t=basic'
EDIT_PROFILE_ADDITIONAL = '&p=Edit%20Profile&t=additional'
EDIT_PROFILE_RESUME = '&p=Edit%20Profile&t=resume'

AVAILABLE_PATH = reverse('students:available_jobs', args=[SESSION]) + '?page=2'
AVAILABLE_NEXT = '?next=' + AVAILABLE_PATH

HISTORY_NEXT = '?next=' + reverse('students:history_jobs') + '?page=2'
HISTORY_WRONG_1 = '?nex=/app/students/jobs/history/?page=2'
HISTORY_WRONG_2 = '?next=/app/student/jobs/history/?page=2'
HISTORY_WRONG_3 = '?next=/app/students/jobs/histor/?page=2'


def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)


class StudentTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        cls.user = userApi.get_user(USERS[2], 'username')
        cls.testing_resume = os.path.join(settings.BASE_DIR, 'users', 'tests', 'files', 'resumeguide200914341.pdf')
        cls.testing_sin = os.path.join(settings.BASE_DIR, 'users', 'tests', 'files', 'karsten-wurth-9qvZSH_NOQs-unsplash.jpg')
        cls.testing_study_permit = os.path.join(settings.BASE_DIR, 'users', 'tests', 'files', 'lucas-davies-3aubsNmGuLE-unsplash.jpg')

    def login(self, username=None, password=None):
        if username and password:
            self.client.post(LOGIN_URL, data={'username': username, PASSWORD: password})
        else:
            self.client.post(LOGIN_URL, data={'username': self.user.username, PASSWORD: PASSWORD})

    def messages(self, res):
        return [m.message for m in get_messages(res.wsgi_request)]

    def json_messages(self, res):
        return json.loads( res.content.decode('utf-8') )

    def submit_profile_resume(self, username):
        ''' Submit profile and resume '''

        RESUME = self.testing_resume

        data = {
            'preferred_name': 'preferred name',
            'status': '3',
            'student_year': '2',
            'has_graduated': '2',
            'faculty': '1',
            'program': '5',
            'program_others': 'program others',
            'graduation_date': '2020-05-20',
            'degrees': ['2', '5'],
            'degree_details': 'degree details',
            'trainings': ['1','2', '3', '4'],
            'training_details': 'training details',
            'lfs_ta_training': '1',
            'lfs_ta_training_details': 'Lfs ta training details'
        }

        response = self.client.post( reverse('students:edit_profile') + '?t=general', data=urlencode(data, True), content_type=ContentType )
        messages = self.messages(response)
        self.assertEqual(messages[0], 'Success! User100 Test - General information has been updated.')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:edit_profile') + '?t=graduate')
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('students:edit_profile') + '?t=graduate')
        self.assertEqual(response.status_code, 200)

        data2 = {
            'total_academic_years': 4,
            'total_terms': 4,
            'total_ta_hours': 200,
            'ta_experience': '2',
            'ta_experience_details': 'Ta experience details',
            'qualifications': 'qualifications',
            'prior_employment': 'prior employment',
            'special_considerations': 'special considerations',
            'path': 'graduate'
        }
        response2 = self.client.post( reverse('students:update_profile_ta'), data=urlencode(data2), content_type=ContentType )
        messages2 = self.messages(response2)
        self.assertEqual(messages2[0], 'Success! User100 Test - TA information has been updated.')
        self.assertEqual(response2.status_code, 302)
        self.assertEqual(response2.url, reverse('students:show_profile') + '?next=' + reverse('students:edit_profile') + EDIT_PROFILE_ADDITIONAL)
        self.assertRedirects(response2, response2.url)


        response3 = self.client.get(response2.url)
        self.assertEqual(response3.status_code, 200)
        self.assertEqual(response3.context['loggedin_user'].username, username)
        self.assertEqual(response3.context['loggedin_user'].roles, ['Student'])

        user = response3.context['loggedin_user']
        self.assertEqual(user.profile.preferred_name, data['preferred_name'])
        self.assertEqual(user.profile.status.id, int(data['status']))
        self.assertEqual(user.profile.student_year, data['student_year'])
        self.assertEqual(user.profile.has_graduated, data['has_graduated'])
        self.assertEqual(user.profile.faculty.id, int(data['faculty']))
        self.assertEqual(user.profile.program.id, int(data['program']))
        self.assertEqual(user.profile.program_others, data['program_others'])
        self.assertEqual(user.profile.graduation_date.year, 2020)
        self.assertEqual(user.profile.graduation_date.month, 5)
        self.assertEqual(user.profile.graduation_date.day, 20)
        self.assertEqual( len(user.profile.degrees.all()), len(data['degrees']) )
        self.assertEqual(user.profile.degree_details, data['degree_details'])
        self.assertEqual( len(user.profile.trainings.all()), len(data['trainings']) )
        self.assertEqual(user.profile.training_details, data['training_details'])
        self.assertEqual(user.profile.lfs_ta_training, data['lfs_ta_training'])
        self.assertEqual(user.profile.lfs_ta_training_details, data['lfs_ta_training_details'])

        self.assertEqual(user.profile.total_academic_years, data2['total_academic_years'])
        self.assertEqual(user.profile.total_terms, data2['total_terms'])
        self.assertEqual(user.profile.total_ta_hours, data2['total_ta_hours'])
        self.assertEqual(user.profile.ta_experience, data2['ta_experience'])
        self.assertEqual(user.profile.ta_experience_details, data2['ta_experience_details'])
        self.assertEqual(user.profile.qualifications, data2['qualifications'])
        self.assertEqual(user.profile.prior_employment, data2['prior_employment'])
        self.assertEqual(user.profile.special_considerations, data2['special_considerations'])

        user = userApi.get_user(username, 'username')

        data0 = {
            'user': user.id,
            'uploaded': SimpleUploadedFile('resume.pdf', open(RESUME, 'rb').read(), content_type='application/pdf')
        }
        response = self.client.post(reverse('students:upload_resume') + '?nex=/app/students/&p=Home&t=resume', data=data0, format='multipart')
        self.assertEqual(response.status_code, 404)

        data1 = {
            'user': user.id,
            'uploaded': SimpleUploadedFile('resume.pdf', open(RESUME, 'rb').read(), content_type='application/pdf')
        }
        response = self.client.post(reverse('students:upload_resume') + '?next=/app/studens/&p=Home&t=resume', data=data1, format='multipart')
        self.assertEqual(response.status_code, 404)

        data2 = {
            'user': user.id,
            'uploaded': SimpleUploadedFile('resume.pdf', open(RESUME, 'rb').read(), content_type='application/pdf')
        }
        response = self.client.post(reverse('students:upload_resume') + '?next=/app/students/&p=Hom&t=resume', data=data2, format='multipart')
        self.assertEqual(response.status_code, 404)

        data3 = {
            'user': user.id,
            'uploaded': SimpleUploadedFile('resume.pdf', open(RESUME, 'rb').read(), content_type='application/pdf')
        }
        response = self.client.post(reverse('students:upload_resume') + '?next=/app/students/&p=Hom&t=resumE', data=data3, format='multipart')
        self.assertEqual(response.status_code, 404)

        data4 = {
            'user': user.id,
            'uploaded': SimpleUploadedFile('resume.pdf', open(RESUME, 'rb').read(), content_type='application/pdf')
        }
        response = self.client.post( reverse('students:upload_resume') + NEXT + HOME_RESUME, data=data4, format='multipart')
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:show_profile') + NEXT + HOME_RESUME)
        self.assertRedirects(response, response.url)

        resume = userApi.has_user_resume_created(user)
        self.assertIsNotNone(resume)


    def submit_profile_resume_undergraduate(self, username):
        ''' Submit profile and resume '''

        RESUME = self.testing_resume

        data = {
            'preferred_name': 'preferred name',
            'qualifications': 'qualifications',
            'prior_employment': 'prior employment',
            'special_considerations': 'special considerations',
            'status': '1',
            'program': '5',
            'program_others': 'program others',
            'graduation_date': '2020-05-20',
            'degrees': ['2', '5'],
            'degree_details': 'degree details',
            'trainings': ['1', '2', '3', '4'],
            'training_details': 'training details',
            'lfs_ta_training': '1',
            'lfs_ta_training_details': 'Lfs ta training details',
            'ta_experience': '2',
            'ta_experience_details': 'Ta experience details'
        }

        response = self.client.post( reverse('students:edit_profile'), data=urlencode(data, True), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:show_profile') + '?next=' + reverse('students:edit_profile') + EDIT_PROFILE_ADDITIONAL)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:show_profile') + '?next=' + reverse('students:edit_profile') + EDIT_PROFILE_ADDITIONAL )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context['loggedin_user'].username, username)
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        user = response.context['loggedin_user']
        self.assertEqual(user.profile.preferred_name, data['preferred_name'])
        self.assertEqual(user.profile.qualifications, data['qualifications'])
        self.assertEqual(user.profile.prior_employment, data['prior_employment'])
        self.assertEqual(user.profile.special_considerations, data['special_considerations'])
        self.assertEqual(user.profile.status.id, int(data['status']))
        self.assertEqual(user.profile.program.id, int(data['program']))
        self.assertEqual(user.profile.program_others, data['program_others'])
        self.assertEqual(user.profile.graduation_date.year, 2020)
        self.assertEqual(user.profile.graduation_date.month, 5)
        self.assertEqual(user.profile.graduation_date.day, 20)
        self.assertEqual( len(user.profile.degrees.all()), len(data['degrees']) )
        self.assertEqual(user.profile.degree_details, data['degree_details'])
        self.assertEqual( len(user.profile.trainings.all()), len(data['trainings']) )
        self.assertEqual(user.profile.training_details, data['training_details'])
        self.assertEqual(user.profile.lfs_ta_training, data['lfs_ta_training'])
        self.assertEqual(user.profile.lfs_ta_training_details, data['lfs_ta_training_details'])
        self.assertEqual(user.profile.ta_experience, data['ta_experience'])
        self.assertEqual(user.profile.ta_experience_details, data['ta_experience_details'])

        user = userApi.get_user(username, 'username')
        data = {
            'user': user.id,
            'uploaded': SimpleUploadedFile('resume.pdf', open(RESUME, 'rb').read(), content_type='application/pdf')
        }
        response = self.client.post( reverse('students:upload_resume') + NEXT + HOME_RESUME, data=data, format='multipart')
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:show_profile') + NEXT + HOME_RESUME)
        self.assertRedirects(response, response.url)

        resume = userApi.has_user_resume_created(user)
        self.assertIsNotNone(resume)


    def submit_confiential_information_international_complete(self, username):
        ''' Submit confidential information '''

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

    def submit_confiential_information_domestic_incomplete_employee_number(self, username):
        ''' Submit confidential information with an employee number '''

        SIN = self.testing_sin
        STUDY_PERMIT = self.testing_study_permit

        user = userApi.get_user(username, 'username')
        data = {
            'user': user.id,
            'nationality': '0'
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
            'is_new_employee': True,
            'employee_number': '',
            'sin': SimpleUploadedFile('sin.jpg', open(SIN, 'rb').read(), content_type='image/jpeg')
        }
        response = self.client.post( reverse('students:submit_confidentiality'), data=data, format='multipart' )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

    def submit_confiential_information_domestic_incomplete(self, username):
        ''' Submit confidential information - missing sin '''

        SIN = self.testing_sin
        STUDY_PERMIT = self.testing_study_permit

        user = userApi.get_user(username, 'username')
        data = {
            'user': user.id,
            'nationality': '0'
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
            'employee_number': random_with_N_digits(7)
        }
        response = self.client.post( reverse('students:submit_confidentiality'), data=data, format='multipart' )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

    def submit_confiential_information_international_incomplete(self, username):
        ''' Submit confidential information - missing date of birth and expired study permit expiry date'''

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
            'employee_number': random_with_N_digits(7),
            'sin': SimpleUploadedFile('sin.jpg', open(SIN, 'rb').read(), content_type='image/jpeg'),
            'sin_expiry_date': '2030-01-01',
            'study_permit': SimpleUploadedFile('study_permit.jpg', open(STUDY_PERMIT, 'rb').read(), content_type='image/jpeg'),
            'study_permit_expiry_date': '2019-05-05'
        }

        response = self.client.post( reverse('students:submit_confidentiality'), data=data, format='multipart' )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

    def delete_document(self, username, user_id, list, option='domestic'):
        ''' Delete a list of document '''
        if 'resume' in list:
            userApi.delete_user_resume(user_id)

        if 'sin' in list:
            if option == 'international':
                userApi.delete_user_sin(username, '1')
            else:
                userApi.delete_user_sin(username)

        if 'study_permit' in list:
            if option == 'international':
                userApi.delete_user_study_permit(username, '1')
            else:
                userApi.delete_user_study_permit(username)

    @tag('test_view_url_exists_at_desired_location_admin')
    def test_view_url_exists_at_desired_location_admin(self):
        print('- Test: view url exists at desired location - admin')

        self.login(USERS[0], PASSWORD)

        response = self.client.get( reverse('students:index') )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('students:available_jobs', args=[SESSION]) )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('students:apply_job', args=[SESSION, JOB]) + AVAILABLE_NEXT )
        self.assertEqual(response.status_code, 403)


    @tag('test_view_url_exists_at_desired_location_admin2')
    def test_view_url_exists_at_desired_location_admin2(self):
        print('- Test: view url exists at desired location - admin2')

        self.login('user3.admin', PASSWORD)

        response = self.client.get( reverse('students:index') )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('students:available_jobs', args=[SESSION]) )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('students:apply_job', args=[SESSION, JOB]) + AVAILABLE_NEXT )
        self.assertEqual(response.status_code, 403)


    @tag('test_view_url_exists_at_desired_location_instructor')
    def test_view_url_exists_at_desired_location_instructor(self):
        print('- Test: view url exists at desired location - instructor')

        self.login(USERS[1], PASSWORD)

        response = self.client.get( reverse('students:index') )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('students:available_jobs', args=[SESSION]) )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('students:apply_job', args=[SESSION, JOB]) + AVAILABLE_NEXT )
        self.assertEqual(response.status_code, 403)


    @tag('test_view_url_exists_at_desired_location_student')
    def test_view_url_exists_at_desired_location_student(self):
        print('- Test: view url exists at desired location - student')

        self.login()

        response = self.client.get( reverse('students:index') )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:show_profile') + NEXT + HOME_BASIC)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:available_jobs', args=[SESSION]) )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('students:apply_job', args=[SESSION, JOB]) + AVAILABLE_NEXT )
        self.assertEqual(response.status_code, 403)

        self.submit_profile_resume(USERS[2])
        self.submit_confiential_information_international_complete(USERS[2])

        response = self.client.get( reverse('students:index') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:show_profile') + NEXT + HOME_BASIC )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:edit_profile') + '?t=general' )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:show_confidentiality') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:submit_confidentiality') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:edit_confidentiality') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:explore_jobs') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:favourite_jobs') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:available_jobs', args=[SESSION]) )
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('students:history_jobs'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('students:terminate_job', args=[SESSION, 'apbi-260-001-agroecology-i-introduction-to-principles-and-techniques-w1']) + HISTORY_NEXT)
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:apply_job', args=[SESSION, JOB]) + AVAILABLE_NEXT )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:accept_decline_job', args=[SESSION, JOB]) + HISTORY_NEXT )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:show_job', args=[SESSION, JOB]) + HISTORY_NEXT + '&p=History%20of%20Jobs' )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:show_application', args=[APP]) + HISTORY_NEXT )
        self.assertEqual(response.status_code, 200)

        self.delete_document(USERS[2], USER_IDS[2], ['resume'])


    @tag('')
    def test_view_url_exists_at_desired_location_student2(self):
        print('- Test: view url exists at desired location - student2')

        self.login(STUDENT, PASSWORD)
        self.submit_confiential_information_international_complete(STUDENT)

        response = self.client.get( reverse('students:accept_decline_job', args=[SESSION, STUDENT_JOB]) + HISTORY_NEXT )
        self.assertEqual(response.status_code, 200)

        self.delete_document(STUDENT, STUDENT_ID, ['sin', 'study_permit'], 'international')


    @tag('')
    def test_home_page(self):
        print('- Test: Display a home page')
        self.login()

        response = self.client.get( reverse('students:index') )
        messages = self.messages(response)
        self.assertEqual(messages, [])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:show_profile') + NEXT + HOME_BASIC)
        self.assertRedirects(response, response.url)

        self.submit_profile_resume(USERS[2])
        response = self.client.get( reverse('students:index') )
        messages = self.messages(response)
        self.assertEqual(messages, [])
        self.assertEqual(response.status_code, 200)

        self.delete_document(USERS, USER_IDS[2], ['resume'])


    # It works in March or April
    @tag('')
    def test_alert_message(self):
        print('- Test: Display an alert message in March and April')
        self.login()

        response = self.client.get( reverse('students:index') )
        messages = self.messages(response)
        self.assertEqual(messages, [])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:show_profile') + NEXT + HOME_BASIC)
        self.assertRedirects(response, response.url)

        self.submit_profile_resume(USERS[2])
        response = self.client.get( reverse('students:index') )
        messages = self.messages(response)
        self.assertEqual(messages, [])
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context['loggedin_user'].username,  USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual(response.context['total_assigned_hours'], {'accepted': {'2019-W1': 100.0, '2019-W2': 50.0}})
        self.assertTrue(response.context['can_alert'])

        # Click on the Read button
        data = {
            'student': self.user.id,
            'has_read': 'true'
        }

        response = self.client.post( reverse('students:read_alert'), data=urlencode(data, True), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:index'))
        self.assertRedirects(response, response.url)

        res = self.client.get( reverse('students:index') )
        self.assertFalse(res.context['can_alert'])

        self.delete_document(USERS[2], USER_IDS[2], ['resume'])


    @tag('')
    def test_show_profile(self):
        print('- Test: Display all lists of session terms')
        self.login()

        next = '?next=/app/students/&p={0}&t={1}'
        next_wrong = '?nex=/app/students/&p={0}&t={1}'
        next_page_wrong = '?next=/app/students/&a={0}&t={1}'
        next_tab_wrong = '?next=/app/students/&p={0}&j={1}'

        response = self.client.get( reverse('students:show_profile') + next_wrong.format('Home', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:show_profile') + next_page_wrong.format('Home', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:show_profile') + next_tab_wrong.format('Home', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:show_profile') + next.format('Hom', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:show_profile') + next.format('Home', 'basid') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:show_profile') + next.format('Home', 'basic') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:show_profile') + next_wrong.format('Edit%20Profile', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:show_profile') + next_page_wrong.format('Edit%20Profile', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:show_profile') + next_tab_wrong.format('Edit%20Profile', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:show_profile') + next.format('EditProfile', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:show_profile') + next.format('Edit%20Profile', 'basid') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:show_profile') + next.format('Edit%20Profile', 'basic') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:show_profile') + next_wrong.format('Confidential%20Information', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:show_profile') + next_page_wrong.format('Confidential%20Information', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:show_profile') + next_tab_wrong.format('Confidential%20Information', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:show_profile') + next.format('Confidential%20information', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:show_profile') + next.format('Confidential%20Information', 'basid') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:show_profile') + next.format('Confidential%20Information', 'basic') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:show_profile') + NEXT + HOME_BASIC )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username,  USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertFalse(response.context['form'].is_bound)


    @tag('')
    def test_edit_profile(self):
        print('- Test: Edit user profile')
        self.login()

        # graduation date is none
        data1 = {
            'status': '3',
            'program': '5',
            'degrees': ['2', '5'],
            'degree_details': 'degree details',
            'training_details': 'training details',
            'lfs_ta_training': '1',
            'lfs_ta_training_details': 'Lfs ta training details',
            'ta_experience': '2',
            'ta_experience_details': 'Ta experience details',
            'qualifications': 'qualifications',
            'next': reverse('students:show_profile') + '?next=' + reverse('students:edit_profile') + EDIT_PROFILE_BASIC
        }

        response = self.client.post( reverse('students:edit_profile'), data=urlencode(data1, True), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred. Anticipated Graduation Date: This field is required.' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:edit_profile'))
        self.assertRedirects(response, response.url)

        # fill in the others of program
        data2 = {
            'status': '3',
            'program': '16',
            'graduation_date': '2020-05-05',
            'degrees': ['2', '5'],
            'degree_details': 'degree details',
            'training_details': 'training details',
            'lfs_ta_training': '1',
            'lfs_ta_training_details': 'Lfs ta training details',
            'ta_experience': '2',
            'ta_experience_details': 'Ta experience details',
            'qualifications': 'qualifications',
            'next': reverse('students:show_profile') + '?next=' + reverse('students:edit_profile') + EDIT_PROFILE_BASIC
        }

        response = self.client.post( reverse('students:edit_profile'), data=urlencode(data2, True), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred. Please indicate the name of your program if you select "Other" in Current Program.' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:edit_profile'))
        self.assertRedirects(response, response.url)

        # fill in the others of program and graduation date is none
        data3 = {
            'status': '3',
            'program': '16',
            'degrees': ['2', '5'],
            'degree_details': 'degree details',
            'training_details': 'training details',
            'lfs_ta_training': '1',
            'lfs_ta_training_details': 'Lfs ta training details',
            'ta_experience': '2',
            'ta_experience_details': 'Ta experience details',
            'qualifications': 'qualifications',
            'next': reverse('students:show_profile') + '?next=' + reverse('students:edit_profile') + EDIT_PROFILE_BASIC
        }

        response = self.client.post( reverse('students:edit_profile'), data=urlencode(data3, True), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred. Please indicate the name of your program if you select "Other" in Current Program. Anticipated Graduation Date: This field is required.' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:edit_profile'))
        self.assertRedirects(response, response.url)


        # qualification is none
        data4 = {
            'status': '3',
            'program': '5',
            'graduation_date': '2020-05-05',
            'degrees': ['2', '5'],
            'degree_details': 'degree details',
            'training_details': 'training details',
            'lfs_ta_training': '1',
            'lfs_ta_training_details': 'Lfs ta training details',
            'ta_experience': '2',
            'ta_experience_details': 'Ta experience details',
            'next': reverse('students:show_profile') + '?next=' + reverse('students:edit_profile') + EDIT_PROFILE_BASIC
        }

        response = self.client.post( reverse('students:edit_profile'), data=urlencode(data4, True), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred. Form is invalid. QUALIFICATIONS: This field is required.' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:edit_profile'))
        self.assertRedirects(response, response.url)

        data5 = {
            'preferred_name': 'preferred name',
            'status': '3',
            'program': '5',
            'program_others': '',
            'graduation_date': '2020-05-20',
            'degrees': ['2', '5'],
            'degree_details': 'degree details',
            'trainings': ['1', '2', '3'],
            'training_details': 'training details',
            'lfs_ta_training': '1',
            'lfs_ta_training_details': 'Lfs ta training details',
            'ta_experience': '2',
            'ta_experience_details': 'Ta experience details',
            'preferred_name': 'preferred name',
            'prior_employment': 'prior employment',
            'qualifications': 'qualifications',
            'special_considerations': 'special_considerations',
            'next': reverse('students:show_profile') + '?next=' + reverse('students:edit_profile') + EDIT_PROFILE_BASIC
        }

        response = self.client.post( reverse('students:edit_profile'), data=urlencode(data5, True), content_type=ContentType )
        messages = self.messages(response)
        self.assertEqual('An error occurred. Trainings: You must check all fields to proceed.', messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:edit_profile'))
        self.assertRedirects(response, response.url)

        data = {
            'preferred_name': 'preferred name',
            'status': '3',
            'program': '5',
            'program_others': '',
            'graduation_date': '2020-05-20',
            'degrees': ['2', '5'],
            'degree_details': 'degree details',
            'trainings': ['1', '2', '3', '4'],
            'training_details': 'training details',
            'lfs_ta_training': '1',
            'lfs_ta_training_details': 'Lfs ta training details',
            'ta_experience': '2',
            'ta_experience_details': 'Ta experience details',
            'preferred_name': 'preferred name',
            'prior_employment': 'prior employment',
            'qualifications': 'qualifications',
            'special_considerations': 'special_considerations',
            'next': reverse('students:show_profile') + '?next=' + reverse('students:edit_profile') + EDIT_PROFILE_BASIC
        }

        response = self.client.post( reverse('students:edit_profile'), data=urlencode(data, True), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:show_profile') + '?next=' + reverse('students:edit_profile') + EDIT_PROFILE_ADDITIONAL)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:show_profile') + '?next=' + reverse('students:edit_profile') + EDIT_PROFILE_ADDITIONAL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        user = response.context['loggedin_user']
        self.assertEqual(user.profile.preferred_name, data['preferred_name'])
        self.assertEqual(user.profile.qualifications, data['qualifications'])
        self.assertEqual(user.profile.prior_employment, data['prior_employment'])
        self.assertEqual(user.profile.special_considerations, data['special_considerations'])
        self.assertEqual(user.profile.status.id, int(data['status']))
        self.assertEqual(user.profile.program.id, int(data['program']))
        self.assertEqual(user.profile.program_others, data['program_others'])
        self.assertEqual(user.profile.graduation_date.year, 2020)
        self.assertEqual(user.profile.graduation_date.month, 5)
        self.assertEqual(user.profile.graduation_date.day, 20)
        self.assertEqual( len(user.profile.degrees.all()), len(data['degrees']) )
        self.assertEqual(user.profile.degree_details, data['degree_details'])
        self.assertEqual( len(user.profile.trainings.all()), len(data['trainings']) )
        self.assertEqual(user.profile.training_details, data['training_details'])
        self.assertEqual(user.profile.lfs_ta_training, data['lfs_ta_training'])
        self.assertEqual(user.profile.lfs_ta_training_details, data['lfs_ta_training_details'])
        self.assertEqual(user.profile.ta_experience, data['ta_experience'])
        self.assertEqual(user.profile.ta_experience_details, data['ta_experience_details'])


    """
    @tag('')
    def test_edit_profile_without_program_others(self):
        print('- Test: Edit profile without program others')
        self.login()

        data = {
            'preferred_name': 'preferred name',
            'status': '3',
            'program': '5',
            'program_others': '',
            'graduation_date': '2020-05-20',
            'degrees': ['2', '5'],
            'degree_details': 'degree details',
            'trainings': ['1', '2', '3', '4'],
            'training_details': 'training details',
            'lfs_ta_training': '1',
            'lfs_ta_training_details': 'Lfs ta training details',
            'ta_experience': '2',
            'ta_experience_details': 'Ta experience details',
            'preferred_name': 'preferred name',
            'prior_employment': 'prior employment',
            'qualifications': 'qualifications',
            'special_considerations': 'special_considerations'
        }

        self.assertEqual( len(userApi.get_programs()), 16 )
        userApi.delete_program( userApi.get_program_others_id() )
        self.assertEqual( len(userApi.get_programs()) , 15)
        response = self.client.post( reverse('students:edit_profile'), data=urlencode(data, True), content_type=ContentType )
        self.assertEqual(response.status_code, 403)"""


    @tag('')
    def test_upload_user_resume(self):
        print('- Test: upload user resume')
        self.login()

        user = userApi.get_user(USERS[2], 'username')
        RESUME = self.testing_resume

        self.assertIsNone(userApi.has_user_resume_created(user))

        data = {
            'user': user.id,
            'uploaded': SimpleUploadedFile('resume.pdf', open(RESUME, 'rb').read(), content_type='application/pdf')
        }
        response = self.client.post( reverse('students:upload_resume') + NEXT + HOME_RESUME, data=data, format='multipart')
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:show_profile') + NEXT + HOME_RESUME)
        self.assertRedirects(response, response.url)

        resume = userApi.has_user_resume_created(userApi.get_user(USERS[2], 'username'))
        self.assertIsNotNone(resume)

        response = self.client.get(reverse('students:show_profile') + NEXT + HOME_RESUME)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertIsNotNone(response.context['loggedin_user'].resume)

        self.delete_document(USERS[2], USER_IDS[2], ['resume'])


    @tag('')
    def test_delete_user_resume(self):
        print('- Test: delete user resume')
        self.login()

        user = userApi.get_user(USERS[2], 'username')
        RESUME = self.testing_resume

        data = {
            'user': user.id,
            'uploaded': SimpleUploadedFile('resume.pdf', open(RESUME, 'rb').read(), content_type='application/pdf')
        }
        response = self.client.post( reverse('students:upload_resume') + NEXT + HOME_RESUME, data=data, format='multipart' )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        resume = userApi.has_user_resume_created(userApi.get_user(USERS[2], 'username'))
        self.assertIsNotNone(resume)

        response = self.client.get(reverse('students:show_profile') + NEXT + HOME_RESUME)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertIsNotNone(response.context['user'].resume)

        response = self.client.post(reverse('students:delete_resume') + '?nex=/app/students/&p=Home&t=resume', data={ 'user': USERS[2] }, format='multipart')
        self.assertEqual(response.status_code, 404)

        response = self.client.post(reverse('students:delete_resume') + '?next=/app/studens/&p=Home&t=resume', data={ 'user': USERS[2] }, format='multipart')
        self.assertEqual(response.status_code, 404)

        response = self.client.post(reverse('students:delete_resume') + '?next=/app/students/&p=Hom&t=resume', data={ 'user': USERS[2] }, format='multipart')
        self.assertEqual(response.status_code, 404)

        response = self.client.post(reverse('students:delete_resume') + '?next=/app/students/&p=Hom&t=resumE', data={ 'user': USERS[2] }, format='multipart')
        self.assertEqual(response.status_code, 404)

        response = self.client.post( reverse('students:delete_resume') + NEXT + HOME_RESUME, data=urlencode({ 'user': USER_IDS[2] }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:show_profile') + NEXT + HOME_RESUME)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:show_profile') )
        self.assertEqual(response.status_code, 404)

        resume = userApi.has_user_resume_created(userApi.get_user(USERS[2], 'username'))
        self.assertIsNone(resume)


    @tag('')
    def test_show_confidentiality(self):
        print('- Test: Display user confidentiality')
        self.login()

        response = self.client.get( reverse('students:show_confidentiality') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])


    @tag('')
    def test_check_submit_confidentiality_empty_employee_number(self):
        print('- Test: Check and submit confidential information - empty employee number')
        self.login()

        user = userApi.get_user(USERS[2], 'username')
        data1 = {
            'user': user.id,
            'nationality': '1'
        }

        response = self.client.post( reverse('students:check_confidentiality'), data=urlencode(data1), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Please submit your information' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        data2 = {
            'user': user.id,
            'nationality': '1',
            'employee_number': '',
            'sin': SimpleUploadedFile('sin.jpg', open(self.testing_sin, 'rb').read(), content_type='image/jpeg'),
            'sin_expiry_date': '2020-01-01',
            'study_permit': SimpleUploadedFile('study_permit.jpg', open(self.testing_study_permit, 'rb').read(), content_type='image/jpeg'),
            'study_permit_expiry_date': '2020-05-05'
        }
        response = self.client.post( reverse('students:submit_confidentiality'), data=data2, format='multipart')
        messages = self.messages(response)
        self.assertTrue('An error occurred. New employees must check this <strong>I am a new employee</strong> field.' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)


    @tag('')
    def test_check_submit_confidentiality_not_new_employee(self):
        print('- Test: Check and submit confidential information - not new employee')
        self.login()

        user = userApi.get_user(USERS[2], 'username')
        data1 = {
            'user': user.id,
            'nationality': '1'
        }

        response = self.client.post( reverse('students:check_confidentiality'), data=urlencode(data1), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Please submit your information' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        data2 = {
            'user': user.id,
            'nationality': '1',
            'is_new_employee': 'true',
            'employee_number': '0000000',
            'sin': SimpleUploadedFile('sin.jpg', open(self.testing_sin, 'rb').read(), content_type='image/jpeg'),
            'sin_expiry_date': '2020-01-01',
            'study_permit': SimpleUploadedFile('study_permit.jpg', open(self.testing_study_permit, 'rb').read(), content_type='image/jpeg'),
            'study_permit_expiry_date': '2020-05-05'
        }
        response = self.client.post( reverse('students:submit_confidentiality'), data=data2, format='multipart')
        messages = self.messages(response)
        self.assertTrue('An error occurred. Please uncheck this <strong>I am a new employee</strong> field if you are not a new employee.' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)


    @tag('')
    def test_check_submit_confidentiality_checked_new_employee(self):
        print('- Test: Check and submit confidential information - checked new employee')
        self.login()

        user = userApi.get_user(USERS[2], 'username')
        userApi.create_confidentiality(user)

        user.confidentiality.is_new_employee = False
        user.confidentiality.employee_number = '0000000'
        user.confidentiality.save(update_fields=['is_new_employee', 'employee_number'])

        data3 = {
            'user': user.id,
            'nationality': '1',
            'is_new_employee': True,
            'employee_number': '0000000',
            'sin': SimpleUploadedFile('sin.jpg', open(self.testing_sin, 'rb').read(), content_type='image/jpeg'),
            'sin_expiry_date': '2020-01-01',
            'study_permit': SimpleUploadedFile('study_permit.jpg', open(self.testing_study_permit, 'rb').read(), content_type='image/jpeg'),
            'study_permit_expiry_date': '2020-05-05'
        }
        response = self.client.post( reverse('students:submit_confidentiality'), data=data3, format='multipart')
        messages = self.messages(response)
        self.assertTrue('An error occurred. Your Employee Number is 0000000. Only new employees can check this <strong>I am a new employee</strong> field.' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)


    @tag('')
    def test_check_submit_confidentiality_success(self):
        print('- Test: Check and submit confidential information - success')
        self.login()

        user = userApi.get_user(USERS[2], 'username')
        userApi.create_confidentiality(user)

        user.confidentiality.is_new_employee = True
        user.confidentiality.save(update_fields=['is_new_employee'])
        data4 = {
            'user': user.id,
            'nationality': '1',
            'date_of_birth': '2000-01-01',
            'is_new_employee': True,
            'employee_number': '',
            'sin': SimpleUploadedFile('sin.jpg', open(self.testing_sin, 'rb').read(), content_type='image/jpeg'),
            'sin_expiry_date': '2020-01-01',
            'study_permit': SimpleUploadedFile('study_permit.jpg', open(self.testing_study_permit, 'rb').read(), content_type='image/jpeg'),
            'study_permit_expiry_date': '2020-05-05'
        }
        response = self.client.post( reverse('students:submit_confidentiality'), data=data4, format='multipart' )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:show_confidentiality') )
        self.assertEqual(response.status_code, 200)

        loggedin_user = response.context['loggedin_user']
        self.assertEqual(loggedin_user.confidentiality.nationality, '1')
        self.assertEqual(loggedin_user.confidentiality.date_of_birth, datetime.date(2000, 1, 1))
        self.assertTrue(loggedin_user.confidentiality.is_new_employee)
        self.assertIsNone(loggedin_user.confidentiality.employee_number)
        self.assertEqual(loggedin_user.confidentiality.sin_expiry_date, datetime.date(2020, 1, 1))
        self.assertEqual(loggedin_user.confidentiality.study_permit_expiry_date, datetime.date(2020, 5, 5))

        self.delete_document(USERS[2], USER_IDS[2], ['sin', 'study_permit'], 'international')

        data5 = {
            'user': user.id,
            'nationality': '1',
            'date_of_birth': '2000-01-01',
            'employee_number': '0000009',
            'sin': SimpleUploadedFile('sin.jpg', open(self.testing_sin, 'rb').read(), content_type='image/jpeg'),
            'sin_expiry_date': '2020-01-01',
            'study_permit': SimpleUploadedFile('study_permit.jpg', open(self.testing_study_permit, 'rb').read(), content_type='image/jpeg'),
            'study_permit_expiry_date': '2020-05-05'
        }
        response = self.client.post( reverse('students:submit_confidentiality'), data=data5, format='multipart' )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:show_confidentiality') )
        self.assertEqual(response.status_code, 200)
        loggedin_user = response.context['loggedin_user']
        self.assertEqual(loggedin_user.confidentiality.nationality, '1')
        self.assertEqual(loggedin_user.confidentiality.date_of_birth, datetime.date(2000, 1, 1))
        self.assertFalse(loggedin_user.confidentiality.is_new_employee)
        self.assertEqual(loggedin_user.confidentiality.employee_number, data5['employee_number'])
        self.assertEqual(loggedin_user.confidentiality.sin_expiry_date, datetime.date(2020, 1, 1))
        self.assertEqual(loggedin_user.confidentiality.study_permit_expiry_date, datetime.date(2020, 5, 5))

        self.delete_document(USERS[2], USER_IDS[2], ['sin', 'study_permit'], 'international')


    @tag('')
    def test_edit_confidentiality(self):
        print('- Test: Edit confidentional information')
        self.login()

        user = userApi.get_user(USERS[2], 'username')
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
            'nationality': '1',
            'date_of_birth': '2000-01-01',
            'employee_number': '1234567',
            'sin_expiry_date': '2020-01-01',
            'study_permit_expiry_date': '2020-05-05'
        }
        response = self.client.post( reverse('students:submit_confidentiality'), data=data, format='multipart' )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        # edit date of birth, employee number sin_expiry_date, and study_permit_expiry_date
        data2 = {
            'user': user.id,
            'nationality': '1',
            'date_of_birth': '2000-11-11',
            'employee_number': '1234568',
            'sin_expiry_date': '2020-01-11',
            'study_permit_expiry_date': '2020-05-22'
        }
        response = self.client.post( reverse('students:edit_confidentiality'), data=data2, format='multipart' )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:show_confidentiality') )
        self.assertEqual(response.status_code, 200)
        loggedin_user = response.context['loggedin_user']
        self.assertEqual(loggedin_user.confidentiality.nationality, data2['nationality'])
        self.assertEqual(loggedin_user.confidentiality.date_of_birth, datetime.date(2000, 11, 11))
        self.assertFalse(loggedin_user.confidentiality.is_new_employee)
        self.assertEqual(loggedin_user.confidentiality.employee_number, data2['employee_number'])
        self.assertEqual(loggedin_user.confidentiality.sin_expiry_date, datetime.date(2020, 1, 11))
        self.assertEqual(loggedin_user.confidentiality.study_permit_expiry_date, datetime.date(2020, 5, 22))

        data3 = {
            'user': user.id,
            'nationality': '0',
        }
        response = self.client.post( reverse('students:edit_confidentiality'), data=data3, format='multipart' )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:show_confidentiality') )
        self.assertEqual(response.status_code, 200)
        loggedin_user = response.context['loggedin_user']
        self.assertEqual(loggedin_user.confidentiality.nationality, data3['nationality'])


    @tag('')
    def test_edit_confidentiality_checking(self):
        print('- Test: Edit confidentional information with checking conditions for employee number')
        self.login()

        user = userApi.get_user(USERS[2], 'username')
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
            'nationality': '1',
            'date_of_birth': '2000-01-01',
            'employee_number': '0000000',
            'sin_expiry_date': '2020-01-01',
            'study_permit_expiry_date': '2020-05-05'
        }
        response = self.client.post( reverse('students:submit_confidentiality'), data=data, format='multipart' )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        user1 = userApi.get_user(user.id)
        user1.confidentiality.is_new_employee = True
        user1.confidentiality.employee_number = None
        user1.confidentiality.save(update_fields=['is_new_employee', 'employee_number'])

        data1 = {
            'user': user1.id,
            'nationality': '1',
            'date_of_birth': '2000-01-01',
            'employee_number': '',
            'sin': SimpleUploadedFile('sin.jpg', open(self.testing_sin, 'rb').read(), content_type='image/jpeg'),
            'sin_expiry_date': '2020-01-01',
            'study_permit': SimpleUploadedFile('study_permit.jpg', open(self.testing_study_permit, 'rb').read(), content_type='image/jpeg'),
            'study_permit_expiry_date': '2020-05-05'
        }
        response = self.client.post( reverse('students:edit_confidentiality'), data=data1, format='multipart')
        messages = self.messages(response)
        self.assertTrue('An error occurred. New employees must check this <strong>I am a new employee</strong> field.' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        data2 = {
            'user': user1.id,
            'nationality': '1',
            'date_of_birth': '2000-01-01',
            'is_new_employee': True,
            'employee_number': '0000000',
            'sin': SimpleUploadedFile('sin.jpg', open(self.testing_sin, 'rb').read(), content_type='image/jpeg'),
            'sin_expiry_date': '2020-01-01',
            'study_permit': SimpleUploadedFile('study_permit.jpg', open(self.testing_study_permit, 'rb').read(), content_type='image/jpeg'),
            'study_permit_expiry_date': '2020-05-05'
        }
        response = self.client.post( reverse('students:edit_confidentiality'), data=data2, format='multipart')
        messages = self.messages(response)
        self.assertTrue('An error occurred. Please uncheck this <strong>I am a new employee</strong> field if you are not a new employee.' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        user3 = userApi.get_user(user.id)
        user3.confidentiality.is_new_employee = False
        user3.confidentiality.employee_number = '0000000'
        user3.confidentiality.save(update_fields=['is_new_employee', 'employee_number'])
        data3 = {
            'user': user3.id,
            'nationality': '1',
            'date_of_birth': '2000-01-01',
            'is_new_employee': True,
            'employee_number': '0000000',
            'sin': SimpleUploadedFile('sin.jpg', open(self.testing_sin, 'rb').read(), content_type='image/jpeg'),
            'sin_expiry_date': '2020-01-01',
            'study_permit': SimpleUploadedFile('study_permit.jpg', open(self.testing_study_permit, 'rb').read(), content_type='image/jpeg'),
            'study_permit_expiry_date': '2020-05-05'
        }
        response = self.client.post( reverse('students:edit_confidentiality'), data=data3, format='multipart')
        messages = self.messages(response)
        self.assertTrue('An error occurred. Your Employee Number is 0000000. Only new employees can check this <strong>I am a new employee</strong> field.' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        self.delete_document(USERS[2], USER_IDS[2], ['sin', 'study_permit'], 'international')


    @tag('')
    def test_delete_confidential_information(self):
        print('- Test: delete confidential information')
        self.login()

        self.submit_confiential_information_international_complete(USERS[2])

        response = self.client.get( reverse('students:show_confidentiality') )
        self.assertEqual(response.status_code, 200)

        user = response.context['loggedin_user']
        self.assertEqual(user.confidentiality.nationality, '1')
        self.assertEqual(user.confidentiality.date_of_birth, datetime.date(2000, 1, 1))
        self.assertFalse(user.confidentiality.is_new_employee)
        self.assertIsNotNone(user.confidentiality.employee_number)
        self.assertEqual(user.confidentiality.sin_expiry_date, datetime.date(2030, 1, 1))
        self.assertEqual(user.confidentiality.study_permit_expiry_date, datetime.date(2030, 1, 1))
        self.assertEqual(user.confidentiality.sin, 'users/user100.test/sin/sin.jpg')
        self.assertEqual(user.confidentiality.study_permit, 'users/user100.test/study_permit/study_permit.jpg')

        data = {
            'user': USERS[2],
            'date_of_birth': 'on',
            'employee_number': 'on',
            'sin': 'on',
            'sin_expiry_date': 'on',
            'study_permit': 'on',
            'study_permit_expiry_date': 'on'
        }
        response = self.client.post( reverse('students:delete_confidential_information'), data=data, format='multipart' )
        messages = self.messages(response)
        self.assertEqual(messages[0], 'Success! Confidential Information of user100.test deleted')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        user = userApi.get_user(USERS[2], 'username')
        self.assertIsNotNone(userApi.has_user_confidentiality_created(user))

        self.assertEqual(user.confidentiality.nationality, '1')
        self.assertEqual(user.confidentiality.date_of_birth, None)
        self.assertFalse(user.confidentiality.is_new_employee)
        self.assertEqual(user.confidentiality.employee_number, None)
        self.assertEqual(user.confidentiality.sin_expiry_date, None)
        self.assertEqual(user.confidentiality.study_permit_expiry_date, None)
        self.assertFalse( bool(user.confidentiality.sin) )
        self.assertFalse( bool(user.confidentiality.sin) )


    @tag('')
    def test_delete_confidential_information_nothing_selected(self):
        print('- Test: delete confidential information - nothing selected')
        self.login()

        self.submit_confiential_information_international_complete(USERS[2])

        data = {
            'user': USERS[2]
        }
        response = self.client.post( reverse('students:delete_confidential_information'), data=data, format='multipart'  )
        messages = self.messages(response)
        self.assertEqual(messages[0], 'An error occurred while deleting. Please select any information that you want to delete.')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)


        user = userApi.get_user(USERS[2], 'username')
        self.assertIsNotNone(userApi.has_user_confidentiality_created(user))

        self.assertEqual(user.confidentiality.nationality, '1')
        self.assertEqual(user.confidentiality.date_of_birth, datetime.date(2000, 1, 1))
        self.assertFalse(user.confidentiality.is_new_employee)
        self.assertIsNotNone(user.confidentiality.employee_number)
        self.assertEqual(user.confidentiality.sin_expiry_date, datetime.date(2030, 1, 1))
        self.assertEqual(user.confidentiality.study_permit_expiry_date, datetime.date(2030, 1, 1))
        self.assertEqual(user.confidentiality.sin, 'users/user100.test/sin/sin.jpg')
        self.assertEqual(user.confidentiality.study_permit, 'users/user100.test/study_permit/study_permit.jpg')

        self.delete_document(USERS[2], USER_IDS[2], ['sin', 'study_permit'], 'international')


    @tag('test_explore_jobs')
    def test_explore_jobs(self):
        print('- Test: Display all lists of session terms')
        self.login()

        response = self.client.get(reverse('students:explore_jobs'))
        messages = self.messages(response)
        self.assertTrue('Important' in messages[0])

        self.submit_profile_resume(USERS[2])

        response = self.client.get(reverse('students:explore_jobs'))
        messages = self.messages(response)
        self.assertEqual(messages, [])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        self.assertEqual(len(response.context['visible_current_sessions']), 3)
        self.assertEqual(len(response.context['favourites']), 3)
        self.assertTrue(response.context['can_apply'])
        self.assertEqual(response.context['expiry_status'], [])
        self.assertEqual(response.context['this_year'], 2024)

        for session in response.context['visible_current_sessions']:
            self.assertTrue(session.is_locked)

        self.delete_document(USERS[2], USER_IDS[2], ['resume'])


    @tag('test_unlock_sessions')
    def test_unlock_sessions(self):
        print('- Test: unlock sessions')

        self.login()

        self.submit_profile_resume(USERS[2])
        self.submit_confiential_information_international_complete(USERS[2])

        response = self.client.get( reverse('students:explore_jobs') )
        messages = self.messages(response)
        self.assertEqual(messages, [])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        self.assertEqual(len(response.context['visible_current_sessions']), 3)
        self.assertEqual(len(response.context['favourites']), 3)
        self.assertTrue(response.context['can_apply'])
        self.assertEqual(response.context['expiry_status'], [])
        self.assertEqual(response.context['this_year'], 2024)

        sessions = []
        for session in response.context['visible_current_sessions']:
            self.assertTrue(session.is_locked)
            sessions.append(session.slug)

            res1 = self.client.get(reverse('students:edit_profile') + '?t=summary&session=' + session.slug)
            self.assertEqual(res1.status_code, 200)
            self.assertEqual(res1.context['total_assigned_hours'], 80.0)
            self.assertEqual(res1.context['path'], 'graduate')
            self.assertEqual(res1.context['current_tab'], 'summary')
            self.assertFalse(res1.context['confirm_profile_reminder'])

            data = {
                'user': USERS[2],
                'session': session.slug,
                'next': reverse('students:edit_profile') + '?t=summary&session=' + session.slug
            }
            res2 = self.client.post(reverse('students:confirm_profile_reminder'), data=data, content_type=ContentType)
            messages = self.messages(res2)

        self.delete_document(USERS[2], USER_IDS[2], ['resume'])


    @tag('')
    def test_favrouite_jobs(self):
        print('- Test: Display all lists of favourite jobs')
        self.login()

        response = self.client.get( reverse('students:favourite_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        self.assertEqual( len(response.context['favourites']), 3 )


    @tag('')
    def test_select_favourite_job(self):
        print('- Test: Select favourite job')
        self.login()

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT )
        self.assertEqual(response.status_code, 403)

        self.submit_profile_resume(USERS[2])

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT )
        self.assertEqual(response.status_code, 200)

        loggedin_user = response.context['loggedin_user']

        data0 = {
            'applicant': loggedin_user.id,
            'job': 109,
            'is_selected': True,
            'next': '/app/student/sessions/2019-w1/jobs/available/?page=2'
        }
        response = self.client.post( reverse('students:select_favourite_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT, data=urlencode(data0), content_type=ContentType )
        self.assertEqual(response.status_code, 404)

        data1 = {
            'applicant': loggedin_user.id,
            'job': 109,
            'is_selected': True,
            'next': '/app/students/Sessions/2019-w1/jobs/available/?page=2'
        }
        response = self.client.post( reverse('students:select_favourite_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT, data=urlencode(data1), content_type=ContentType )
        self.assertEqual(response.status_code, 404)

        data2 = {
            'applicant': loggedin_user.id,
            'job': 109,
            'is_selected': True,
            'next': '/app/students/sessions/2019-w3/jobs/available/?page=2'
        }
        response = self.client.post( reverse('students:select_favourite_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT, data=urlencode(data2), content_type=ContentType )
        self.assertEqual(response.status_code, 404)

        data3 = {
            'applicant': loggedin_user.id,
            'job': 109,
            'is_selected': True,
            'next': '/app/students/sessions/2019-w1/job/available/?page=2'
        }
        response = self.client.post( reverse('students:select_favourite_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT, data=urlencode(data3), content_type=ContentType )
        self.assertEqual(response.status_code, 404)


        data4 = {
            'applicant': loggedin_user.id,
            'job': 109,
            'is_selected': True,
            'next': '/app/students/sessions/2019-w1/jobs/availablee/?page=2'
        }
        response = self.client.post( reverse('students:select_favourite_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT, data=urlencode(data4), content_type=ContentType )
        self.assertEqual(response.status_code, 404)

        data5 = {
            'applicant': response.context['loggedin_user'].id,
            'job': 109,
            'is_selected': True,
            'next': AVAILABLE_PATH
        }
        response = self.client.post( reverse('students:select_favourite_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT, data=urlencode(data5), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT)
        #self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:favourite_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        self.assertEqual( len(response.context['favourites']), 4 )

        self.delete_document(USERS[2], USER_IDS[2], ['resume'])


    @tag('')
    def test_available_jobs(self):
        print('- Test: Display jobs available to apply')
        self.login()

        response = self.client.get( reverse('students:available_jobs', args=[SESSION]) )
        self.assertEqual(response.status_code, 403)

        self.submit_profile_resume(USERS[2])

        response = self.client.get( reverse('students:available_jobs', args=[SESSION]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual( len(response.context['jobs']), 50 )

        self.delete_document(USERS[2], USER_IDS[2], ['resume'])


    @tag('')
    def test_apply_job_undergraduate(self):
        print('- Test: Undergraduate students can apply for each job')
        self.login()

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT )
        self.assertEqual(response.status_code, 403)

        self.submit_profile_resume_undergraduate(USERS[2])

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual(response.context['job'].course.slug, STUDENT_JOB)
        self.assertFalse(response.context['has_applied_job'])
        self.assertFalse(response.context['form'].is_bound)

        data = {
            'applicant': response.context['loggedin_user'].id,
            'job': response.context['job'].id,
            'how_qualified': '4',
            'how_interested': '3',
            'availability': True,
            'availability_note': 'nothing',
            'next': AVAILABLE_PATH
        }
        response = self.client.post( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT, data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, AVAILABLE_PATH)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual(response.context['job'].course.slug, STUDENT_JOB)
        self.assertTrue(response.context['has_applied_job'])
        self.assertFalse(response.context['form'].is_bound)

        self.delete_document(USERS[2], USER_IDS[2], ['resume'])


    @tag('')
    def test_apply_job_no_supervisor_approval(self):
        print('- Test: Graudate students cannot apply for each job without supervisor approval')
        self.login()

        self.submit_profile_resume(USERS[2])

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual(response.context['job'].course.slug, STUDENT_JOB)
        self.assertFalse(response.context['has_applied_job'])
        self.assertFalse(response.context['form'].is_bound)

        data = {
            'applicant': response.context['loggedin_user'].id,
            'job': response.context['job'].id,
            'how_qualified': '4',
            'how_interested': '3',
            'availability': True,
            'availability_note': 'nothing',
            'next': AVAILABLE_PATH
        }
        response = self.client.post( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT, data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred. You must check "Yes" in the box under "Supervisor Approval" if you are a graduate student. Undergraduate students should leave this box blank.' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT)
        #self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual(response.context['job'].course.slug, STUDENT_JOB)
        self.assertFalse(response.context['has_applied_job'])
        self.assertFalse(response.context['form'].is_bound)

        self.delete_document(USERS[2], USER_IDS[2], ['resume'])


    @tag('')
    def test_apply_job(self):
        print('- Test: Graudate students can apply for each job')
        self.login()
        self.submit_profile_resume(USERS[2])

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + '?nex=' + reverse('students:favourite_jobs') + '?page=2' )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + '?next=/app/Students/jobs/favourite/?page=2' )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + '?next=/app/student/jobs/favourite/?page=2' )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + '?next=/app/student/Jobs/favourite/?page=2' )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + '?next=/app/students/jobs/favorite/?page=2' )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + '?next=' + reverse('students:favourite_jobs') + '?page=2' )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + '?nex=/app' + AVAILABLE_NEXT )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + '?next=/app/students/session/2019-w1/jobs/available/' )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + '?next=/app/students/sessions/2019-w11/jobs/available/' )
        self.assertEqual(response.status_code, 404)

        session = adminApi.get_session(SESSION, 'slug')
        session.is_visible = False
        session.save(update_fields=['is_visible'])

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT )
        self.assertEqual(response.status_code, 403)

        session.is_visible = True
        session.is_archived = True
        session.save(update_fields=['is_visible', 'is_archived'])

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT )
        self.assertEqual(response.status_code, 403)

        session.is_archived = False
        session.save(update_fields=['is_archived'])

        j = adminApi.get_job_by_session_slug_job_slug(SESSION, STUDENT_JOB)
        j.is_active = False
        j.save(update_fields=['is_active'])

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT )
        self.assertEqual(response.status_code, 403)

        j.is_active = True
        j.save(update_fields=['is_active'])

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual(response.context['job'].course.slug, STUDENT_JOB)
        self.assertFalse(response.context['has_applied_job'])
        self.assertFalse(response.context['form'].is_bound)

        loggedin_user = response.context['loggedin_user']
        job = response.context['job']

        data0 = {
            'applicant':loggedin_user.id,
            'job': job.id,
            'supervisor_approval': True,
            'how_qualified': '4',
            'how_interested': '3',
            'availability': True,
            'availability_note': 'nothing',
            'next': '/app/student/sessions/2019-w1/jobs/available/?page=2'
        }
        response = self.client.post( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT, data=urlencode(data0), content_type=ContentType )
        self.assertEqual(response.status_code, 404)

        data1 = {
            'applicant': loggedin_user.id,
            'job': job.id,
            'supervisor_approval': True,
            'how_qualified': '4',
            'how_interested': '3',
            'availability': True,
            'availability_note': 'nothing',
            'next': '/app/students/Sessions/2019-w1/jobs/available/?page=2'
        }
        response = self.client.post( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT, data=urlencode(data1), content_type=ContentType )
        self.assertEqual(response.status_code, 404)

        data2 = {
            'applicant': loggedin_user.id,
            'job': job.id,
            'supervisor_approval': True,
            'how_qualified': '4',
            'how_interested': '3',
            'availability': True,
            'availability_note': 'nothing',
            'next': '/app/students/sessions/2019-w3/jobs/available/?page=2'
        }
        response = self.client.post( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT, data=urlencode(data2), content_type=ContentType )
        self.assertEqual(response.status_code, 404)

        data3 = {
            'applicant': loggedin_user.id,
            'job': job.id,
            'supervisor_approval': True,
            'how_qualified': '4',
            'how_interested': '3',
            'availability': True,
            'availability_note': 'nothing',
            'next': '/app/students/sessions/2019-w1/job/available/?page=2'
        }
        response = self.client.post( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT, data=urlencode(data3), content_type=ContentType )
        self.assertEqual(response.status_code, 404)


        data4 = {
            'applicant': loggedin_user.id,
            'job': job.id,
            'supervisor_approval': True,
            'how_qualified': '4',
            'how_interested': '3',
            'availability': True,
            'availability_note': 'nothing',
            'next': '/app/students/sessions/2019-w1/jobs/availablee/?page=2'
        }
        response = self.client.post( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT, data=urlencode(data4), content_type=ContentType )
        self.assertEqual(response.status_code, 404)

        data5 = {
            'applicant': loggedin_user.id,
            'job': job.id,
            'supervisor_approval': True,
            'how_qualified': '4',
            'how_interested': '3',
            'availability': True,
            'availability_note': 'nothing',
            'next': AVAILABLE_PATH
        }
        response = self.client.post( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT, data=urlencode(data5), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, AVAILABLE_PATH)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual(response.context['job'].course.slug, STUDENT_JOB)
        self.assertTrue(response.context['has_applied_job'])
        self.assertFalse(response.context['form'].is_bound)

        self.delete_document(USERS[2], USER_IDS[2], ['resume'])


    @tag('')
    def test_cannot_apply_jobs(self):
        print('- Test: Students cannot apply for each job')

        # not student role
        self.login(USERS[0], PASSWORD)
        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT )
        self.assertEqual(response.status_code, 403)

        self.login(USERS[1], PASSWORD)
        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT )
        self.assertEqual(response.status_code, 403)

        self.login()

        # didn't complete profile and resume
        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT )
        self.assertEqual(response.status_code, 403)

        self.submit_profile_resume(USERS[2])

        session = adminApi.get_session(SESSION, 'slug')
        session.is_visible = False
        session.is_archived = True
        session.save(update_fields=['is_visible', 'is_archived'])

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT )
        self.assertEqual(response.status_code, 403)

        session = adminApi.get_session(SESSION, 'slug')
        session.is_visible = True
        session.is_archived = True
        session.save(update_fields=['is_visible', 'is_archived'])

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT )
        self.assertEqual(response.status_code, 403)

        job = adminApi.get_job_by_session_slug_job_slug(SESSION, STUDENT_JOB)
        job.is_active = False
        job.save(update_fields=['is_active'])

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT )
        self.assertEqual(response.status_code, 403)

        self.delete_document(USERS[2], USER_IDS[2], ['resume'])


    """
    @tag('')
    def test_apply_jobs_without_undergraduate(self):
        print('- Test: Students apply with undergraduate')

        self.login()

        self.assertEqual( len(userApi.get_statuses()), 9 )
        userApi.delete_status( userApi.get_undergraduate_status_id() )
        self.assertEqual( len(userApi.get_statuses()) , 8)

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) + AVAILABLE_NEXT )
        self.assertEqual(response.status_code, 403)"""


    @tag('')
    def test_history_jobs(self):
        print('- Test: Display History of Jobs applied by a student')
        self.login()

        response = self.client.get( reverse('students:history_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual( len(response.context['apps']), 7 )


    @tag('')
    def test_accept_decline_job_domestic_incomplete(self):
        print('- Test: Display a job to select accept a job offer with domestic students')
        self.login(STUDENT, PASSWORD)

        user = userApi.get_user(STUDENT, 'username')

        # if students don't complete required documents, they cannot accept or decline their job offer.
        available1 = userApi.add_confidentiality_validation(user)
        self.assertEqual(available1['status'], False)
        self.assertEqual(available1['message'], "You haven't completed it yet. Please upload required documents.")

        response = self.client.get( reverse('students:accept_decline_job', args=[SESSION, STUDENT_JOB]) + HISTORY_NEXT )
        self.assertEqual(response.status_code, 200)

        self.submit_confiential_information_domestic_incomplete(user.username)

        user = userApi.get_user(STUDENT, 'username')
        available2 = userApi.add_confidentiality_validation(user)
        self.assertEqual(available2['status'], False)
        self.assertEqual(available2['message'], 'Please check the following information, and update required documents. <ul><li>SIN</li></ul>')

        self.delete_document(STUDENT, STUDENT_ID, [])


    @tag('')
    def test_accept_decline_job_domestic_incomplete_employee_number(self):
        print('- Test: Display a job to select accept a job offer with domestic students without an employee number')
        self.login(STUDENT, PASSWORD)

        user = userApi.get_user(STUDENT, 'username')

        # if students don't complete required documents, they cannot accept or decline their job offer.
        available1 = userApi.add_confidentiality_validation(user)
        self.assertFalse(available1['status'])
        self.assertEqual(available1['message'], "You haven't completed it yet. Please upload required documents.")

        response = self.client.get( reverse('students:accept_decline_job', args=[SESSION, STUDENT_JOB]) + HISTORY_NEXT )
        self.assertEqual(response.status_code, 200)

        self.submit_confiential_information_domestic_incomplete_employee_number(user.username)

        user2 = userApi.get_user(STUDENT, 'username')
        available2 = userApi.add_confidentiality_validation(user2)
        self.assertTrue(available2['status'])
        self.assertEqual(available2['message'], '')

        user2.confidentiality.is_new_employee = False
        user2.confidentiality.save(update_fields=['is_new_employee'])
        available3 = userApi.add_confidentiality_validation(user2)
        self.assertFalse(available3['status'])
        self.assertEqual(available3['message'], 'Please check the following information, and update required documents. <ul><li>Employee Number</li></ul>')

        self.delete_document(STUDENT, STUDENT_ID, ['sin'])


    @tag('')
    def test_accept_decline_job_international_incomplete(self):
        print('- Test: Display a job to select accept or decline a job offer with international students')
        self.login(STUDENT, PASSWORD)

        user = userApi.get_user(STUDENT, 'username')

        # if students don't complete required documents, they cannot accept or decline their job offer.
        available1 = userApi.add_confidentiality_validation(user)
        self.assertEqual(available1['status'], False)
        self.assertEqual(available1['message'], "You haven't completed it yet. Please upload required documents.")

        response = self.client.get( reverse('students:accept_decline_job', args=[SESSION, STUDENT_JOB]) + HISTORY_NEXT )
        self.assertEqual(response.status_code, 200)

        self.submit_confiential_information_international_incomplete(user.username)

        user2 = userApi.get_user(STUDENT, 'username')
        available2 = userApi.add_confidentiality_validation(user2)
        self.assertEqual(available2['status'], False)
        self.assertEqual(available2['message'], 'Please check the following information, and update required documents. <ul><li>Date of Birth</li><li>Study Permit Expiry Date</li></ul>')

        user2.confidentiality.is_new_employee = False
        user2.confidentiality.save(update_fields=['is_new_employee'])
        available3 = userApi.add_confidentiality_validation(user2)
        self.assertFalse(available3['status'])
        self.assertEqual(available3['message'], 'Please check the following information, and update required documents. <ul><li>Date of Birth</li><li>Study Permit Expiry Date</li></ul>')

        user2.confidentiality.employee_number = None
        user2.confidentiality.save(update_fields=['employee_number'])
        available4 = userApi.add_confidentiality_validation(user2)
        self.assertFalse(available4['status'])
        self.assertEqual(available4['message'], 'Please check the following information, and update required documents. <ul><li>Employee Number</li><li>Date of Birth</li><li>Study Permit Expiry Date</li></ul>')

        self.delete_document(STUDENT, STUDENT_ID, ['sin', 'study_permit'], 'international')


    @tag('')
    def test_accept_decline_job(self):
        print('- Test: Display a job to select accept or decline a job offer')
        self.login(STUDENT, PASSWORD)

        response = self.client.get( reverse('students:accept_decline_job', args=[SESSION, STUDENT_JOB]) + HISTORY_WRONG_1 )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:accept_decline_job', args=[SESSION, STUDENT_JOB]) + HISTORY_WRONG_2 )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:accept_decline_job', args=[SESSION, STUDENT_JOB]) + HISTORY_WRONG_3 )
        self.assertEqual(response.status_code, 404)

        session = adminApi.get_session(SESSION, 'slug')
        session.is_archived = True
        session.save(update_fields=['is_archived'])

        response = self.client.get( reverse('students:accept_decline_job', args=[SESSION, STUDENT_JOB]) + HISTORY_NEXT )
        self.assertEqual(response.status_code, 403)

        session.is_archived = False
        session.save(update_fields=['is_archived'])

        user = userApi.get_user(STUDENT, 'username')

        # if students don't complete required documents, they cannot accept their job offer.
        available1 = userApi.add_confidentiality_validation(user)
        self.assertEqual(available1['status'], False)
        self.assertEqual(available1['message'], "You haven't completed it yet. Please upload required documents.")

        response = self.client.get( reverse('students:accept_decline_job', args=[SESSION, STUDENT_JOB]) + HISTORY_NEXT )
        self.assertEqual(response.status_code, 200)

        self.submit_confiential_information_international_complete(user.username)

        user = userApi.get_user(STUDENT, 'username')
        available2 = userApi.add_confidentiality_validation(user)
        self.assertEqual(available2['status'], True)
        self.assertEqual(available2['message'], '')

        response = self.client.get( reverse('students:accept_decline_job', args=[SESSION, STUDENT_JOB]) + HISTORY_NEXT )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, STUDENT)
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual(response.context['app'].job.session.slug, SESSION)
        self.assertEqual(response.context['app'].job.course.slug, STUDENT_JOB)
        self.assertEqual(response.context['app'].applicant.username, STUDENT)
        self.assertEqual(response.context['app'].offered.get_assigned_display(), 'Offered')
        self.assertEqual(response.context['app'].offered.assigned_hours, 15.0)
        self.assertFalse(response.context['app'].accepted)
        self.assertFalse( response.context['app'].declined )

        self.delete_document(STUDENT, STUDENT_ID, ['sin', 'study_permit'], 'international')


    @tag('')
    def test_accept_offer(self):
        print('- Test: Students accept a job offer')
        self.login(STUDENT, PASSWORD)

        self.submit_confiential_information_international_complete(STUDENT)

        response = self.client.get( reverse('students:accept_decline_job', args=[SESSION, STUDENT_JOB]) + HISTORY_NEXT )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, STUDENT)
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        app = response.context['app']
        self.assertEqual(app.job.course.slug, STUDENT_JOB)
        self.assertEqual(app.applicant.username, STUDENT)

        data1 = {
            'application': app.id,
            'assigned_hours': app.offered.assigned_hours,
            'decision': 'accept',
            'next': reverse('students:history_jobs') + '?page=2'
        }
        response = self.client.post( reverse('students:make_decision', args=[SESSION, STUDENT_JOB]), data=urlencode(data1), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:accept_decline_job', args=[SESSION, STUDENT_JOB]) + HISTORY_NEXT)
        self.assertRedirects(response, response.url)

        data2 = {
            'application': app.id,
            'assigned_hours': app.offered.assigned_hours,
            'has_contract_read': 'true',
            'next': reverse('students:history_jobs') + '?page=2'
        }
        response = self.client.post( reverse('students:make_decision', args=[SESSION, STUDENT_JOB]), data=urlencode(data2), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:accept_decline_job', args=[SESSION, STUDENT_JOB]) + HISTORY_NEXT)
        self.assertRedirects(response, response.url)

        data3 = {
            'application': app.id,
            'assigned_hours': app.offered.assigned_hours,
            'decision': 'accept',
            'has_contract_read': 'true',
            'next': '/app/students/jobs/histry/?page=2'
        }
        response = self.client.post( reverse('students:make_decision', args=[SESSION, STUDENT_JOB]), data=urlencode(data3), content_type=ContentType )
        self.assertEqual(response.status_code, 404)

        data4 = {
            'application': app.id,
            'assigned_hours': app.offered.assigned_hours,
            'decision': 'accept',
            'has_contract_read': 'true',
            'next': reverse('students:history_jobs') + '?page=2'
        }
        response = self.client.post( reverse('students:make_decision', args=[SESSION, STUDENT_JOB]), data=urlencode(data4), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:history_jobs') + '?page=2')
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:history_jobs') + '?page=2' )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, STUDENT)
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        apps = response.context['apps']
        self.assertEqual( len(apps), 3 )

        appl = None
        for a in apps:
            if a.id == app.id: appl = a

        self.assertEqual(appl.job.session.slug, SESSION)
        self.assertEqual(appl.job.course.slug, STUDENT_JOB)
        self.assertEqual(appl.accepted.get_assigned_display(), 'Accepted')
        self.assertEqual(appl.accepted.assigned_hours, data4['assigned_hours'])
        self.assertTrue(appl.accepted.has_contract_read)
        self.assertEqual(appl.job.assigned_ta_hours, app.job.assigned_ta_hours)
        self.assertEqual(appl.job.accumulated_ta_hours, app.job.accumulated_ta_hours + appl.accepted.assigned_hours)

        total_hours = adminApi.get_total_assigned_hours(apps, ['accepted'])
        self.assertEqual(total_hours['accepted'], {'2019-W1': appl.accepted.assigned_hours})

        self.delete_document(STUDENT, STUDENT_ID, ['sin', 'study_permit'], 'international')


    @tag('')
    def test_today_accepted_application_student(self):
        print('- Test: Display today accepted applications - student')
        self.login(STUDENT, PASSWORD)

        self.submit_confiential_information_international_complete(STUDENT)

        response = self.client.get( reverse('students:accept_decline_job', args=[SESSION, STUDENT_JOB]) + HISTORY_NEXT )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, STUDENT)
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        app = response.context['app']
        self.assertEqual(app.job.course.slug, STUDENT_JOB)
        self.assertEqual(app.applicant.username, STUDENT)

        data1 = {
            'application': app.id,
            'assigned_hours': app.offered.assigned_hours,
            'decision': 'accept',
            'has_contract_read': 'true',
            'next': reverse('students:history_jobs') + '?page=2'
        }
        response = self.client.post( reverse('students:make_decision', args=[SESSION, STUDENT_JOB]), data=urlencode(data1), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:history_jobs') + '?page=2')
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:history_jobs') + '?page=2' )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, STUDENT)
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        apps = response.context['apps']
        self.assertEqual( len(apps), 3 )

        appl = None
        for a in apps:
            if a.id == app.id: appl = a

        self.assertEqual(appl.job.session.slug, SESSION)
        self.assertEqual(appl.job.course.slug, STUDENT_JOB)
        self.assertEqual(appl.accepted.get_assigned_display(), 'Accepted')
        self.assertEqual(appl.accepted.assigned_hours, data1['assigned_hours'])
        self.assertTrue(appl.accepted.has_contract_read)
        self.assertEqual(appl.job.assigned_ta_hours, app.job.assigned_ta_hours)
        self.assertEqual(appl.job.accumulated_ta_hours, app.job.accumulated_ta_hours + appl.accepted.assigned_hours)

        total_hours = adminApi.get_total_assigned_hours(apps, ['accepted'])
        self.assertEqual(total_hours['accepted'], {'2019-W1': appl.accepted.assigned_hours})


        self.login(USERS[0], PASSWORD)
        response = self.client.get(reverse('administrators:accepted_applications'))
        self.assertEqual(response.status_code, 200)
        today_accepted_apps = response.context['today_accepted_apps']
        today_processed_stats = response.context['today_processed_stats']
        today = response.context['today']

        self.assertEqual(len(today_accepted_apps), 1)
        self.assertEqual(today_processed_stats['processed'], 0)
        self.assertEqual(today_processed_stats['not_processed'], 1)
        self.assertEqual(today.strftime('%Y-%m-%d'), datetime.date.today().strftime('%Y-%m-%d'))

        # enter processed
        data2 = {
            'application': appl.id,
            'pin': '1237',
            'tasm': True,
            'processed': 'Done',
            'worktag': 'adsf1111',
            'processing_note': 'this is a processing note'
        }
        response = self.client.post(reverse('administrators:update_admin_docs'), data=urlencode(data2), content_type=ContentType)
        messages = self.json_messages(response)
        self.assertTrue('success', messages['status'])
        self.assertTrue('Success' in messages['message'])
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('administrators:accepted_applications'))
        self.assertEqual(response.status_code, 200)
        today_accepted_apps = response.context['today_accepted_apps']
        today_processed_stats = response.context['today_processed_stats']
        today = response.context['today']

        self.assertEqual(len(today_accepted_apps), 1)
        self.assertEqual(today_processed_stats['processed'], 1)
        self.assertEqual(today_processed_stats['not_processed'], 0)
        self.assertEqual(today.strftime('%Y-%m-%d'), datetime.date.today().strftime('%Y-%m-%d'))

        self.delete_document(STUDENT, STUDENT_ID, ['sin', 'study_permit'], 'international')


        # 2nd student
        self.login(STUDENT2, PASSWORD)

        JOB2 = 'apbi-260-001-agroecology-i-introduction-to-principles-and-techniques-w1'
        SLUG2 = '2019-w1-apbi-260-001-agroecology-i-introduction-to-principles-and-techniques-w1-application-by-user66test'
        #app = adminApi.get_application(APP_SLUG, 'slug')

        self.submit_profile_resume(STUDENT2)
        self.submit_confiential_information_international_complete(STUDENT2)

        response = self.client.get( reverse('students:reaccept_application', args=[SLUG2]) + '?next=/app/students/jobs/history/' )
        self.assertEqual(response.status_code, 200)
        app2 = response.context['app']

        self.assertEqual(app2.job.session.slug, SESSION)
        self.assertEqual(app2.job.course.slug, JOB2)
        self.assertTrue(app2.is_declined_reassigned)

        new_hours = 70.5
        data3 = {
            'application': app2.id,
            'assigned_hours': new_hours,
            'decision': 'accept',
            'has_contract_read': 'true',
            'next': reverse('students:history_jobs') + '?page=2'
        }
        response = self.client.post( reverse('students:reaccept_application', args=[SLUG2]) + HISTORY_NEXT, data=urlencode(data3), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:history_jobs') + '?page=2')
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:history_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, STUDENT2)
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        apps2 = response.context['apps']
        self.assertEqual( len(apps2), 5 )

        appl2 = None
        for a in apps2:
            if a.id == app2.id: appl2 = a

        self.assertEqual(appl2.job.session.slug, SESSION)
        self.assertEqual(appl2.job.course.slug, JOB2)
        self.assertEqual(appl2.accepted.get_assigned_display(), 'Accepted')
        self.assertTrue(appl2.accepted.has_contract_read)
        self.assertEqual(appl2.accepted.assigned_hours, new_hours)
        self.assertEqual(appl2.job.assigned_ta_hours, app2.job.assigned_ta_hours)

        diff = new_hours - app2.accepted.assigned_hours
        self.assertEqual(appl2.job.accumulated_ta_hours, app2.job.accumulated_ta_hours + diff)

        total_hours = adminApi.get_total_assigned_hours(apps2, ['accepted'])
        self.assertEqual(total_hours['accepted'], {'2019-W1': 45.0 + diff, '2019-W2': 30.0})

        self.login(USERS[0], PASSWORD)

        response = self.client.get(reverse('administrators:accepted_applications'))
        self.assertEqual(response.status_code, 200)
        today_accepted_apps = response.context['today_accepted_apps']
        today_processed_stats = response.context['today_processed_stats']
        today = response.context['today']

        self.assertEqual(len(today_accepted_apps), 2)
        self.assertEqual(today_processed_stats['processed'], 1)
        self.assertEqual(today_processed_stats['not_processed'], 1)
        self.assertEqual(today.strftime('%Y-%m-%d'), datetime.date.today().strftime('%Y-%m-%d'))

        # enter processed
        data4 = {
            'application': app2.id,
            'pin': '1237',
            'tasm': True,
            'processed': 'Done',
            'worktag': 'adsf1111',
            'processing_note': 'this is a processing note'
        }
        response = self.client.post(reverse('administrators:update_admin_docs'), data=urlencode(data4), content_type=ContentType)
        messages = self.json_messages(response)
        self.assertTrue('success', messages['status'])
        self.assertTrue('Success' in messages['message'])
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('administrators:accepted_applications'))
        self.assertEqual(response.status_code, 200)
        today_accepted_apps = response.context['today_accepted_apps']
        today_processed_stats = response.context['today_processed_stats']
        today = response.context['today']

        self.assertEqual(len(today_accepted_apps), 2)
        self.assertEqual(today_processed_stats['processed'], 2)
        self.assertEqual(today_processed_stats['not_processed'], 0)
        self.assertEqual(today.strftime('%Y-%m-%d'), datetime.date.today().strftime('%Y-%m-%d'))

        self.delete_document(STUDENT2, STUDENT2_ID, ['resume', 'sin', 'study_permit'], 'international')


    @tag('')
    def test_cannot_accept_offer(self):
        print('- Test: Students cannot accept a job offer')
        self.login(STUDENT, PASSWORD)

        self.submit_confiential_information_international_incomplete(STUDENT)

        response = self.client.get( reverse('students:accept_decline_job', args=[SESSION, STUDENT_JOB]) + HISTORY_NEXT )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, STUDENT)
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        app = response.context['app']
        self.assertEqual(app.job.course.slug, STUDENT_JOB)
        self.assertEqual(app.applicant.username, STUDENT)

        data1 = {
            'application': app.id,
            'assigned_hours': app.offered.assigned_hours,
            'decision': 'accept',
            'has_contract_read': 'true',
            'next': reverse('students:history_jobs') + '?page=2'
        }
        response = self.client.post( reverse('students:make_decision', args=[SESSION, STUDENT_JOB]), data=urlencode(data1), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred. Please check the following information, and update required documents. <ul><li>Date of Birth</li><li>Study Permit Expiry Date</li></ul>' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:accept_decline_job', args=[SESSION, STUDENT_JOB]) + HISTORY_NEXT)
        self.assertRedirects(response, response.url)

        self.delete_document(STUDENT, STUDENT_ID, ['sin', 'study_permit'], 'international')


    @tag('')
    def test_decline_offer(self):
        print('- Test: Students decline job offers')
        self.login(STUDENT, PASSWORD)

        self.submit_confiential_information_international_complete(STUDENT)

        response = self.client.get( reverse('students:accept_decline_job', args=[SESSION, STUDENT_JOB]) + HISTORY_NEXT )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, STUDENT)
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        app = response.context['app']
        self.assertEqual(app.job.session.slug, SESSION)
        self.assertEqual(app.job.course.slug, STUDENT_JOB)
        self.assertEqual(app.applicant.username, STUDENT)

        data1 = {
            'application': app.id,
            'assigned_hours': app.offered.assigned_hours,
            'has_contract_read': 'true',
            'next': reverse('students:history_jobs') + '?page=2'
        }
        response = self.client.post( reverse('students:make_decision', args=[SESSION, STUDENT_JOB]), data=urlencode(data1), content_type=ContentType )
        messages = self.messages(response)
        self.assertEqual(messages[0], 'An error occurred. Please choose "Accept" or "Decline".')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:accept_decline_job', args=[SESSION, STUDENT_JOB]) + HISTORY_NEXT)
        self.assertRedirects(response, response.url)

        data2 = {
            'application': app.id,
            'assigned_hours': app.offered.assigned_hours,
            'decision': 'decline',
            'next': reverse('students:history_jobs') + '?page=2'
        }
        response = self.client.post( reverse('students:make_decision', args=[SESSION, STUDENT_JOB]), data=urlencode(data2), content_type=ContentType )
        messages = self.messages(response)
        self.assertEqual(messages[0], 'An error occurred. Please read and understand a Job Offer Contract.')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:accept_decline_job', args=[SESSION, STUDENT_JOB]) + HISTORY_NEXT)
        self.assertRedirects(response, response.url)

        data3 = {
            'application': app.id,
            'assigned_hours': app.offered.assigned_hours,
            'decision': 'decline',
            'has_contract_read': 'true',
            'next': reverse('students:history_jobs') + '?page=2'
        }
        response = self.client.post( reverse('students:make_decision', args=[SESSION, STUDENT_JOB]), data=urlencode(data3), content_type=ContentType )
        messages = self.messages(response)
        self.assertEqual(messages[0], 'You declined the job offer - 2019 W1: APBI 265 001.')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:history_jobs') + '?page=2')
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:history_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, STUDENT)
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        apps = response.context['apps']
        self.assertEqual( len(apps), 3 )

        appl = None
        for a in apps:
            if a.id == app.id: appl = a

        self.assertEqual(appl.job.session.slug, SESSION)
        self.assertEqual(appl.job.course.slug, STUDENT_JOB)
        self.assertEqual(appl.declined.get_assigned_display(), 'Declined')
        self.assertTrue(appl.declined.has_contract_read)
        self.assertEqual(appl.declined.assigned_hours, 0.0)

        self.assertEqual(appl.job.assigned_ta_hours, app.job.assigned_ta_hours)
        self.assertEqual(appl.job.accumulated_ta_hours, app.job.accumulated_ta_hours + appl.declined.assigned_hours)

        total_hours = adminApi.get_total_assigned_hours(apps, ['accepted'])
        self.assertEqual(total_hours['accepted'], {})

        self.delete_document(STUDENT, STUDENT_ID, ['sin', 'study_permit'], 'international')


    @tag('')
    def test_decline_offer_with_incomplete_confidentiality(self):
        print('- Test: Students decline job offers with incomplete confidentiality')
        self.login(STUDENT, PASSWORD)

        self.submit_confiential_information_international_incomplete(STUDENT)

        response = self.client.get( reverse('students:accept_decline_job', args=[SESSION, STUDENT_JOB]) + HISTORY_NEXT )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, STUDENT)
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        app = response.context['app']
        self.assertEqual(app.job.session.slug, SESSION)
        self.assertEqual(app.job.course.slug, STUDENT_JOB)
        self.assertEqual(app.applicant.username, STUDENT)

        data1 = {
            'application': app.id,
            'assigned_hours': app.offered.assigned_hours,
            'decision': 'decline',
            'has_contract_read': 'true',
            'next': reverse('students:history_jobs') + '?page=2'
        }
        response = self.client.post( reverse('students:make_decision', args=[SESSION, STUDENT_JOB]), data=urlencode(data1), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('You declined the job offer - 2019 W1: APBI 265 001' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:history_jobs') + '?page=2')
        self.assertRedirects(response, response.url)

        self.delete_document(STUDENT, STUDENT_ID, ['sin', 'study_permit'], 'international')


    @tag('')
    def test_reaccept_application_not_ready(self):
        print('- Test: Students re-accept new job offers - not ready')

        STUDENT = 'user65.test'
        self.login(STUDENT, PASSWORD)

        self.submit_confiential_information_international_complete(STUDENT)

        APP_SLUG = SESSION + '-' + STUDENT_JOB + '-application-by-' + 'user65test'
        app = adminApi.get_application(APP_SLUG, 'slug')
        self.assertFalse(app.is_declined_reassigned)

        self.delete_document(STUDENT, STUDENT_ID, ['sin', 'study_permit'], 'international')


    @tag('')
    def test_reaccept_application_success(self):
        print('- Test: Students re-accept new job offers - success')

        self.login(STUDENT2, PASSWORD)

        response = self.client.get( reverse('students:index') )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:show_profile') + NEXT + HOME_BASIC)
        self.assertRedirects(response, response.url)

        self.submit_profile_resume(STUDENT2)
        self.submit_confiential_information_international_complete(STUDENT2)

        response = self.client.get( reverse('students:index') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_assigned_hours']['accepted'], {'2019-W1': 45.0, '2019-W2': 30.0})

        JOB = 'apbi-260-001-agroecology-i-introduction-to-principles-and-techniques-w1'
        SLUG = '2019-w1-apbi-260-001-agroecology-i-introduction-to-principles-and-techniques-w1-application-by-user66test'

        response = self.client.get( reverse('students:reaccept_application', args=[SLUG]) + HISTORY_WRONG_1 )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:reaccept_application', args=[SLUG]) + HISTORY_WRONG_1 )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:reaccept_application', args=[SLUG]) + HISTORY_WRONG_1 )
        self.assertEqual(response.status_code, 404)

        appl = adminApi.get_application(SLUG, 'slug')
        appl.job.session.is_archived = True
        appl.job.session.save(update_fields=['is_archived'])

        response = self.client.get( reverse('students:reaccept_application', args=[SLUG]) + HISTORY_NEXT )
        self.assertEqual(response.status_code, 403)

        appl.job.session.is_archived = False
        appl.job.session.save(update_fields=['is_archived'])

        response = self.client.get( reverse('students:reaccept_application', args=[SLUG]) + HISTORY_NEXT )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context['loggedin_user'].username, STUDENT2)
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        app = response.context['app']
        self.assertEqual(app.job.session.slug, SESSION)
        self.assertEqual(app.job.course.slug, JOB)
        self.assertTrue(app.is_declined_reassigned)

        new_hours = 70.5

        data1 = {
            'application': app.id,
            'assigned_hours': new_hours,
            'has_contract_read': 'true',
            'next': reverse('students:history_jobs') + '?page=2'
        }
        response = self.client.post( reverse('students:reaccept_application', args=[SLUG]) + HISTORY_NEXT, data=urlencode(data1), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:reaccept_application', args=[SLUG]) + HISTORY_NEXT)
        self.assertRedirects(response, response.url)

        data2 = {
            'application': app.id,
            'assigned_hours': new_hours,
            'decision': 'accept',
            'next': reverse('students:history_jobs') + '?page=2'
        }
        response = self.client.post( reverse('students:reaccept_application', args=[SLUG]) + HISTORY_NEXT, data=urlencode(data2), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:reaccept_application', args=[SLUG]) + HISTORY_NEXT)
        self.assertRedirects(response, response.url)

        data3 = {
            'application': app.id,
            'assigned_hours': new_hours,
            'decision': 'accept',
            'has_contract_read': 'true',
            'next': '/app/students/jobs/historY/?page=2'
        }
        response = self.client.post( reverse('students:reaccept_application', args=[SLUG]) + HISTORY_NEXT, data=urlencode(data3), content_type=ContentType )
        self.assertEqual(response.status_code, 404)

        data4 = {
            'application': app.id,
            'assigned_hours': new_hours,
            'decision': 'accept',
            'has_contract_read': 'true',
            'next': reverse('students:history_jobs') + '?page=2'
        }
        response = self.client.post( reverse('students:reaccept_application', args=[SLUG]) + HISTORY_NEXT, data=urlencode(data4), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:history_jobs') + '?page=2')
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:history_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, STUDENT2)
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        apps = response.context['apps']
        self.assertEqual( len(apps), 5 )

        appl = None
        for a in apps:
            if a.id == app.id: appl = a

        self.assertEqual(appl.job.session.slug, SESSION)
        self.assertEqual(appl.job.course.slug, JOB)
        self.assertEqual(appl.accepted.get_assigned_display(), 'Accepted')
        self.assertTrue(appl.accepted.has_contract_read)
        self.assertEqual(appl.accepted.assigned_hours, new_hours)
        self.assertEqual(appl.job.assigned_ta_hours, app.job.assigned_ta_hours)

        diff = new_hours - app.accepted.assigned_hours
        self.assertEqual(appl.job.accumulated_ta_hours, app.job.accumulated_ta_hours + diff)

        total_hours = adminApi.get_total_assigned_hours(apps, ['accepted'])
        self.assertEqual(total_hours['accepted'], {'2019-W1': 45.0 + diff, '2019-W2': 30.0})

        self.delete_document(STUDENT2, STUDENT2_ID, ['resume', 'sin', 'study_permit'], 'international')


    @tag('')
    def test_reaccept_application_with_incomplete_confidentiality_not_ready(self):
        print('- Test: Students cannot re-accept new job offers - not ready')

        self.login(STUDENT, PASSWORD)

        self.submit_confiential_information_international_complete(STUDENT)

        APP_SLUG = SESSION + '-' + STUDENT_JOB + '-application-by-' + 'user65test'
        app = adminApi.get_application(APP_SLUG, 'slug')
        self.assertFalse(app.is_declined_reassigned)

        self.delete_document(STUDENT, STUDENT_ID, ['sin', 'study_permit'], 'international')


    @tag('')
    def test_reaccept_application_with_incomplete_confidentiality_success(self):
        print('- Test: Students cannot re-accept new job offers - success')

        self.login(STUDENT2, PASSWORD)

        response = self.client.get( reverse('students:index') )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:show_profile') + NEXT + HOME_BASIC)
        self.assertRedirects(response, response.url)

        self.submit_profile_resume(STUDENT2)
        self.submit_confiential_information_international_incomplete(STUDENT2)

        SLUG = '2019-w1-apbi-260-001-agroecology-i-introduction-to-principles-and-techniques-w1-application-by-user66test'
        app = adminApi.get_application(SLUG, 'slug')
        data1 = {
            'application': app.id,
            'assigned_hours': 70.5,
            'decision': 'accept',
            'has_contract_read': 'true',
            'next': reverse('students:history_jobs') + '?page=2'
        }
        response = self.client.post( reverse('students:reaccept_application', args=[SLUG]) + HISTORY_NEXT, data=urlencode(data1), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred. Please check the following information, and update required documents. <ul><li>Date of Birth</li><li>Study Permit Expiry Date</li></ul>' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:reaccept_application', args=[SLUG]) + HISTORY_NEXT)
        self.assertRedirects(response, response.url)

        self.delete_document(STUDENT2, STUDENT2_ID, ['resume', 'sin', 'study_permit'], 'international')


    @tag('')
    def test_redecline_application_not_ready(self):
        print('- Test: Students re-decline new job offers - not ready')

        self.login(STUDENT, PASSWORD)

        self.submit_confiential_information_international_complete(STUDENT)

        APP_SLUG = SESSION + '-' + STUDENT_JOB + '-application-by-' + 'user65test'
        app = adminApi.get_application(APP_SLUG, 'slug')
        self.assertFalse(app.is_declined_reassigned)

        self.delete_document(STUDENT, STUDENT_ID, ['sin', 'study_permit'], 'international')


    @tag('')
    def test_redecline_application_success(self):
        print('- Test: Students re-decline new job offers - success')

        self.login(STUDENT2, PASSWORD)

        self.submit_confiential_information_international_complete(STUDENT2)

        response = self.client.get( reverse('students:index') )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:show_profile') + NEXT + HOME_BASIC)
        self.assertRedirects(response, response.url)

        self.submit_profile_resume(STUDENT2)

        response = self.client.get( reverse('students:index') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_assigned_hours']['accepted'], {'2019-W1': 45.0, '2019-W2': 30.0})

        JOB = 'apbi-260-001-agroecology-i-introduction-to-principles-and-techniques-w1'
        SLUG = '2019-w1-apbi-260-001-agroecology-i-introduction-to-principles-and-techniques-w1-application-by-user66test'

        response = self.client.get( reverse('students:reaccept_application', args=[SLUG]) + HISTORY_WRONG_1 )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:reaccept_application', args=[SLUG]) + HISTORY_WRONG_1 )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:reaccept_application', args=[SLUG]) + HISTORY_WRONG_1 )
        self.assertEqual(response.status_code, 404)


        response = self.client.get( reverse('students:reaccept_application', args=[SLUG]) + HISTORY_NEXT )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context['loggedin_user'].username, STUDENT2)
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        app = response.context['app']
        self.assertEqual(app.job.session.slug, SESSION)
        self.assertEqual(app.job.course.slug, JOB)
        self.assertTrue(app.is_declined_reassigned)

        data1 = {
            'application': app.id,
            'assigned_hours': 35.5,
            'has_contract_read': 'true',
            'next': reverse('students:history_jobs') + '?page=2'
        }
        response = self.client.post( reverse('students:reaccept_application', args=[SLUG]) + HISTORY_NEXT, data=urlencode(data1), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:reaccept_application', args=[SLUG]) + HISTORY_NEXT)
        self.assertRedirects(response, response.url)

        data2 = {
            'application': app.id,
            'assigned_hours': 35.5,
            'decision': 'decline',
            'next': reverse('students:history_jobs') + '?page=2'
        }
        response = self.client.post( reverse('students:reaccept_application', args=[SLUG]) + HISTORY_NEXT, data=urlencode(data2), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:reaccept_application', args=[SLUG]) + HISTORY_NEXT)
        self.assertRedirects(response, response.url)

        data3 = {
            'application': app.id,
            'assigned_hours': 35.5,
            'decision': 'decline',
            'has_contract_read': 'true',
            'next': reverse('students:history_jobs') + '?page=2'
        }
        response = self.client.post( reverse('students:reaccept_application', args=[SLUG]) + HISTORY_NEXT, data=urlencode(data3), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('You declined the job offer - 2019 W1: APBI 260 001' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:history_jobs') + '?page=2')
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:history_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, STUDENT2)
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        apps = response.context['apps']
        self.assertEqual( len(apps), 5 )

        appl = None
        for a in apps:
            if a.id == app.id: appl = a

        self.assertEqual(appl.job.session.slug, SESSION)
        self.assertEqual(appl.job.course.slug, JOB)
        self.assertEqual(appl.declined.get_assigned_display(), 'Declined')
        self.assertTrue(appl.declined.has_contract_read)
        self.assertEqual(appl.declined.assigned_hours, 0.0)

        self.assertEqual(appl.job.assigned_ta_hours, app.job.assigned_ta_hours)
        self.assertEqual(appl.job.accumulated_ta_hours, app.job.accumulated_ta_hours - 45.0) # accepted hours was 45.0

        self.delete_document(STUDENT2, STUDENT2_ID, ['resume', 'sin', 'study_permit'], 'international')


    @tag('')
    def test_redecline_application_with_incomplete_confidentiality(self):
        print('- Test: Students re-decline new job offers with incomplete confidentiality')

        self.login(STUDENT2, PASSWORD)

        self.submit_profile_resume(STUDENT2)
        self.submit_confiential_information_international_incomplete(STUDENT2)

        JOB = 'apbi-260-001-agroecology-i-introduction-to-principles-and-techniques-w1'
        SLUG = '2019-w1-apbi-260-001-agroecology-i-introduction-to-principles-and-techniques-w1-application-by-user66test'

        response = self.client.get( reverse('students:reaccept_application', args=[SLUG]) + HISTORY_NEXT )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context['loggedin_user'].username, STUDENT2)
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        app = response.context['app']
        self.assertEqual(app.job.session.slug, SESSION)
        self.assertEqual(app.job.course.slug, JOB)
        self.assertTrue(app.is_declined_reassigned)

        data1 = {
            'application': app.id,
            'assigned_hours': 35.5,
            'decision': 'decline',
            'has_contract_read': 'true',
            'next': reverse('students:history_jobs') + '?page=2'
        }
        response = self.client.post( reverse('students:reaccept_application', args=[SLUG]) + HISTORY_NEXT, data=urlencode(data1), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('You declined the job offer - 2019 W1: APBI 260 001' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:history_jobs') + '?page=2')
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:history_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, STUDENT2)
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        apps = response.context['apps']
        self.assertEqual( len(apps), 5 )

        appl = None
        for a in apps:
            if a.id == app.id: appl = a

        self.assertEqual(appl.job.session.slug, SESSION)
        self.assertEqual(appl.job.course.slug, JOB)
        self.assertEqual(appl.declined.get_assigned_display(), 'Declined')
        self.assertTrue(appl.declined.has_contract_read)
        self.assertEqual(appl.declined.assigned_hours, 0.0)

        self.assertEqual(appl.job.assigned_ta_hours, app.job.assigned_ta_hours)
        self.assertEqual(appl.job.accumulated_ta_hours, app.job.accumulated_ta_hours - 45.0) # accepted hours was 45.0

        self.delete_document(STUDENT2, STUDENT2_ID, ['resume', 'sin', 'study_permit'], 'international')


    @tag('')
    def test_terminate_job(self):
        print('- Test: A student terminates a job contract')
        self.login()

        response = self.client.get( reverse('students:terminate_job', args=[SESSION, 'apbi-200-001-introduction-to-soil-science-w1']) )
        self.assertEqual(response.status_code, 404)

        STUDENT_JOB = 'apbi-260-001-agroecology-i-introduction-to-principles-and-techniques-w1'

        response = self.client.get( reverse('students:terminate_job', args=[SESSION, STUDENT_JOB]) + HISTORY_WRONG_1 )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:terminate_job', args=[SESSION, STUDENT_JOB]) + HISTORY_WRONG_2 )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:terminate_job', args=[SESSION, STUDENT_JOB]) + HISTORY_WRONG_3 )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('students:terminate_job', args=[SESSION, STUDENT_JOB]) + HISTORY_NEXT )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        app = response.context['app']
        self.assertEqual(app.id, 22)
        self.assertTrue(app.is_terminated)

        data1 = {
            'application': app.id,
            'assigned_hours': app.accepted.assigned_hours,
            'assigned': utils.CANCELLED,
            'parent_id': app.accepted.id,
            'next': '/app/students/jobs/History/?page=2'
        }
        response = self.client.post( reverse('students:terminate_job', args=[SESSION, STUDENT_JOB]) + HISTORY_NEXT, data=urlencode(data1), content_type=ContentType )
        self.assertEqual(response.status_code, 404)

        data2 = {
            'application': app.id,
            'assigned_hours': app.accepted.assigned_hours,
            'assigned': utils.CANCELLED,
            'parent_id': app.accepted.id,
            'next': reverse('students:history_jobs') + '?page=2'
        }
        response = self.client.post( reverse('students:terminate_job', args=[SESSION, STUDENT_JOB]) + HISTORY_NEXT, data=urlencode(data2), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Application of 2019 W1 - APBI 260 001 terminated.' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:history_jobs') + '?page=2')
        self.assertRedirects(response, response.url)

        job = adminApi.get_job_by_session_slug_job_slug(SESSION, STUDENT_JOB)
        self.assertEqual(job.assigned_ta_hours, app.job.assigned_ta_hours)
        self.assertEqual(job.accumulated_ta_hours, app.job.accumulated_ta_hours - app.accepted.assigned_hours)


    @tag('')
    def test_show_job(self):
        print('- Test: display a job')
        self.login()

        response = self.client.get( reverse('students:show_job', args=[SESSION, JOB]) + HISTORY_WRONG_1 + '&p=History%20of%20Jobs')
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:show_job', args=[SESSION, JOB]) + HISTORY_WRONG_2 + '&p=History%20of%20Jobs')
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:show_job', args=[SESSION, JOB]) + HISTORY_WRONG_3 + '&p=History%20of%20Jobs')
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('students:show_job', args=[SESSION, JOB]) + HISTORY_NEXT + '&a=History%20of%20Jobs')
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:show_job', args=[SESSION, JOB]) + HISTORY_NEXT + '&p=History%20of%20jobs')
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('students:show_job', args=[SESSION, JOB]) + HISTORY_NEXT + '&p=History%20of%20Jobs')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        job = response.context['job']
        self.assertEqual(job.session.year, '2019')
        self.assertEqual(job.session.term.code, 'W1')
        self.assertEqual(job.session.slug, SESSION)
        self.assertEqual(job.course.slug, JOB)


    @tag('')
    def test_show_application(self):
        print('- Test: Display an application details')
        self.login()

        response = self.client.get( reverse('students:show_application', args=[APP]) + HISTORY_WRONG_1)
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:show_application', args=[APP]) + HISTORY_WRONG_2)
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('students:show_application', args=[APP]) + HISTORY_WRONG_3)
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('students:show_application', args=[APP]) + HISTORY_NEXT )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual(response.context['app'].slug, APP)

        app = adminApi.get_application(response.context['app'].slug, 'slug')
        self.assertEqual(response.context['app'].id, app.id)
        self.assertEqual(response.context['app'].applicant.username, app.applicant.username)
