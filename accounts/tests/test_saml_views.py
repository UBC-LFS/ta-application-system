from django.test import TestCase

from users import api as userApi

from administrators.tests.test_sessions import LOGIN_URL, ContentType, DATA, USERS, SESSION, JOB, APP, COURSE, PASSWORD


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

    def test_login_success_created_user_1(self):
        print('- Test: login success with a created user - no student number and no employee number')

        created_user = userApi.create_user({
            'first_name': 'User600',
            'last_name': 'Test',
            'email': 'user600.test@example.com',
            'username': 'user600.test',
            'student_number': None,
            'employee_number': None,
            #'puid': 'TEST00000600'
        })
        self.assertIsNotNone(created_user)
        self.assertIsNotNone( userApi.has_user_profile_created(created_user) )
        self.assertIsNotNone( userApi.has_user_confidentiality_created(created_user) )

        saml_data = {
            'auth': True,
            'attrs': {
                'first_name': created_user.first_name,
                'last_name': created_user.last_name,
                'email': created_user.email,
                'username': created_user.username,
                'student_number': None,
                'employee_number': None,
                #'puid': 'TEST00000600'
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
        #self.assertEqual(user.profile.puid, saml_data['attrs']['puid'])

        roles = userApi.get_user_roles(user)
        self.assertEqual(roles, ['Student'])
        self.assertIsNotNone(user.confidentiality)
        self.assertIsNone(user.confidentiality.employee_number)
        self.assertTrue(user.confidentiality.is_new_employee)


    def test_login_success_created_user_2(self):
        print('- Test: login success with a created user - yes student number and no employee number')

        created_user = userApi.create_user({
            'first_name': 'User600',
            'last_name': 'Test',
            'email': 'user600.test@example.com',
            'username': 'user600.test',
            'student_number': None,
            'employee_number': None,
            #'puid': 'TEST00000600'
        })
        self.assertIsNotNone(created_user)
        self.assertIsNotNone( userApi.has_user_profile_created(created_user) )
        self.assertIsNotNone( userApi.has_user_confidentiality_created(created_user) )

        saml_data = {
            'auth': True,
            'attrs': {
                'first_name': created_user.first_name,
                'last_name': created_user.last_name,
                'email': created_user.email,
                'username': created_user.username,
                'student_number': '58684563',
                'employee_number': None,
                #'puid': 'TEST00000600'
            }
        }
        user = self.saml_authenticate(saml_data)
        self.assertIsNotNone(user)
        self.assertEqual(user.username, saml_data['attrs']['username'])
        self.assertEqual(user.email, saml_data['attrs']['email'])
        self.assertEqual(user.first_name, saml_data['attrs']['first_name'])
        self.assertEqual(user.last_name, saml_data['attrs']['last_name'])
        self.assertIsNotNone(user.profile)
        self.assertEqual(user.profile.student_number,  saml_data['attrs']['student_number'])
        #self.assertEqual(user.profile.puid, saml_data['attrs']['puid'])

        roles = userApi.get_user_roles(user)
        self.assertEqual(roles, ['Student'])
        self.assertIsNotNone(user.confidentiality)
        self.assertIsNone(user.confidentiality.employee_number)
        self.assertTrue(user.confidentiality.is_new_employee)


    def test_login_success_created_user_3(self):
        print('- Test: login success with a created user - student number and yes employee number')

        created_user = userApi.create_user({
            'first_name': 'User600',
            'last_name': 'Test',
            'email': 'user600.test@example.com',
            'username': 'user600.test',
            'student_number': None,
            'employee_number': None,
            #'puid': 'TEST00000600'
        })
        self.assertIsNotNone(created_user)
        self.assertIsNotNone( userApi.has_user_profile_created(created_user) )
        self.assertIsNotNone( userApi.has_user_confidentiality_created(created_user) )

        saml_data = {
            'auth': True,
            'attrs': {
                'first_name': created_user.first_name,
                'last_name': created_user.last_name,
                'email': created_user.email,
                'username': created_user.username,
                'student_number': '58684563',
                'employee_number': '8456345',
                #'puid': 'TEST00000600'
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
        #self.assertEqual(user.profile.puid, saml_data['attrs']['puid'])

        roles = userApi.get_user_roles(user)
        self.assertEqual(roles, ['Student'])
        self.assertIsNotNone(user.confidentiality)
        self.assertEqual(user.confidentiality.employee_number, saml_data['attrs']['employee_number'])
        self.assertFalse(user.confidentiality.is_new_employee)


    def test_login_success_created_user_4(self):
        print('- Test: login success with a created user - change student number and employee number')

        created_user = userApi.create_user({
            'first_name': 'User600',
            'last_name': 'Test',
            'email': 'user600.test@example.com',
            'username': 'user600.test',
            'student_number': None,
            'employee_number': None,
            #'puid': 'TEST00000600'
        })
        self.assertIsNotNone(created_user)
        self.assertIsNotNone( userApi.has_user_profile_created(created_user) )
        self.assertIsNotNone( userApi.has_user_confidentiality_created(created_user) )

        saml_data = {
            'auth': True,
            'attrs': {
                'first_name': created_user.first_name,
                'last_name': created_user.last_name,
                'email': created_user.email,
                'username': created_user.username,
                'student_number': '58684500',
                'employee_number': '8456300',
                #'puid': 'TEST00000600'
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
        #self.assertEqual(user.profile.puid, saml_data['attrs']['puid'])

        roles = userApi.get_user_roles(user)
        self.assertEqual(roles, ['Student'])
        self.assertIsNotNone(user.confidentiality)
        self.assertEqual(user.confidentiality.employee_number, saml_data['attrs']['employee_number'])
        self.assertFalse(user.confidentiality.is_new_employee)


    def test_login_success_user_not_exists(self):
        print('- Test: login success - a user does not exist')

        # create and login
        saml_data = {
            'auth': True,
            'attrs': {
                'first_name': 'User700',
                'last_name': 'Test',
                'email': 'user700.test@example.com',
                'username': 'user700.test',
                'student_number': None,
                'employee_number': None,
                #'puid': 'TEST00000700'
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
        #self.assertEqual(user.profile.puid, saml_data['attrs']['puid'])

        roles = userApi.get_user_roles(user)
        self.assertEqual(roles, ['Student'])
        self.assertIsNotNone(user.confidentiality)
        self.assertIsNone(user.confidentiality.employee_number)
        self.assertTrue(user.confidentiality.is_new_employee)

        # login with an employee number
        saml_data2 = {
            'auth': True,
            'attrs': {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'username': user.username,
                'student_number': None,
                'employee_number': '6997879',
                #'puid': user.profile.puid
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
        #self.assertEqual(user2.profile.puid, saml_data2['attrs']['puid'])

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
                'employee_number': None,
                #'puid': 'TEST00000600'
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
                'employee_number': None,
                #'puid': 'TEST00000600'
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
        #self.assertEqual(user.profile.puid, saml_data['attrs']['puid'])

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
                'student_number': user.profile.student_number,
                'employee_number': None,
                #'puid': user.profile.puid
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
        #self.assertEqual(user2.profile.puid, saml_data2['attrs']['puid'])

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
                'employee_number': None,
                #'puid': 'TEST00000602'
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
                'employee_number': None,
                #'puid': 'TEST00000602'
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
        #self.assertEqual(user4.profile.puid, saml_data4['attrs']['puid'])

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
                'employee_number': '5544332',
                #'puid': 'TEST00000600'
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
        #self.assertEqual(user.profile.puid, saml_data['attrs']['puid'])

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
                'employee_number': '5544332',
                #'puid': user.profile.puid
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
        #self.assertEqual(user.profile.puid, saml_data['attrs']['puid'])

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
                'employee_number': '5544332',
                #'puid': 'TEST00000602'
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
                'employee_number': '1544331',
                #'puid': 'TEST00000602'
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
        #self.assertEqual(user4.profile.puid, saml_data4['attrs']['puid'])

        roles4 = userApi.get_user_roles(user4)
        self.assertEqual(roles4, ['Student'])
        self.assertIsNotNone(user4.confidentiality)
        self.assertEqual(user.confidentiality.employee_number, saml_data['attrs']['employee_number'])
        self.assertFalse(user4.confidentiality.is_new_employee)


    """def test_login_none_puid(self):
        print('- Test: login - none puid')
        # TODO


    def test_login_duplicated_puid(self):
        print('- Test: login - duplicated puid')

        # create and login
        saml_data = {
            'auth': True,
            'attrs': {
                'first_name': 'Test',
                'last_name': 'User600',
                'email': 'test.user600@example.com',
                'username': 'test.user600',
                'student_number': '96665541',
                'employee_number': '5544332',
                'puid': 'TEST00000600'
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
        self.assertEqual(user.profile.puid, saml_data['attrs']['puid'])

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
                'student_number': user.profile.student_number,
                'employee_number': user.confidentiality.employee_number,
                'puid': user.profile.puid
            }
        }
        user2 = self.saml_authenticate(saml_data2)
        self.assertIsNotNone(user2)
        self.assertEqual(user2.username, saml_data2['attrs']['username'])
        self.assertEqual(user2.email, saml_data2['attrs']['email'])
        self.assertEqual(user2.first_name, saml_data2['attrs']['first_name'])
        self.assertEqual(user2.last_name, saml_data2['attrs']['last_name'])
        self.assertIsNotNone(user2.profile)
        self.assertEqual(user.profile.student_number, saml_data['attrs']['student_number'])
        self.assertEqual(user.profile.puid, saml_data['attrs']['puid'])

        roles2 = userApi.get_user_roles(user2)
        self.assertEqual(roles2, ['Student'])
        self.assertIsNotNone(user2.confidentiality)
        self.assertEqual(user.confidentiality.employee_number, saml_data['attrs']['employee_number'])
        self.assertFalse(user2.confidentiality.is_new_employee)

        # login - failure with same puid
        saml_data3 = {
            'auth': True,
            'attrs': {
                'first_name': 'Test2',
                'last_name': 'User6002',
                'email': 'test2.user6002@example.com',
                'username': 'test2.user6002',
                'student_number': '11111113',
                'employee_number': '5544332',
                'puid': 'TEST00000600'
            }
        }
        user3 = self.saml_authenticate(saml_data3)
        self.assertEqual(user3, 'SuspiciousOperation')

        # login - success with different puid
        saml_data4 = {
            'auth': True,
            'attrs': {
                'first_name': 'Test2',
                'last_name': 'User6002',
                'email': 'test2.user6002@example.com',
                'username': 'test2.user6002',
                'student_number': '71111119',
                'employee_number': '1544331',
                'puid': 'TEST00000602'
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
        self.assertEqual(user4.profile.puid, saml_data4['attrs']['puid'])

        roles4 = userApi.get_user_roles(user4)
        self.assertEqual(roles4, ['Student'])
        self.assertIsNotNone(user4.confidentiality)
        self.assertEqual(user.confidentiality.employee_number, saml_data['attrs']['employee_number'])
        self.assertFalse(user4.confidentiality.is_new_employee)"""
