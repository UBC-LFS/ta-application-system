from django.test import TestCase

from users import api as userApi

from administrators.tests.test_views import LOGIN_URL, ContentType, DATA, USERS, SESSION, JOB, APP, COURSE, PASSWORD


class LoginTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        print('\nLogin testing has started ==>')

    def saml_authenticate(self, saml_auth):
        ''' test saml authenticate function '''
        if not saml_auth:
            return None

        if saml_auth['auth']:
            user_data = saml_auth['attrs']

            if user_data['username'] == None:
                return 'SuspiciousOperation'

            if userApi.contain_user_duplicated_info(user_data) == True:
                return 'SuspiciousOperation'

            user = userApi.user_exists(user_data)
            if user == None:
                user = userApi.create_user(user_data)
            return user

        return None

    def test_login_success_user_exists(self):
        print('- Test: login success - user exists')

        # Create a new user
        created_user = userApi.create_user({
            'first_name': 'User600',
            'last_name': 'Test',
            'email': 'user600.test@email.com',
            'username': 'user600.test',
            'student_number': None,
            'employee_number': None
        })
        self.assertIsNotNone( userApi.has_user_profile_created(created_user) )
        self.assertIsNotNone( userApi.has_user_confidentiality_created(created_user) )

        # login - no student number and no employee number
        saml_data = {
            'auth': True,
            'attrs': {
                'first_name': created_user.first_name,
                'last_name': created_user.last_name,
                'email': created_user.email,
                'username': created_user.username,
                'student_number': None,
                'employee_number': None
            }
        }
        user = self.saml_authenticate(saml_data)
        self.assertIsNotNone(user)
        self.assertEqual(user.username, saml_data['attrs']['username'])
        self.assertEqual(user.email, saml_data['attrs']['email'])
        self.assertEqual(user.first_name, saml_data['attrs']['first_name'])
        self.assertEqual(user.last_name, saml_data['attrs']['last_name'])
        self.assertIsNotNone(user.profile)
        self.assertIsNone(user.profile.student_number)
        roles = userApi.get_user_roles(user)
        self.assertEqual(roles, ['Student'])
        self.assertIsNotNone(user.confidentiality)
        self.assertIsNone(user.confidentiality.employee_number)
        self.assertTrue(user.confidentiality.is_new_employee)

        # login - yes student number and no employee number
        self.assertIsNotNone(created_user)
        saml_data2 = {
            'auth': True,
            'attrs': {
                'first_name': created_user.first_name,
                'last_name': created_user.last_name,
                'email': created_user.email,
                'username': created_user.username,
                'student_number': '58684563',
                'employee_number': None
            }
        }
        user2 = self.saml_authenticate(saml_data2)
        self.assertIsNotNone(user2)
        self.assertEqual(user2.username, saml_data2['attrs']['username'])
        self.assertEqual(user2.email, saml_data2['attrs']['email'])
        self.assertEqual(user2.first_name, saml_data2['attrs']['first_name'])
        self.assertEqual(user2.last_name, saml_data2['attrs']['last_name'])
        self.assertIsNotNone(user2.profile)
        self.assertEqual(user2.profile.student_number,  saml_data2['attrs']['student_number'])
        roles2 = userApi.get_user_roles(user2)
        self.assertEqual(roles2, ['Student'])
        self.assertIsNotNone(user2.confidentiality)
        self.assertIsNone(user2.confidentiality.employee_number)
        self.assertTrue(user2.confidentiality.is_new_employee)

        # login - yes student number and yes employee number
        saml_data3 = {
            'auth': True,
            'attrs': {
                'first_name': created_user.first_name,
                'last_name': created_user.last_name,
                'email': created_user.email,
                'username': created_user.username,
                'student_number': '58684563',
                'employee_number': '8456345'
            }
        }
        user3 = self.saml_authenticate(saml_data3)
        self.assertIsNotNone(user3)
        self.assertEqual(user3.username, saml_data3['attrs']['username'])
        self.assertEqual(user3.email, saml_data3['attrs']['email'])
        self.assertEqual(user3.first_name, saml_data3['attrs']['first_name'])
        self.assertEqual(user3.last_name, saml_data3['attrs']['last_name'])
        self.assertIsNotNone(user3.profile)
        self.assertEqual(user3.profile.student_number, saml_data3['attrs']['student_number'])
        roles3 = userApi.get_user_roles(user3)
        self.assertEqual(roles3, ['Student'])
        self.assertIsNotNone(user3.confidentiality)
        self.assertEqual(user3.confidentiality.employee_number, saml_data3['attrs']['employee_number'])
        self.assertFalse(user3.confidentiality.is_new_employee)

        # login - Change student number and employee number
        saml_data4 = {
            'auth': True,
            'attrs': {
                'first_name': created_user.first_name,
                'last_name': created_user.last_name,
                'email': created_user.email,
                'username': created_user.username,
                'student_number': '58684500',
                'employee_number': '8456300'
            }
        }
        user4 = self.saml_authenticate(saml_data4)
        self.assertIsNotNone(user4)
        self.assertEqual(user4.username, saml_data4['attrs']['username'])
        self.assertEqual(user4.email, saml_data4['attrs']['email'])
        self.assertEqual(user4.first_name, saml_data4['attrs']['first_name'])
        self.assertEqual(user4.last_name, saml_data4['attrs']['last_name'])
        self.assertIsNotNone(user4.profile)
        self.assertEqual(user4.profile.student_number, saml_data4['attrs']['student_number'])
        roles4 = userApi.get_user_roles(user4)
        self.assertEqual(roles4, ['Student'])
        self.assertIsNotNone(user4.confidentiality)
        self.assertEqual(user4.confidentiality.employee_number, saml_data4['attrs']['employee_number'])
        self.assertFalse(user4.confidentiality.is_new_employee)

    def test_login_user_not_exists(self):
        print('- Test: login - an user does not exist')

        # login
        saml_data = {
            'auth': True,
            'attrs': {
                'first_name': 'User700',
                'last_name': 'Test',
                'email': 'user700.test@email.com',
                'username': 'user700.test',
                'student_number': None,
                'employee_number': None
            }
        }
        user = self.saml_authenticate(saml_data)
        self.assertIsNotNone(user)
        self.assertEqual(user.username, saml_data['attrs']['username'])
        self.assertEqual(user.email, saml_data['attrs']['email'])
        self.assertEqual(user.first_name, saml_data['attrs']['first_name'])
        self.assertEqual(user.last_name, saml_data['attrs']['last_name'])
        self.assertIsNotNone(user.profile)
        self.assertIsNone(user.profile.student_number)
        roles = userApi.get_user_roles(user)
        self.assertEqual(roles, ['Student'])
        self.assertIsNotNone(user.confidentiality)
        self.assertIsNone(user.confidentiality.employee_number)
        self.assertTrue(user.confidentiality.is_new_employee)

        saml_data2 = {
            'auth': True,
            'attrs': {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'username': user.username,
                'student_number': None,
                'employee_number': '6997879'
            }
        }
        user2 = self.saml_authenticate(saml_data2)
        self.assertIsNotNone(user2)
        self.assertEqual(user2.username, saml_data2['attrs']['username'])
        self.assertEqual(user2.email, saml_data2['attrs']['email'])
        self.assertEqual(user2.first_name, saml_data2['attrs']['first_name'])
        self.assertEqual(user2.last_name, saml_data2['attrs']['last_name'])
        self.assertIsNotNone(user2.profile)
        self.assertIsNone(user2.profile.student_number)
        roles2 = userApi.get_user_roles(user2)
        self.assertEqual(roles2, ['Student'])
        self.assertIsNotNone(user2.confidentiality)
        self.assertEqual(user2.confidentiality.employee_number, saml_data2['attrs']['employee_number'])
        self.assertFalse(user2.confidentiality.is_new_employee)


    def test_login_failure_missing_username(self):
        print('- Test: login failure - missing username')

        saml_data = {
            'auth': True,
            'attrs': {
                'first_name': 'Test',
                'last_name': 'User600',
                'email': 'test.user600@example.com',
                'username': None,
                'student_number': None,
                'employee_number': None
            }
        }
        user = self.saml_authenticate(saml_data)
        self.assertEqual(user, 'SuspiciousOperation')

    def test_login_duplicated_student_number(self):
        print('- Test: login - duplicated student number')

        # login - success
        saml_data = {
            'auth': True,
            'attrs': {
                'first_name': 'Test',
                'last_name': 'User600',
                'email': 'test.user600@example.com',
                'username': 'test.user600',
                'student_number': '55443322',
                'employee_number': None
            }
        }
        user = self.saml_authenticate(saml_data)
        self.assertIsNotNone(user)
        self.assertEqual(user.username, saml_data['attrs']['username'])
        self.assertEqual(user.email, saml_data['attrs']['email'])
        self.assertEqual(user.first_name, saml_data['attrs']['first_name'])
        self.assertEqual(user.last_name, saml_data['attrs']['last_name'])
        self.assertIsNotNone(user.profile)
        self.assertEqual(user.profile.student_number, saml_data['attrs']['student_number'])
        roles = userApi.get_user_roles(user)
        self.assertEqual(roles, ['Student'])
        self.assertIsNotNone(user.confidentiality)
        self.assertIsNone(user.confidentiality.employee_number)
        self.assertTrue(user.confidentiality.is_new_employee)

        # login - success
        saml_data2 = {
            'auth': True,
            'attrs': {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'username': user.username,
                'student_number': '55443322',
                'employee_number': None
            }
        }
        user2 = self.saml_authenticate(saml_data2)
        self.assertIsNotNone(user2)
        self.assertEqual(user2.username, saml_data2['attrs']['username'])
        self.assertEqual(user2.email, saml_data2['attrs']['email'])
        self.assertEqual(user2.first_name, saml_data2['attrs']['first_name'])
        self.assertEqual(user2.last_name, saml_data2['attrs']['last_name'])
        self.assertIsNotNone(user2.profile)
        self.assertEqual(user2.profile.student_number, saml_data2['attrs']['student_number'])
        roles2 = userApi.get_user_roles(user2)
        self.assertEqual(roles2, ['Student'])
        self.assertIsNotNone(user2.confidentiality)
        self.assertIsNone(user2.confidentiality.employee_number)
        self.assertTrue(user2.confidentiality.is_new_employee)

        # login - failure with same student number
        saml_data3 = {
            'auth': True,
            'attrs': {
                'first_name': 'Test2',
                'last_name': 'User6002',
                'email': 'test2.user6002@example.com',
                'username': 'test2.user6002',
                'student_number': '55443322',
                'employee_number': None
            }
        }
        user3 = self.saml_authenticate(saml_data3)
        self.assertEqual(user3, 'SuspiciousOperation')

        # login - success with different student number
        saml_data4 = {
            'auth': True,
            'attrs': {
                'first_name': 'Test2',
                'last_name': 'User6002',
                'email': 'test2.user6002@example.com',
                'username': 'test2.user6002',
                'student_number': '15443321',
                'employee_number': None
            }
        }
        user4 = self.saml_authenticate(saml_data4)
        self.assertIsNotNone(user4)
        self.assertEqual(user4.username, saml_data4['attrs']['username'])
        self.assertEqual(user4.email, saml_data4['attrs']['email'])
        self.assertEqual(user4.first_name, saml_data4['attrs']['first_name'])
        self.assertEqual(user4.last_name, saml_data4['attrs']['last_name'])
        self.assertIsNotNone(user4.profile)
        self.assertEqual(user4.profile.student_number, saml_data4['attrs']['student_number'])
        roles4 = userApi.get_user_roles(user4)
        self.assertEqual(roles4, ['Student'])
        self.assertIsNotNone(user4.confidentiality)
        self.assertIsNone(user4.confidentiality.employee_number)
        self.assertTrue(user4.confidentiality.is_new_employee)


    def test_login_duplicated_employee_number(self):
        print('- Test: login - duplicated employee number')

        # login - success
        saml_data = {
            'auth': True,
            'attrs': {
                'first_name': 'Test',
                'last_name': 'User600',
                'email': 'test.user600@example.com',
                'username': 'test.user600',
                'student_number': None,
                'employee_number': '5544332'
            }
        }
        user = self.saml_authenticate(saml_data)
        self.assertIsNotNone(user)
        self.assertEqual(user.username, saml_data['attrs']['username'])
        self.assertEqual(user.email, saml_data['attrs']['email'])
        self.assertEqual(user.first_name, saml_data['attrs']['first_name'])
        self.assertEqual(user.last_name, saml_data['attrs']['last_name'])
        self.assertIsNotNone(user.profile)
        self.assertIsNone(user.profile.student_number)
        roles = userApi.get_user_roles(user)
        self.assertEqual(roles, ['Student'])
        self.assertIsNotNone(user.confidentiality)
        self.assertEqual(user.confidentiality.employee_number, saml_data['attrs']['employee_number'])
        self.assertFalse(user.confidentiality.is_new_employee)

        # login - success
        saml_data2 = {
            'auth': True,
            'attrs': {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'username': user.username,
                'student_number': None,
                'employee_number': '5544332'
            }
        }
        user2 = self.saml_authenticate(saml_data2)
        self.assertIsNotNone(user2)
        self.assertEqual(user2.username, saml_data2['attrs']['username'])
        self.assertEqual(user2.email, saml_data2['attrs']['email'])
        self.assertEqual(user2.first_name, saml_data2['attrs']['first_name'])
        self.assertEqual(user2.last_name, saml_data2['attrs']['last_name'])
        self.assertIsNotNone(user2.profile)
        self.assertIsNone(user.profile.student_number)
        roles2 = userApi.get_user_roles(user2)
        self.assertEqual(roles2, ['Student'])
        self.assertIsNotNone(user2.confidentiality)
        self.assertEqual(user.confidentiality.employee_number, saml_data['attrs']['employee_number'])
        self.assertFalse(user2.confidentiality.is_new_employee)

        # login - failure with same employee number
        saml_data3 = {
            'auth': True,
            'attrs': {
                'first_name': 'Test2',
                'last_name': 'User6002',
                'email': 'test2.user6002@example.com',
                'username': 'test2.user6002',
                'student_number': None,
                'employee_number': '5544332'
            }
        }
        user3 = self.saml_authenticate(saml_data3)
        self.assertEqual(user3, 'SuspiciousOperation')

        # login - success with different employee number
        saml_data4 = {
            'auth': True,
            'attrs': {
                'first_name': 'Test2',
                'last_name': 'User6002',
                'email': 'test2.user6002@example.com',
                'username': 'test2.user6002',
                'student_number': None,
                'employee_number': '1544331'
            }
        }
        user4 = self.saml_authenticate(saml_data4)
        self.assertIsNotNone(user4)
        self.assertEqual(user4.username, saml_data4['attrs']['username'])
        self.assertEqual(user4.email, saml_data4['attrs']['email'])
        self.assertEqual(user4.first_name, saml_data4['attrs']['first_name'])
        self.assertEqual(user4.last_name, saml_data4['attrs']['last_name'])
        self.assertIsNotNone(user4.profile)
        self.assertIsNone(user4.profile.student_number)
        roles4 = userApi.get_user_roles(user4)
        self.assertEqual(roles4, ['Student'])
        self.assertIsNotNone(user4.confidentiality)
        self.assertEqual(user.confidentiality.employee_number, saml_data['attrs']['employee_number'])
        self.assertFalse(user4.confidentiality.is_new_employee)
