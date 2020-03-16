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


STUDENT = 'user65.test'
STUDENT_JOB = 'apbi-265-001-sustainable-agriculture-and-food-systems-w1'


class StudentTest(TestCase):
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

    def submit_profile_resume(self, username):
        ''' Submit profile and resume '''
        data = {
            'preferred_name': 'preferred name',
            'qualifications': 'qualifications',
            'prior_employment': 'prior employment',
            'special_considerations': 'special considerations',
            'status': '3',
            'program': '5',
            'program_others': 'program others',
            'graduation_date': '2020-05-20',
            'degrees': ['2', '5'],
            'degree_details': 'degree details',
            'trainings': ['2', '3'],
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
        self.assertEqual(response.url, '/students/profile/information/basic/')
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:show_profile', args=['basic']) )
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
        resume_name = 'resume.pdf'
        data = {
            'user': user.id,
            'resume': SimpleUploadedFile('resume.pdf', b'file_content', content_type='application/pdf')
        }
        response = self.client.post( reverse('students:upload_resume'), data=data, format='multipart')
        messages = self.messages(response)

        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/students/profile/information/resume/')
        self.assertRedirects(response, response.url)

        resume = userApi.has_user_resume_created(user)
        self.assertIsNotNone(resume)


    def submit_profile_resume_undergraduate(self, username):
        ''' Submit profile and resume '''
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
            'trainings': ['2', '3'],
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
        self.assertEqual(response.url, '/students/profile/information/basic/')
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:show_profile', args=['basic']) )
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
        resume_name = 'resume.pdf'
        data = {
            'user': user.id,
            'resume': SimpleUploadedFile('resume.pdf', b'file_content', content_type='application/pdf')
        }
        response = self.client.post( reverse('students:upload_resume'), data=data, format='multipart')
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/students/profile/information/resume/')
        self.assertRedirects(response, response.url)

        resume = userApi.has_user_resume_created(user)
        self.assertIsNotNone(resume)


    def test_view_url_exists_at_desired_location(self):
        print('\n- Test: view url exists at desired location')
        self.login()

        response = self.client.get( reverse('students:index') )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/students/profile/information/basic/')
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:available_jobs', args=[SESSION]) )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('students:apply_job', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 403)

        self.submit_profile_resume(USERS[2])

        response = self.client.get( reverse('students:index') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:show_profile', args=['basic']) )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:edit_profile') )
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

        response = self.client.get(reverse('students:cancel_job', args=[SESSION, 'apbi-260-001-agroecology-i-introduction-to-principles-and-techniques-w1']))
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:apply_job', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:accept_decline_job', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:show_job', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:show_application', args=[APP]) )
        self.assertEqual(response.status_code, 200)

    def test_show_profile(self):
        print('\n- Test: Display all lists of session terms')
        self.login()

        response = self.client.get( reverse('students:show_profile', args=['basic']) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username,  USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertFalse(response.context['form'].is_bound)

    def test_edit_profile(self):
        print('\n- Test: Edit user profile')
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
        }

        response = self.client.post( reverse('students:edit_profile'), data=urlencode(data1, True), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred. Anticipated Graduation Date: This field is required.' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/students/profile/edit/')
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
            'qualifications': 'qualifications'
        }

        response = self.client.post( reverse('students:edit_profile'), data=urlencode(data2, True), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred. Please indicate your program if you select "Others" in the Current Program.' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/students/profile/edit/')
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
            'qualifications': 'qualifications'
        }

        response = self.client.post( reverse('students:edit_profile'), data=urlencode(data3, True), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred. Please indicate your program if you select "Others" in the Current Program. Anticipated Graduation Date: This field is required.' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/students/profile/edit/')
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
            'ta_experience_details': 'Ta experience details'
        }

        response = self.client.post( reverse('students:edit_profile'), data=urlencode(data4, True), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred. Form is invalid. QUALIFICATIONS: This field is required.' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/students/profile/edit/')
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
            'special_considerations': 'special_considerations'
        }

        response = self.client.post( reverse('students:edit_profile'), data=urlencode(data, True), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/students/profile/information/basic/')
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:show_profile', args=['basic']) )
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


    def test_upload_user_resume(self):
        print('\n- Test: upload user resume')
        self.login()
        user = userApi.get_user(USERS[2], 'username')

        self.assertIsNone(userApi.has_user_resume_created(user))
        resume_name = 'resume.pdf'
        data = {
            'user': user.id,
            'resume': SimpleUploadedFile('resume.pdf', b'file_content', content_type='application/pdf')
        }
        response = self.client.post( reverse('students:upload_resume'), data=data, format='multipart')
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/students/profile/information/resume/')
        self.assertRedirects(response, response.url)

        resume = userApi.has_user_resume_created(userApi.get_user(USERS[2], 'username'))
        self.assertIsNotNone(resume)

        response = self.client.get(reverse('students:show_profile', args=['basic']))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertIsNotNone(response.context['loggedin_user'].resume)


    def test_delete_user_resume(self):
        print('\n- Test: delete user resume')
        self.login()
        user = userApi.get_user(USERS[2], 'username')

        data = {
            'user': user.id,
            'resume': SimpleUploadedFile('resume.pdf', b'file_content', content_type='application/pdf')
        }
        response = self.client.post( reverse('students:upload_resume'), data=data, format='multipart' )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        resume = userApi.has_user_resume_created(userApi.get_user(USERS[2], 'username'))
        self.assertIsNotNone(resume)

        response = self.client.get(reverse('students:show_profile', args=['basic']))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertIsNotNone(response.context['user'].resume)

        response = self.client.post( reverse('students:delete_resume'), data=urlencode({ 'user': USERS[2] }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/students/profile/information/resume/')
        self.assertRedirects(response, response.url)

        #response = self.client.get( reverse('students:show_profile') )
        #self.assertEqual(response.status_code, 200)
        #self.assertEqual(response.context['loggedin_user'].username,  USERS[2])
        #resume = userApi.has_user_resume_created(userApi.get_user(USERS[2], 'username'))
        #self.assertIsNone(resume)


    def test_show_confidentiality(self):
        print('\n- Test: Display user confidentiality')
        self.login()

        response = self.client.get( reverse('students:show_confidentiality') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])


    def test_check_submit_confidentiality(self):
        print('\n- Test: Check and submit confidential information ')
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
            'nationality': data['nationality'],
            'employee_number': '1234567',
            #'sin': SimpleUploadedFile('sin.png', b'\x00\x01\x02\x03', content_type='image/png'),
            'sin_expiry_date': '2020-01-01',
            #'study_permit': SimpleUploadedFile('study_permit.png', b'\x00\x01\x02\x03', content_type='image/png'),
            'study_permit_expiry_date': '2020-05-05'
        }

        response = self.client.post( reverse('students:submit_confidentiality'), data=data, format='multipart' )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:show_confidentiality') )
        self.assertEqual(response.status_code, 200)
        loggedin_user = response.context['loggedin_user']
        self.assertEqual(loggedin_user.confidentiality.nationality, data['nationality'])
        self.assertEqual(loggedin_user.confidentiality.employee_number, data['employee_number'])
        self.assertEqual(loggedin_user.confidentiality.sin_expiry_date, datetime.date(2020, 1, 1))
        self.assertEqual(loggedin_user.confidentiality.study_permit_expiry_date, datetime.date(2020, 5, 5))

    def test_edit_confidentiality(self):
        print('\n- Test: Edit confidentional information')
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
            'employee_number': '1234567',
            'sin_expiry_date': '2020-01-01',
            'study_permit_expiry_date': '2020-05-05'
        }
        response = self.client.post( reverse('students:submit_confidentiality'), data=data, format='multipart' )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        data = {
            'user': user.id,
            'nationality': '1',
            'employee_number': '1234568',
            'sin_expiry_date': '2020-01-11',
            'study_permit_expiry_date': '2020-05-22'
        }
        response = self.client.post( reverse('students:edit_confidentiality'), data=data, format='multipart' )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:show_confidentiality') )
        self.assertEqual(response.status_code, 200)
        loggedin_user = response.context['loggedin_user']
        self.assertEqual(loggedin_user.confidentiality.nationality, data['nationality'])
        self.assertEqual(loggedin_user.confidentiality.employee_number, data['employee_number'])
        self.assertEqual(loggedin_user.confidentiality.sin_expiry_date, datetime.date(2020, 1, 11))
        self.assertEqual(loggedin_user.confidentiality.study_permit_expiry_date, datetime.date(2020, 5, 22))

        data = {
            'user': user.id,
            'nationality': '0',
        }
        response = self.client.post( reverse('students:edit_confidentiality'), data=data, format='multipart' )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:show_confidentiality') )
        self.assertEqual(response.status_code, 200)
        loggedin_user = response.context['loggedin_user']
        self.assertEqual(loggedin_user.confidentiality.nationality, data['nationality'])


    def test_explore_jobs(self):
        print('\n- Test: Display all lists of session terms')
        self.login()

        response = self.client.get( reverse('students:explore_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        self.assertEqual( len(response.context['visible_current_sessions']), 3 )
        self.assertEqual( len(response.context['favourites']), 3 )

    def test_favrouite_jobs(self):
        print('\n- Test: Display all lists of favourite jobs')
        self.login()

        response = self.client.get( reverse('students:favourite_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        self.assertEqual( len(response.context['favourites']), 3 )

    def test_select_favourite_job(self):
        print('\n- Test: Select favourite job')
        self.login()

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) )
        self.assertEqual(response.status_code, 403)

        self.submit_profile_resume(USERS[2])

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) )
        self.assertEqual(response.status_code, 200)

        data = {
            'applicant': response.context['loggedin_user'].id,
            'job': 109,
            'is_selected': True
        }
        response = self.client.post( reverse('students:select_favourite_job', args=[SESSION, STUDENT_JOB]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/students/sessions/{0}/jobs/{1}/apply/'.format(SESSION, STUDENT_JOB))
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:favourite_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        self.assertEqual( len(response.context['favourites']), 4 )


    def test_available_jobs(self):
        print('\n- Test: Display jobs available to apply')
        self.login()

        response = self.client.get( reverse('students:available_jobs', args=[SESSION]) )
        self.assertEqual(response.status_code, 403)

        self.submit_profile_resume(USERS[2])

        response = self.client.get( reverse('students:available_jobs', args=[SESSION]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual( len(response.context['jobs']), 50 )


    def test_apply_job_undergraduate(self):
        print('\n- Test: Undergraduate students can apply for each job')
        self.login()

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) )
        self.assertEqual(response.status_code, 403)

        self.submit_profile_resume_undergraduate(USERS[2])

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) )
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
            'availability_note': 'nothing'
        }

        response = self.client.post( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/students/sessions/{0}/jobs/available/'.format(SESSION))
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual(response.context['job'].course.slug, STUDENT_JOB)
        self.assertTrue(response.context['has_applied_job'])
        self.assertFalse(response.context['form'].is_bound)

    def test_apply_job_no_supervisor_approval(self):
        print('\n- Test: Graudate students cannot apply for each job without supervisor approval')
        self.login()

        self.submit_profile_resume(USERS[2])

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) )
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
            'availability_note': 'nothing'
        }

        response = self.client.post( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred. You need your "Supervisor Approval" to submit the form if you are not an Undergraduate student.' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/students/sessions/{0}/jobs/{1}/apply/'.format(SESSION, STUDENT_JOB))
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual(response.context['job'].course.slug, STUDENT_JOB)
        self.assertFalse(response.context['has_applied_job'])
        self.assertFalse(response.context['form'].is_bound)

    def test_apply_job(self):
        print('\n- Test: Graudate students can apply for each job')
        self.login()

        self.submit_profile_resume(USERS[2])

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual(response.context['job'].course.slug, STUDENT_JOB)
        self.assertFalse(response.context['has_applied_job'])
        self.assertFalse(response.context['form'].is_bound)

        data = {
            'applicant': response.context['loggedin_user'].id,
            'job': response.context['job'].id,
            'supervisor_approval': True,
            'how_qualified': '4',
            'how_interested': '3',
            'availability': True,
            'availability_note': 'nothing'
        }

        response = self.client.post( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/students/sessions/{0}/jobs/available/'.format(SESSION))
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual(response.context['job'].course.slug, STUDENT_JOB)
        self.assertTrue(response.context['has_applied_job'])
        self.assertFalse(response.context['form'].is_bound)

    def test_cannot_apply_jobs(self):
        print('\n- Test: Students cannot apply for each job')

        # not student role
        self.login(USERS[0], PASSWORD)
        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) )
        self.assertEqual(response.status_code, 403)

        self.login(USERS[1], PASSWORD)
        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) )
        self.assertEqual(response.status_code, 403)

        self.login()

        # didn't complete profile and resume
        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) )
        self.assertEqual(response.status_code, 403)

        self.submit_profile_resume(USERS[2])

        session = adminApi.get_session(SESSION, 'slug')
        session.is_visible = False
        session.is_archived = True
        session.save(update_fields=['is_visible', 'is_archived'])

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) )
        self.assertEqual(response.status_code, 403)

        session = adminApi.get_session(SESSION, 'slug')
        session.is_visible = True
        session.is_archived = True
        session.save(update_fields=['is_visible', 'is_archived'])

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) )
        self.assertEqual(response.status_code, 403)

        job = adminApi.get_job_by_session_slug_job_slug(SESSION, STUDENT_JOB)
        job.is_active = False
        job.save(update_fields=['is_active'])

        response = self.client.get( reverse('students:apply_job', args=[SESSION, STUDENT_JOB]) )
        self.assertEqual(response.status_code, 403)

    def test_history_jobs(self):
        print('\n- Test: Display History of Jobs applied by a student')
        self.login()

        response = self.client.get( reverse('students:history_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual( len(response.context['apps']), 7 )

    def test_accept_decline_job(self):
        print('\n- Test: Display a job to select accept or decline a job offer')
        self.login(STUDENT, '12')

        response = self.client.get( reverse('students:accept_decline_job', args=[SESSION, STUDENT_JOB]) )
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


    def test_accept_offer(self):
        print('\n- Test: Students accept a job offer')
        self.login(STUDENT, '12')

        response = self.client.get( reverse('students:accept_decline_job', args=[SESSION, STUDENT_JOB]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, STUDENT)
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        app = response.context['app']
        self.assertEqual(app.job.course.slug, STUDENT_JOB)
        self.assertEqual(app.applicant.username, STUDENT)

        data = {
            'application': app.id,
            'assigned_hours': app.offered.assigned_hours
        }

        response = self.client.post( reverse('students:accept_offer', args=[SESSION, STUDENT_JOB]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
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
        self.assertEqual(appl.accepted.get_assigned_display(), 'Accepted')
        self.assertEqual(appl.accepted.assigned_hours, data['assigned_hours'])
        self.assertEqual(appl.job.assigned_ta_hours, app.job.assigned_ta_hours)
        self.assertEqual(appl.job.accumulated_ta_hours, app.job.accumulated_ta_hours + appl.accepted.assigned_hours)

        total_hours = adminApi.get_total_assigned_hours(apps, ['accepted'])
        self.assertEqual(total_hours['accepted'], {'2019-W1': appl.accepted.assigned_hours})


    def test_decline_offer(self):
        print('\n- Test: Students decline job offers')
        self.login(STUDENT, '12')

        response = self.client.get( reverse('students:accept_decline_job', args=[SESSION, STUDENT_JOB]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, STUDENT)
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        app = response.context['app']
        self.assertEqual(app.job.session.slug, SESSION)
        self.assertEqual(app.job.course.slug, STUDENT_JOB)
        self.assertEqual(app.applicant.username, STUDENT)

        data = {
            'application': app.id,
            'assigned_hours': app.offered.assigned_hours
        }

        response = self.client.post( reverse('students:decline_offer', args=[SESSION, STUDENT_JOB]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('You declined the job offer - 2019 W1: APBI 265 001' in messages[0])
        self.assertEqual(response.status_code, 302)
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
        self.assertEqual(appl.declined.assigned_hours, 0.0)

        self.assertEqual(appl.job.assigned_ta_hours, app.job.assigned_ta_hours)
        self.assertEqual(appl.job.accumulated_ta_hours, app.job.accumulated_ta_hours + appl.declined.assigned_hours)

        total_hours = adminApi.get_total_assigned_hours(apps, ['accepted'])
        self.assertEqual(total_hours['accepted'], {})


    def test_reaccept_application(self):
        print('\n- Test: Students re-accept new job offers')

        STUDENT = 'user65.test'
        self.login(STUDENT, '12')

        APP_SLUG = SESSION + '-' + STUDENT_JOB + '-application-by-' + 'user65test'
        app = adminApi.get_application(APP_SLUG, 'slug')
        self.assertFalse(app.is_declined_reassigned)

        STUDENT = 'user66.test'
        self.login(STUDENT, '12')

        response = self.client.get( reverse('students:index') )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/students/profile/information/basic/')
        self.assertRedirects(response, response.url)

        self.submit_profile_resume(STUDENT)

        response = self.client.get( reverse('students:index') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_assigned_hours']['accepted'], {'2019-W1': 45.5, '2019-W2': 30.0})

        JOB = 'apbi-260-001-agroecology-i-introduction-to-principles-and-techniques-w1'
        SLUG = '2019-w1-apbi-260-001-agroecology-i-introduction-to-principles-and-techniques-w1-application-by-user66test'
        response = self.client.get( reverse('students:reaccept_application', args=[SLUG]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, STUDENT)
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        app = response.context['app']
        self.assertEqual(app.job.session.slug, SESSION)
        self.assertEqual(app.job.course.slug, JOB)
        self.assertTrue(app.is_declined_reassigned)

        new_hours = 70.5
        data = {
            'application': app.id,
            'assigned_hours': new_hours
        }

        response = self.client.post( reverse('students:reaccept_application', args=[SLUG]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:history_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, STUDENT)
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        apps = response.context['apps']
        self.assertEqual( len(apps), 5 )

        appl = None
        for a in apps:
            if a.id == app.id: appl = a

        self.assertEqual(appl.job.session.slug, SESSION)
        self.assertEqual(appl.job.course.slug, JOB)
        self.assertEqual(appl.accepted.get_assigned_display(), 'Accepted')
        self.assertEqual(appl.accepted.assigned_hours, new_hours)
        self.assertEqual(appl.job.assigned_ta_hours, app.job.assigned_ta_hours)

        diff = new_hours - app.accepted.assigned_hours
        self.assertEqual(appl.job.accumulated_ta_hours, app.job.accumulated_ta_hours + diff)

        total_hours = adminApi.get_total_assigned_hours(apps, ['accepted'])
        self.assertEqual(total_hours['accepted'], {'2019-W1': 45.5 + diff, '2019-W2': 30.0})


    def test_cancel_job(self):
        print('\n- Test: A student terminates a job contract')
        self.login()

        response = self.client.get( reverse('students:cancel_job', args=[SESSION, 'apbi-200-001-introduction-to-soil-science-w1']) )
        self.assertEqual(response.status_code, 404)

        STUDENT_JOB = 'apbi-260-001-agroecology-i-introduction-to-principles-and-techniques-w1'
        response = self.client.get( reverse('students:cancel_job', args=[SESSION, STUDENT_JOB]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        app = response.context['app']
        self.assertEqual(app.id, 22)
        self.assertTrue(app.is_terminated)

        data = {
            'application': app.id,
            'assigned_hours': app.accepted.assigned_hours,
            'assigned': ApplicationStatus.CANCELLED,
            'parent_id': app.accepted.id
        }

        response = self.client.post( reverse('students:cancel_job', args=[SESSION, STUDENT_JOB]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Application of 2019 W1 - APBI 260 001 terminated.' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/students/jobs/history/')
        self.assertRedirects(response, response.url)

        job = adminApi.get_job_by_session_slug_job_slug(SESSION, STUDENT_JOB)
        self.assertEqual(job.assigned_ta_hours, app.job.assigned_ta_hours)
        self.assertEqual(job.accumulated_ta_hours, app.job.accumulated_ta_hours - app.accepted.assigned_hours)


    def test_show_job(self):
        print('\n- Test: display a job')
        self.login()

        response = self.client.get( reverse('students:show_job', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        job = response.context['job']
        self.assertEqual(job.session.year, '2019')
        self.assertEqual(job.session.term.code, 'W1')
        self.assertEqual(job.session.slug, SESSION)
        self.assertEqual(job.course.slug, JOB)


    def test_show_application(self):
        print('\n- Test: Display an application details')
        self.login()

        response = self.client.get( reverse('students:show_application', args=[APP]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[2])
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual(response.context['app'].slug, APP)

        app = adminApi.get_application(response.context['app'].slug, 'slug')
        self.assertEqual(response.context['app'].id, app.id)
        self.assertEqual(response.context['app'].applicant.username, app.applicant.username)
