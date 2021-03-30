from django.test import TestCase
from django.urls import reverse
from administrators.tests.test_sessions import LOGIN_URL, ContentType, DATA, SESSION, PASSWORD, USERS

from users import api as userApi


USER = 'user120.test'

class ObserverTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        cls.user = userApi.get_user(USER, 'username')

    def login(self, username=None, password=None):
        if username and password:
            self.client.post(LOGIN_URL, data={'username': username, 'password': password})
        else:
            self.client.post(LOGIN_URL, data={'username': self.user.username, 'password': PASSWORD})

    def messages(self, res):
        return [m.message for m in get_messages(res.wsgi_request)]

    def test_view_url_exists_at_desired_location_admin(self):
        print('- Test: view url exists at desired location - admin')

        self.login(USERS[0], 'password')
        response = self.client.get( reverse('observers:index') )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('observers:report_accepted_applications') )
        self.assertEqual(response.status_code, 403)


    def test_view_url_exists_at_desired_location_instructor(self):
        print('- Test: view url exists at desired location - instructor')

        self.login(USERS[1], 'password')
        response = self.client.get( reverse('observers:index') )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('observers:report_accepted_applications') )
        self.assertEqual(response.status_code, 403)


    def test_view_url_exists_at_desired_location_student(self):
        print('- Test: view url exists at desired location - student')

        self.login(USERS[2], 'password')
        response = self.client.get( reverse('observers:index') )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('observers:report_accepted_applications') )
        self.assertEqual(response.status_code, 403)


    def test_view_url_exists_at_desired_location_observer(self):
        print('- Test: view url exists at desired location - observer')

        self.login()
        response = self.client.get( reverse('observers:index') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('observers:report_accepted_applications') )
        self.assertEqual(response.status_code, 200)


    def test_index(self):
        print('- Display an index page')
        self.login()

        response = self.client.get( reverse('observers:index') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USER)
        self.assertEqual(response.context['loggedin_user'].roles, ['Observer'])


    def test_report(self):
        print('- Display a report page')
        self.login()

        response = self.client.get( reverse('observers:report_accepted_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USER)
        self.assertEqual(response.context['loggedin_user'].roles, ['Observer'])
        self.assertEqual(response.context['total_apps'], 6)

        apps = [
            { 'id': 24, 'info': '2019_W2_APBI_260_001_user100.test' },
            { 'id': 22, 'info': '2019_W1_APBI_260_001_user100.test' },
            { 'id': 11, 'info': '2019_W1_APBI_200_002_user70.test' },
            { 'id': 8, 'info': '2019_W2_APBI_200_001_user66.test' },
            { 'id': 7, 'info': '2019_W1_APBI_260_001_user66.test' },
            { 'id': 1, 'info': '2019_W1_APBI_200_001_user100.test' }
        ]

        c = 0
        for app in response.context['apps']:
            self.assertEqual(app.id, apps[c]['id'])
            self.assertEqual(app.job.session.year + '_' + app.job.session.term.code + '_' + app.job.course.code.name + '_' + app.job.course.number.name + '_' + app.job.course.section.name + '_' + app.applicant.username, apps[c]['info'])
            c += 1
