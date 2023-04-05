from django.test import TestCase

from users import api as userApi

from administrators.tests.test_sessions import LOGIN_URL, ContentType, DATA, USERS, SESSION, JOB, APP, COURSE, PASSWORD


class LoginTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        print('\nLogin testing has started ==>')
        cls.user = userApi.get_user('sample.user', 'username')
        cls.user2 = userApi.get_user('sample2.user', 'username')
        
    def test_login_success_created_user_1(self):
        print('- Test: login success with a created user - no student number and no employee number')

        self.assertIsNotNone(self.user)
        self.assertIsNone(userApi.has_user_profile_created(self.user))
        self.assertIsNone(userApi.has_user_confidentiality_created(self.user))

        data = {
            'first_name': 'Sample',
            'last_name': 'User',
            'email': 'sample.user@example.com',
            'username': 'sample.user',
            'employee_number': None,
            'student_number': None
        }

        user = userApi.user_exists(data)
        self.assertIsNotNone(userApi.has_user_profile_created(user))
        self.assertIsNone(userApi.has_user_confidentiality_created(user))
        
        self.assertEqual(user.first_name, data['first_name'])
        self.assertEqual(user.last_name, data['last_name'])
        self.assertEqual(user.email, data['email'])
        self.assertEqual(user.username, data['username'])
        self.assertEqual(user.profile.student_number, None)
        self.assertEqual([role.name for role in user.profile.roles.all()], ['Student'])
    

    def test_login_success_created_user_2(self):
        print('- Test: login success with a created user - yes student number and no employee number')

        self.assertIsNotNone(self.user)
        self.assertIsNone(userApi.has_user_profile_created(self.user))
        self.assertIsNone(userApi.has_user_confidentiality_created(self.user))

        data = {
            'first_name': 'Sample',
            'last_name': 'User',
            'email': 'sample.user@example.com',
            'username': 'sample.user',
            'employee_number': None,
            'student_number': '99999999'
        }

        user = userApi.user_exists(data)
        self.assertIsNotNone(userApi.has_user_profile_created(user))
        self.assertIsNone(userApi.has_user_confidentiality_created(user))
        
        self.assertEqual(user.first_name, data['first_name'])
        self.assertEqual(user.last_name, data['last_name'])
        self.assertEqual(user.email, data['email'])
        self.assertEqual(user.username, data['username'])
        self.assertEqual(user.profile.student_number, '99999999')
        self.assertEqual([role.name for role in user.profile.roles.all()], ['Student'])
        

    def test_login_success_created_user_3(self):
        print('- Test: login success with a created user - no student number and yes employee number')

        self.assertIsNotNone(self.user)
        self.assertIsNone(userApi.has_user_profile_created(self.user))
        self.assertIsNone(userApi.has_user_confidentiality_created(self.user))

        data = {
            'first_name': 'Sample',
            'last_name': 'User',
            'email': 'sample.user@example.com',
            'username': 'sample.user',
            'employee_number': '9999999',
            'student_number': None
        }

        user = userApi.user_exists(data)
        self.assertIsNotNone(userApi.has_user_profile_created(user))
        self.assertIsNotNone(userApi.has_user_confidentiality_created(user))
        
        self.assertEqual(user.first_name, data['first_name'])
        self.assertEqual(user.last_name, data['last_name'])
        self.assertEqual(user.email, data['email'])
        self.assertEqual(user.username, data['username'])
        self.assertEqual(user.confidentiality.employee_number, '9999999')
        self.assertEqual(user.profile.student_number, None)
        self.assertEqual([role.name for role in user.profile.roles.all()], ['Student'])


    def test_login_success_created_user_4(self):
        print('- Test: login success with a created user - change student number and employee number')
        
        self.assertIsNotNone(self.user)
        self.assertIsNone(userApi.has_user_profile_created(self.user))
        self.assertIsNone(userApi.has_user_confidentiality_created(self.user))

        data = {
            'first_name': 'Sample',
            'last_name': 'User',
            'email': 'sample.user@example.com',
            'username': 'sample.user',
            'employee_number': None,
            'student_number': None
        }

        user = userApi.user_exists(data)
        self.assertIsNotNone(userApi.has_user_profile_created(user))
        self.assertIsNone(userApi.has_user_confidentiality_created(user))
        
        self.assertEqual(user.first_name, data['first_name'])
        self.assertEqual(user.last_name, data['last_name'])
        self.assertEqual(user.email, data['email'])
        self.assertEqual(user.username, data['username'])
        self.assertEqual(user.profile.student_number, None)
        self.assertEqual([role.name for role in user.profile.roles.all()], ['Student'])

        data2 = {
            'first_name': 'Sample',
            'last_name': 'User',
            'email': 'sample.user@example.com',
            'username': 'sample.user',
            'employee_number': '9999999',
            'student_number': '88888888'
        }
        user2 = userApi.user_exists(data2)
        self.assertIsNotNone(userApi.has_user_profile_created(user2))
        self.assertIsNotNone(userApi.has_user_confidentiality_created(user2))
        
        self.assertEqual(user2.first_name, data2['first_name'])
        self.assertEqual(user2.last_name, data2['last_name'])
        self.assertEqual(user2.email, data2['email'])
        self.assertEqual(user2.username, data2['username'])
        self.assertEqual(user2.confidentiality.employee_number, '9999999')
        self.assertEqual(user2.profile.student_number, '88888888')
        self.assertEqual([role.name for role in user2.profile.roles.all()], ['Student'])


    def test_login_with_two_empty_employee_numbers(self):
        print('- Test: login with two empty employee numbers')

        # User 1
        self.assertIsNotNone(self.user)
        self.assertIsNone(userApi.has_user_profile_created(self.user))
        self.assertIsNone(userApi.has_user_confidentiality_created(self.user))

        data = {
            'first_name': 'Sample',
            'last_name': 'User',
            'email': 'sample.user@example.com',
            'username': 'sample.user',
            'employee_number': None,
            'student_number': '99999999'
        }

        user = userApi.user_exists(data)
        
        self.assertIsNotNone(userApi.has_user_profile_created(user))
        self.assertIsNone(userApi.has_user_confidentiality_created(user))
        
        self.assertEqual(user.first_name, data['first_name'])
        self.assertEqual(user.last_name, data['last_name'])
        self.assertEqual(user.email, data['email'])
        self.assertEqual(user.username, data['username'])
        self.assertEqual(user.profile.student_number, '99999999')
        self.assertEqual([role.name for role in user.profile.roles.all()], ['Student'])

        # User 2
        self.assertIsNotNone(self.user2)
        self.assertIsNone(userApi.has_user_profile_created(self.user2))
        self.assertIsNone(userApi.has_user_confidentiality_created(self.user2))

        data2 = {
            'first_name': 'Sample2',
            'last_name': 'User',
            'email': 'sample2.user@example.com',
            'username': 'sample2.user',
            'employee_number': None,
            'student_number': None
        }

        user3 = userApi.user_exists(data2)
        self.assertIsNotNone(userApi.has_user_profile_created(user3))
        self.assertIsNone(userApi.has_user_confidentiality_created(user3))
        
        self.assertEqual(user3.first_name, data2['first_name'])
        self.assertEqual(user3.last_name, data2['last_name'])
        self.assertEqual(user3.email, data2['email'])
        self.assertEqual(user3.username, data2['username'])
        self.assertEqual(user3.profile.student_number, None)
        self.assertEqual([role.name for role in user3.profile.roles.all()], ['Student'])


    def test_login_with_two_empty_student_numbers(self):
        print('- Test: login with two empty student numbers')

        # User 1
        self.assertIsNotNone(self.user)
        self.assertIsNone(userApi.has_user_profile_created(self.user))
        self.assertIsNone(userApi.has_user_confidentiality_created(self.user))

        data = {
            'first_name': 'Sample',
            'last_name': 'User',
            'email': 'sample.user@example.com',
            'username': 'sample.user',
            'employee_number': '8888888',
            'student_number': None
        }

        user = userApi.user_exists(data)
        self.assertIsNotNone(userApi.has_user_profile_created(user))
        self.assertIsNotNone(userApi.has_user_confidentiality_created(user))
        
        self.assertEqual(user.first_name, data['first_name'])
        self.assertEqual(user.last_name, data['last_name'])
        self.assertEqual(user.email, data['email'])
        self.assertEqual(user.username, data['username'])
        self.assertEqual(user.confidentiality.employee_number, '8888888')
        self.assertEqual(user.profile.student_number, None)
        self.assertEqual([role.name for role in user.profile.roles.all()], ['Student'])

        # User 2
        self.assertIsNotNone(self.user2)
        self.assertIsNone(userApi.has_user_profile_created(self.user2))
        self.assertIsNone(userApi.has_user_confidentiality_created(self.user2))

        data2 = {
            'first_name': 'Sample2',
            'last_name': 'User',
            'email': 'sample2.user@example.com',
            'username': 'sample2.user',
            'employee_number': None,
            'student_number': None
        }

        user3 = userApi.user_exists(data2)
        self.assertIsNotNone(userApi.has_user_profile_created(user3))
        self.assertIsNone(userApi.has_user_confidentiality_created(user3))
        
        self.assertEqual(user3.first_name, data2['first_name'])
        self.assertEqual(user3.last_name, data2['last_name'])
        self.assertEqual(user3.email, data2['email'])
        self.assertEqual(user3.username, data2['username'])
        self.assertEqual(user3.profile.student_number, None)
        self.assertEqual([role.name for role in user3.profile.roles.all()], ['Student'])