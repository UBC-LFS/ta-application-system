from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from urllib.parse import urlencode

from users.models import *
from users import api
from department.tests.test_views import DATA, ContentType

from django.utils.crypto import get_random_string


class UserTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        print('\nUser testing has started ==>')

    def login(self, username, password):
        self.client.post('/accounts/local_login/', data={'username': username, 'password': password})

    def test_view_url_exists_at_desired_location(self):
        """ Test: land department and users pages """

        # Without login
        response = self.client.get('/department/')
        self.assertEqual(response.status_code, 302) # Redirect to /accounts/login
        self.assertRedirects(response, response.url)
        response = self.client.get('/users/')
        self.assertEqual(response.status_code, 302) # Redirect to /accounts/login
        self.assertRedirects(response, response.url)

         # Login with student
        self.login('test.user11', '12')
        response = self.client.get('/department/')
        self.assertEqual(response.status_code, 403) # Permission denied
        response = self.client.get('/users/')
        self.assertEqual(response.status_code, 403) # Permission denied

         # Login with admin
        self.login('admin', '12')
        response = self.client.get('/department/')
        self.assertEqual(response.status_code, 200) # Success
        response = self.client.get('/users/')
        self.assertEqual(response.status_code, 200) # Success


    def test_logged_in_uses_correct_template(self):
        """ Test: land a home index page """
        self.login('admin', '12')
        response = self.client.get(reverse('home:index'))
        self.assertEqual(response.status_code, 200) # check a home page
        self.assertEqual(response.context['loggedin_user']['username'], 'admin') # check a username

    def test_get_users(self):
        """ Test: get all users """
        self.login('admin', '12')
        response = self.client.get(reverse('users:index'))
        self.assertEqual(len(response.context['users']), 30) # 30 users

    def test_create_user_in_view(self):
        """ Test: create a user """
        self.login('admin', '12')
        data = {
            'first_name': 'test',
            'last_name': 'user100',
            'email': 'test.user100@example.com',
            'username': 'test.user100',
            'password': '12'
        }

        self.assertFalse(api.username_exists(data['username'])) # Check username
        self.assertFalse(api.profile_exists_by_username(data['username'])) # Check user's profile
        self.assertFalse(api.resume_exists_by_username(data['username'])) # Check user's resume
        self.assertFalse(api.confidentiality_exists_by_username(data['username'])) # Check user's confidentiality

        response = self.client.post('/users/', data=urlencode(data), content_type=ContentType)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue('Success' in messages[0]) # Check a success message
        self.assertEqual(response.status_code, 302) # Redirect to users index
        user = api.get_user_by_username('test.user100')
        self.assertEqual(user.username, 'test.user100') # Equals to the new user
        self.assertTrue(api.profile_exists_by_username(user.username)) # Check user's profile
        self.assertTrue(api.resume_exists_by_username(user.username)) # Check user's resume
        self.assertTrue(api.confidentiality_exists_by_username(user.username)) # Check user's confidentiality

    def test_create_user_via_api(self):
        """ Test: create a user via api when the function added in SAML """

        # Check an existing user
        data = {
            'first_name': 'test5',
            'last_name': 'user5',
            'email': 'test.user5@example.com',
            'username': 'test.user5',
            'password': '12'
        }
        exists = api.username_exists(data['username'])
        self.assertTrue(exists) # username exists

        data = {
            'first_name': 'test',
            'last_name': 'user55',
            'email': 'test.user55@example.com',
            'username': 'test.user55',
            'password': '12'
        }

        self.assertFalse(api.username_exists(data['username'])) # Check username
        self.assertFalse(api.profile_exists_by_username(data['username'])) # Check user's profile
        self.assertFalse(api.resume_exists_by_username(data['username'])) # Check user's resume
        self.assertFalse(api.confidentiality_exists_by_username(data['username'])) # Check user's confidentiality

        user = api.create_user(data)
        self.assertEqual(user.username, 'test.user55')
        self.assertTrue(api.profile_exists_by_username(user.username)) # Check user's profile
        self.assertTrue(api.resume_exists_by_username(user.username)) # Check user's resume
        self.assertTrue(api.confidentiality_exists_by_username(user.username)) # Check user's confidentiality


    def test_create_existing_user(self):
        """ Test: check an existing user when creating a user """
        self.login('admin', '12')

        # Try data with the existing username
        data = {
            'first_name': 'test',
            'last_name': 'user5',
            'email': 'test.user1@example.com',
            'username': 'test.user5',
            'password': '12'
        }
        response = self.client.post('/users/', data=urlencode(data), content_type=ContentType)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue( 'Error' in messages[0] ) # Check a error message


    def test_delete_user(self):
        """ Test: delete a user """
        self.login('admin', '12')

        user_id = '25'
        username = 'test.user25'
        data = { 'user': user_id }
        response = self.client.post(reverse('users:delete_user'), data=urlencode(data), content_type=ContentType)

        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue('Success' in messages[0]) # Check a success message
        self.assertEqual(response.status_code, 302) # Redirect to users index

        user = api.get_user(user_id)
        self.assertEqual(user, None)
        self.assertFalse(api.username_exists(username)) # Check the delted username
        self.assertFalse(api.profile_exists_by_username(username)) # Check user's profile
        self.assertFalse(api.resume_exists_by_username(username)) # Check user's resume
        self.assertFalse(api.confidentiality_exists_by_username(username)) # Check user's confidentiality

    def test_edit_profile(self):
        """ Test: edit user's profile """
        self.login('admin', '12')
        data = {
            'user': '20',
            'roles': '3',
            'qualifications': 'qualification text',
            'prior_employment': 'prior employment text',
            'special_considerations': 'special considerations text',
            'status': '3',
            'program': '4',
            'graduation_date': '2020-05-25',
            'degrees': ['4', '7'],
            'trainings': ['2', '4'],
            'lfs_ta_training': '1',
            'lfs_ta_training_details': 'lfs ta training details text',
            'ta_experience': '1',
            'ta_experience_details': 'ta experience details text'
        }
        response = self.client.post(reverse('users:edit_profile', args=['test.user20']), data=urlencode(data, True), content_type=ContentType)

        self.assertEqual(response.status_code, 302) # Redirect to user details
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue('Success' in messages[0]) # Check a success message

        # Check user's profile
        user = api.get_user('20')
        self.assertEquals(user.id, 20)
        self.assertEquals( [role.name for role in user.profile.roles.all()] , ['HR'])
        self.assertEquals(user.profile.qualifications, 'qualification text')
        self.assertEquals(user.profile.prior_employment, 'prior employment text')
        self.assertEquals(user.profile.special_considerations, 'special considerations text')
        self.assertEquals(user.profile.status.name, 'Ph.D student')
        self.assertEquals(user.profile.program.name, 'Doctor of Philosophy in Food Science (PhD)')
        self.assertEquals(user.profile.graduation_date.year, 2020)
        self.assertEquals(user.profile.graduation_date.month, 5)
        self.assertEquals(user.profile.graduation_date.day, 25)
        self.assertEquals([degree.name for degree in user.profile.degrees.all()], ['Master of Arts', 'Doctor of Arts'])
        self.assertEquals([training.name for training in user.profile.trainings.all()], ['Instructional Skills Workshops for Grad Students', 'An Educational Leadership Mapping (ELM) tool for teaching and educational leadership'])
        self.assertEquals(user.profile.get_lfs_ta_training_display(), 'Yes')
        self.assertEquals(user.profile.lfs_ta_training_details, 'lfs ta training details text')
        self.assertEquals(user.profile.get_ta_experience_display(), 'Yes')
        self.assertEquals(user.profile.ta_experience_details, 'ta experience details text')

    def test_edit_confidentiality(self):
        """ Test: edit user's confidentiality """
        self.login('admin', '12')
        data = {
            'user': '20',
            'sin': '123456789',
            'employee_number': '0012345',
            'visa': '1',
            'work_permit': True
        }
        response = self.client.post(reverse('users:edit_confidentiality', args=['test.user20']), data=urlencode(data), content_type=ContentType)

        self.assertEqual(response.status_code, 302) # Redirect to user details
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue('Success' in messages[0]) # Check a success message

        user = api.get_user('20')
        self.assertEquals(user.id, 20)
        self.assertEquals(user.confidentiality.sin, '123456789')
        self.assertEquals(user.confidentiality.employee_number, '0012345')
        self.assertEquals(user.confidentiality.get_visa_display(), 'Type 1')
        self.assertEquals(user.confidentiality.work_permit, True)


class StudentProfileTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        print('\nStudentProfile testing has started ==>')

    def login(self, username, password):
        self.client.post('/accounts/local_login/', data={'username': username, 'password': password})

    def test_sessions_view_url_exists_at_desired_location(self):
        """ Test: land student profile pages"""

        # login with a student
        username = 'test.user11'
        self.login(username, '12')
        response = self.client.get( reverse('users:show_student', args=[username]) )
        self.assertEqual(response.status_code, 200) # success

        # login with an instructor
        username = 'test.user5'
        self.login(username, '12')
        response = self.client.get( reverse('users:show_student', args=[username]) )
        self.assertEqual(response.status_code, 403) # permission denied


    def test_show_student(self):
        """ Test: display student's details """

        user_id = '15'
        user = api.get_user(user_id)
        self.login(user.username, '12')
        response = self.client.get( reverse('users:show_student', args=[user.username]) )
        self.assertEqual(response.status_code, 200)

        loggedin_user = response.context['loggedin_user']
        res_user = response.context['user']
        resume_name = response.context['resume_name']
        student_jobs = response.context['student_jobs']
        offered_jobs = response.context['offered_jobs']
        accepted_jobs = response.context['accepted_jobs']
        declined_jobs = response.context['declined_jobs']
        self.assertEqual(loggedin_user['username'], user.username)
        self.assertEqual(res_user.id, int(user_id))
        self.assertEqual(resume_name, '')
        self.assertEqual( len(student_jobs), 0 )
        self.assertEqual( len(offered_jobs), 0 )
        self.assertEqual( len(accepted_jobs), 0 )
        self.assertEqual( len(declined_jobs), 0 )


    def test_edit_student_profile(self):
        """ Test: edit student's profile """
        user_id = '15'
        user = api.get_user(user_id)
        self.login(user.username, '12')

        data = {
            'qualifications': 'updated qualifications',
            'prior_employment': 'updated prior_employment', 
            'special_considerations': 'updated special_considerations',
            'status': '5', 
            'program': '7', 
            'graduation_date': '2020-05-25', 
            'degrees': ['4', '6'], 
            'trainings': ['2', '3'],
            'lfs_ta_training': '1', 
            'lfs_ta_training_details': 'updated lfs_ta_training_details', 
            'ta_experience': '2',
            'ta_experience_details': 'updated ta_experience_details'
        }

        response = self.client.post( reverse('users:edit_student', args=[user.username]), data=urlencode(data, True), content_type=ContentType )
        self.assertEqual(response.status_code, 302) # redirect to the student details page
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue('Success' in messages[0]) # Check a success message

        response = self.client.get( reverse('users:show_student', args=[user.username]) )
        user = response.context['user']
        
        self.assertEqual(user.profile.qualifications, data['qualifications'])
        self.assertEqual(user.profile.prior_employment, data['prior_employment'])
        self.assertEqual(user.profile.special_considerations, data['special_considerations'])
        self.assertEqual(user.profile.status.id, int(data['status']))
        self.assertEqual(user.profile.program.id, int(data['program']))
        self.assertEqual(user.profile.graduation_date.strftime('%Y-%m-%d'), data['graduation_date'])
        self.assertEqual( [str(degree.id) for degree in user.profile.degrees.all()], data['degrees'] )
        self.assertEqual( [str(training.id) for training in user.profile.trainings.all()], data['trainings'] )
        self.assertEqual(user.profile.lfs_ta_training, data['lfs_ta_training'])
        self.assertEqual(user.profile.lfs_ta_training_details, data['lfs_ta_training_details'])
        self.assertEqual(user.profile.ta_experience, data['ta_experience'])
        self.assertEqual(user.profile.ta_experience_details, data['ta_experience_details'])



class InstructorProfileTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        print('\nInstructorProfile testing has started ==>')

    def login(self, username, password):
        self.client.post('/accounts/local_login/', data={'username': username, 'password': password})

    def test_sessions_view_url_exists_at_desired_location(self):
        """ Test: land student profile pages"""


        # login with an instructor
        username = 'test.user5'
        self.login(username, '12')
        response = self.client.get( reverse('users:show_instructor', args=[username]) )
        self.assertEqual(response.status_code, 200) # success

        # login with a student
        username = 'test.user11'
        self.login(username, '12')
        response = self.client.get( reverse('users:show_instructor', args=[username]) )
        self.assertEqual(response.status_code, 403) # permission denied


    def test_show_instructor(self):
        """ Test: display instructor's details """

        user_id = '5'
        user = api.get_user(user_id)
        self.login(user.username, '12')
        response = self.client.get( reverse('users:show_instructor', args=[user.username]) )
        self.assertEqual(response.status_code, 200)

        loggedin_user = response.context['loggedin_user']
        res_user = response.context['user']
        jobs = res_user.job_set.all()
        
        self.assertEqual(loggedin_user['username'], user.username)
        self.assertEqual(res_user.id, int(user_id))
        self.assertEqual( len(jobs), 1 )

    def test_edit_instructor_profile(self):
        """ Test: edit instructor's profile """
        user_id = '5'
        user = api.get_user(user_id)
        self.login(user.username, '12')

        data = {
            'status': '8', 
            'program': '4'
        }
        response = self.client.post( reverse('users:edit_instructor', args=[user.username]), data=urlencode(data), content_type=ContentType )
        self.assertEqual(response.status_code, 302) # redirect to the instructor details page
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue('Success' in messages[0]) # Check a success message

        response = self.client.get( reverse('users:show_instructor', args=[user.username]) )
        user = response.context['user']
        
        self.assertEqual(user.profile.status.id, int(data['status']))
        self.assertEqual(user.profile.program.id, int(data['program']))