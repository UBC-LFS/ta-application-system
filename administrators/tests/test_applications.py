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

import datetime

from administrators.tests.test_sessions import LOGIN_URL, ContentType, DATA, PASSWORD, USERS, SESSION
from students.tests.test_views import STUDENT, STUDENT_JOB, HISTORY_NEXT, random_with_N_digits


APP = '2019-w1-apbi-200-001-introduction-to-soil-science-w1-application-by-user100test'

DASHBOARD_APP = '?next=' + reverse('administrators:applications_dashboard') + '?page=2&p=Dashboard'
ALL_APP = '?next=' + reverse('administrators:all_applications') + '?page=2&p=All%20Applications'
SELECTED_APP = '?next=' + reverse('administrators:selected_applications') + '?page=2&p=Selected%20Applications'
OFFERED_APP = '?next=' + reverse('administrators:offered_applications') + '?page=2&p=Offered%20Applications'
ACCEPTED_APP = '?next=' + reverse('administrators:accepted_applications') + '?page=2&p=Accepted%20Applications'
DECLINED_APP = '?next=' + reverse('administrators:declined_applications') + '?page=2&p=Declined%20Applications'
TERMINATED_APP = '?next=' + reverse('administrators:terminated_applications') + '?page=2&p=Terminated%20Applications'


class ApplicationTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        print('\nApplication testing has started ==>')
        cls.user = userApi.get_user(USERS[0], 'username')
        cls.testing_resume = os.path.join(settings.BASE_DIR, 'users', 'tests', 'files', 'resumeguide200914341.pdf')
        cls.testing_sin = os.path.join(settings.BASE_DIR, 'users', 'tests', 'files', 'karsten-wurth-9qvZSH_NOQs-unsplash.jpg')
        cls.testing_study_permit = os.path.join(settings.BASE_DIR, 'users', 'tests', 'files', 'lucas-davies-3aubsNmGuLE-unsplash.jpg')

    def login(self, username=None, password=None):
        if username and password:
            self.client.post(LOGIN_URL, data={'username': username, 'password': password})
        else:
            self.client.post(LOGIN_URL, data={'username': self.user.username, 'password': PASSWORD})

    def messages(self, res):
        return [m.message for m in get_messages(res.wsgi_request)]

    def json_messages(self, res):
        return json.loads( res.content.decode('utf-8') )


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


    def delete_document(self, user, list, option='domestic'):
        ''' Delete a list of document '''
        if 'resume' in list:
            userApi.delete_user_resume(user)

        if 'sin' in list:
            if option == 'international':
                userApi.delete_user_sin(user, '1')
            else:
                userApi.delete_user_sin(user)

        if 'study_permit' in list:
            if option == 'international':
                userApi.delete_user_study_permit(user, '1')
            else:
                userApi.delete_user_study_permit(user)


    def test_view_url_exists_at_desired_location(self):
        print('- Test: view url exists at desired location')
        self.login()

        response = self.client.get( reverse('administrators:show_application', args=[APP]) + ALL_APP )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:show_application', args=[APP]) + DASHBOARD_APP )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:applications_dashboard') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:all_applications') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:selected_applications') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:offered_applications') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:accepted_applications') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:declined_applications') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:applications_send_email_confirmation') + OFFERED_APP )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:applications_send_email_confirmation') + '?next=/administrators/applications/offerred/?page=2&p=Offered%20Applications' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:email_history') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:decline_reassign_confirmation') + '?next=' + reverse('administrators:accepted_applications') + '?page=2' )
        self.assertEqual(response.status_code, 200)

    def test_show_application(self):
        print('- Test: Display an application details')
        self.login()

        next = '?next=/administrators/applications/{0}/?page=2&p={1}'
        next_wrong = '?nex=/administrators/applications/{0}/?page=2&p={1}'
        next_page_wrong = '?administrators/applications/{0}/?page=2&a={1}'

        response = self.client.get( reverse('administrators:show_application', args=[APP]) + next_wrong.format('dashboard', 'Dashboard') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('administrators:show_application', args=[APP]) + next_page_wrong.format('dashboard', 'Dashboard') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('administrators:show_application', args=[APP]) + next.format('dashboardd', 'Dashboard') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('administrators:show_application', args=[APP]) + next.format('dashboard', 'Dashboardd') )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:show_application', args=[APP]) + next_wrong.format('all', 'All Applications') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('administrators:show_application', args=[APP]) + next_page_wrong.format('all', 'All Applications') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('administrators:show_application', args=[APP]) + next.format('alll', 'All Applications') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('administrators:show_application', args=[APP]) + next.format('all', 'AllApplications') )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:show_application', args=[APP]) + next_wrong.format('selected', 'Selected Applications') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('administrators:show_application', args=[APP]) + next_page_wrong.format('selected', 'Selected Applications') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('administrators:show_application', args=[APP]) + next.format('selectedd', 'Selected Applications') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('administrators:show_application', args=[APP]) + next.format('selected', 'Selected Application') )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:show_application', args=[APP]) + next_wrong.format('offered', 'Offered Applications') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('administrators:show_application', args=[APP]) + next_page_wrong.format('offered', 'Offered Applications') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('administrators:show_application', args=[APP]) + next.format('offred', 'Offered Applications') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('administrators:show_application', args=[APP]) + next.format('offered', 'offered Applications') )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:show_application', args=[APP]) + next_wrong.format('accepted', 'Accepted Applications') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('administrators:show_application', args=[APP]) + next_page_wrong.format('accepted', 'Accepted Applications') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('administrators:show_application', args=[APP]) + next.format('acceptd', 'Accepted Applications') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('administrators:show_application', args=[APP]) + next.format('accepted', 'Acceptd Applications') )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:show_application', args=[APP]) + next_wrong.format('declined', 'Declined Applications') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('administrators:show_application', args=[APP]) + next_page_wrong.format('declined', 'Declined Applications') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('administrators:show_application', args=[APP]) + next.format('declinedd', 'Declined Applications') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('administrators:show_application', args=[APP]) + next.format('declined', 'Declined applications') )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:show_application', args=[APP]) + next_wrong.format('terminated', 'Terminated Applications') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('administrators:show_application', args=[APP]) + next_page_wrong.format('terminated', 'Terminated Applications') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('administrators:show_application', args=[APP]) + next.format('terminate', 'Terminated Applications') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('administrators:show_application', args=[APP]) + next.format('terminated', 'Terminated Applicatios') )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:show_application', args=[APP]) + '?nex=/administrators/applications/?page=2&p=Email%20History' )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('administrators:show_application', args=[APP]) + '?next=/administrator/applications/?page=2&p=Email%20History' )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('administrators:show_application', args=[APP]) + '?next=/administrators/applications/?page=2&l=Email%20History' )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('administrators:show_application', args=[APP]) + '?next=/administrators/applications/?page=2&p=Email%20Histor' )
        self.assertEqual(response.status_code, 404)


        response = self.client.get( reverse('administrators:show_application', args=[APP]) + ALL_APP )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual(response.context['app'].slug, APP)

        app = adminApi.get_application(response.context['app'].slug, 'slug')
        self.assertEqual(response.context['app'].id, app.id)
        self.assertEqual(response.context['app'].applicant.username, app.applicant.username)


    def test_applications_dashboard(self):
        print('- Test: Display a dashboard to take a look at updates')
        self.login()


    def test_all_applications(self):
        print('- Test: Display all applications')
        self.login()

        response = self.client.get( reverse('administrators:all_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['apps']), 26)

        apps = response.context['apps']

        users = [
            { 'id': 1, 'can_reset': False, 'num_reset': 0 }, { 'id': 2, 'can_reset': True, 'num_reset': 0 },
            { 'id': 3, 'can_reset': False, 'num_reset': 0 }, { 'id': 4, 'can_reset': True, 'num_reset': 0 },
            { 'id': 5, 'can_reset': True, 'num_reset': 0 }, { 'id': 6, 'can_reset': False, 'num_reset': 0 },
            { 'id': 7, 'can_reset': False, 'num_reset': 0 }, { 'id': 8, 'can_reset': False, 'num_reset': 0 },
            { 'id': 9, 'can_reset': False, 'num_reset': 1 }, { 'id': 10, 'can_reset': False, 'num_reset': 1 },
            { 'id': 11, 'can_reset': False, 'num_reset': 0 }, { 'id': 12, 'can_reset': False, 'num_reset': 0 },
            { 'id': 13, 'can_reset': True, 'num_reset': 0 }, { 'id': 14, 'can_reset': True, 'num_reset': 0 },
            { 'id': 15, 'can_reset': True, 'num_reset': 0 }, { 'id': 16, 'can_reset': False, 'num_reset': 0 },
            { 'id': 17, 'can_reset': True, 'num_reset': 0 }, { 'id': 18, 'can_reset': False, 'num_reset': 0 },
            { 'id': 19, 'can_reset': False, 'num_reset': 0 }, { 'id': 20, 'can_reset': False, 'num_reset': 0 },
            { 'id': 21, 'can_reset': True, 'num_reset': 1 }, { 'id': 22, 'can_reset': False, 'num_reset': 0 },
            { 'id': 23, 'can_reset': False, 'num_reset': 0 }, { 'id': 24, 'can_reset': False, 'num_reset': 0 },
            { 'id': 25, 'can_reset': True, 'num_reset': 0 }, { 'id': 26, 'can_reset': False, 'num_reset': 0 }
        ]
        users.reverse()

        i = 0
        for app in apps:
            self.assertEqual(app.id, users[i]['id'])
            self.assertEqual(app.can_reset, users[i]['can_reset'])
            self.assertEqual(app.applicationreset_set.count(), users[i]['num_reset'])
            i += 1

    def test_reset_application_applied_app_wrong_next(self):
        print('- Test: reset an application - wrong next')
        self.login()

        app_id = '21'
        app = adminApi.get_application(app_id)
        self.assertEqual(app.instructor_preference, Application.ACCEPTABLE)

        data = {
            'application': app_id,
            'next': '/administrators/applications/selectedd/?page=2'
        }
        response = self.client.post(reverse('administrators:reset_application'), data=urlencode(data), content_type=ContentType)
        self.assertEqual(response.status_code, 404)


    def test_reset_application_applied_app_error(self):
        print('- Test: reset an application - applied app error')
        self.login()

        app_id = '6'
        PATH = '/administrators/applications/all/?page=2'

        data = {
            'application': app_id,
            'next': PATH
        }
        response = self.client.post(reverse('administrators:reset_application'), data=urlencode(data), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue(messages[0], 'An error occurred. Selected or Declined applications can be reset.')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, PATH)
        self.assertRedirects(response, response.url)


    def test_reset_application_offered_app_error(self):
        print('- Test: reset an application - offered app error')
        self.login()

        app_id = '3'
        PATH = '/administrators/applications/all/?page=2'

        data = {
            'application': app_id,
            'next': PATH
        }
        response = self.client.post(reverse('administrators:reset_application'), data=urlencode(data), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue(messages[0], 'An error occurred. Selected or Declined applications can be reset.')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, PATH)
        self.assertRedirects(response, response.url)


    def test_reset_application_accepted_app_error(self):
        print('- Test: reset an application - accepted app error')
        self.login()

        app_id = '6'
        PATH = '/administrators/applications/all/?page=2'

        data = {
            'application': app_id,
            'next': PATH
        }
        response = self.client.post(reverse('administrators:reset_application'), data=urlencode(data), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue(messages[0], 'An error occurred. Selected or Declined applications can be reset.')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, PATH)
        self.assertRedirects(response, response.url)


    def test_reset_application_selected_app_success(self):
        print('- Test: reset an application - selected app success')
        self.login()

        app_id = '2'
        PATH = '/administrators/applications/all/?page=2'

        data = {
            'application': app_id,
            'next': PATH
        }
        response = self.client.post(reverse('administrators:reset_application'), data=urlencode(data), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue(messages[0], 'Success! User65 Test - the following information (ID: 2, 2019 W1 - APBI 200 001) have been reset. <ul><li>Instructor Preference</li><li>Assigned Status</li><li>Assigned Hours</li></ul>')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, PATH)
        self.assertRedirects(response, response.url)


    def test_reset_application_declined_app_success(self):
        print('- Test: reset an application - declined app success')
        self.login()

        app_id = '25'
        PATH = '/administrators/applications/all/?page=2'

        data = {
            'application': app_id,
            'next': PATH
        }
        response = self.client.post(reverse('administrators:reset_application'), data=urlencode(data), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue(messages[0], 'Success! User100 Test - the following information (ID: 25, 2019 S - APBI 200 001) have been reset. <ul><li>Instructor Preference</li><li>Assigned Status</li><li>Assigned Hours</li></ul>')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, PATH)
        self.assertRedirects(response, response.url)


    def test_reset_application_terminated_app_success(self):
        print('- Test: reset an application - terminated app success')

        app_id = '22'

        self.login(USERS[2], PASSWORD)

        STUDENT_JOB = 'apbi-260-001-agroecology-i-introduction-to-principles-and-techniques-w1'
        HISTORY_NEXT = '?next=' + reverse('students:history_jobs') + '?page=2'

        response = self.client.get( reverse('students:terminate_job', args=[SESSION, STUDENT_JOB]) + HISTORY_NEXT )
        self.assertEqual(response.status_code, 200)

        app = response.context['app']
        self.assertEqual(app.id, 22)
        self.assertTrue(app.is_terminated)
        self.assertEqual(adminApi.get_latest_status_in_app(app), 'accepted')

        data = {
            'application': app.id,
            'assigned_hours': app.accepted.assigned_hours,
            'assigned': ApplicationStatus.CANCELLED,
            'parent_id': app.accepted.id,
            'next': reverse('students:history_jobs') + '?page=2'
        }

        response = self.client.post( reverse('students:terminate_job', args=[SESSION, STUDENT_JOB]) + HISTORY_NEXT, data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Application of 2019 W1 - APBI 260 001 terminated.' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:history_jobs') + '?page=2')
        self.assertRedirects(response, response.url)

        appl = adminApi.get_application(app_id)
        self.assertEqual(adminApi.get_latest_status_in_app(appl), 'cancelled')

        self.login()

        PATH = '/administrators/applications/all/?page=2'

        data = {
            'application': app_id,
            'next': PATH
        }
        response = self.client.post(reverse('administrators:reset_application'), data=urlencode(data), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue(messages[0], 'Success! User100 Test - the following information (ID: 1, 2019 W1 - APBI 200 001) have been reset. <ul><li>Instructor Preference</li><li>Assigned Status</li><li>Assigned Hours</li></ul>')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, PATH)
        self.assertRedirects(response, response.url)


    def test_see_reset_logs(self):
        print('- Test: see reset logs')
        self.login()

        app_id = 21

        response = self.client.get( reverse('administrators:all_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])

        apps = response.context['apps']
        self.assertEqual(len(apps), 26)

        users = [
            { 'id': 9, 'num_reset': 1, 'user': 'User2 Admin', 'created_at': '2020-09-26' },
            { 'id': 10, 'num_reset': 1, 'user': 'User2 Admin', 'created_at': '2020-09-27' },
            { 'id': 21, 'num_reset': 1, 'user': 'User2 Admin', 'created_at': '2020-10-15' }
        ]

        i = 0
        for app in apps:
            if app == users[i]['id']:
                self.assetEqual(app.applicationreset_set.count(), users[i]['num_reset'])
                self.assetEqual(app.applicationreset_set.first().user, users[i]['user'])
                self.assetEqual(app.applicationreset_set.first().created_at, users[i]['created_at'])
                i += 1


    def test_can_reoffer(self):
        print('- Test: can reoffer')
        self.login()

        response = self.client.get( reverse('administrators:selected_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])

        apps = response.context['apps']
        self.assertEqual(len(apps), 20)

        offer = []
        edit = []
        available_reoffer = []
        cannot_reoffer = []
        for app in apps:
            if app.offer_modal['title'] == 'Offer':
                offer.append(app.id)
            elif app.offer_modal['title'] == 'Edit Job Offer':
                edit.append(app.id)
            elif app.offer_modal['title'] == 'Re-offer':
                available_reoffer.append(app.id)
                if app.applicationstatus_set.last().assigned == ApplicationStatus.NONE:
                    cannot_reoffer.append(app.id)

        self.assertEqual(offer, [17, 15, 14, 13, 5, 4, 2])
        self.assertEqual(edit, [25, 24, 22, 20, 19, 11, 8, 7, 3, 1])
        self.assertEqual(available_reoffer, [21, 10, 9])
        self.assertEqual(cannot_reoffer, [10, 9])

    def test_reoffer_selected_application_success(self):
        print('- Test: reoffer a selected application - success')
        self.login()

        response = self.client.get( reverse('administrators:selected_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['apps']), 20)

        app_id = 21

        app = None
        for appl in response.context['apps']:
            if appl.id == app_id:
                app = appl
                break

        self.assertIsNotNone(app)
        self.assertIsNotNone(app.selected)
        self.assertEqual(app.selected.id, 72)
        self.assertEqual(app.selected.assigned, ApplicationStatus.SELECTED)
        self.assertEqual(app.selected.created_at, datetime.date(2020, 10, 17))

        FULL_PATH = reverse('administrators:selected_applications') + '?page=1'

        data = {
            'note': 'this is a note',
            'assigned_hours': app.selected.assigned_hours,
            'application': app.id,
            'assigned': ApplicationStatus.OFFERED,
            'applicant': '100',
            'classification': '2',
            'next': FULL_PATH
        }
        response = self.client.post(reverse('administrators:offer_job', args=[app.job.session.slug, app.job.course.slug]), data=urlencode(data), content_type=ContentType)
        messages = self.messages(response)
        self.assertEqual(messages[0], 'Success! You offered this user (User100 Test) 27 hours for this job (2019 W1 - APBI 200 002)')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        app2 = adminApi.get_application(app.id)
        self.assertEqual(app2.instructor_preference, Application.ACCEPTABLE)
        self.assertEqual(app2.classification.id, int(data['classification']))
        self.assertEqual(app2.note, data['note'])

        offered_app = adminApi.get_offered(app)
        self.assertFalse(offered_app.has_contract_read)
        self.assertTrue(offered_app.assigned, ApplicationStatus.OFFERED)
        self.assertEqual(offered_app.assigned_hours, float(data['assigned_hours']))


    def test_reoffer_applied_application_error(self):
        print('- Test: reoffer an applied application - error')
        self.login()

        app_id = 10

        app = adminApi.get_application(app_id)
        applied_app = adminApi.get_applied(app)
        self.assertIsNotNone(app)
        self.assertIsNotNone(applied_app)
        self.assertEqual(applied_app.id, 70)
        self.assertEqual(applied_app.assigned, ApplicationStatus.NONE)
        self.assertEqual(applied_app.created_at, datetime.date(2020, 9, 27))

        FULL_PATH = reverse('administrators:selected_applications') + '?page=1'

        data = {
            'note': 'this is a note',
            'assigned_hours': applied_app.assigned_hours,
            'application': app.id,
            'assigned': ApplicationStatus.OFFERED,
            'applicant': '70',
            'classification': '2',
            'next': FULL_PATH
        }
        response = self.client.post(reverse('administrators:offer_job', args=[app.job.session.slug, app.job.course.slug]), data=urlencode(data), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue(messages[0], 'An error occurred. An applied application cannot be reset.')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)


    def test_reset_aplication_success(self):
        print('- Test: reset an application - success')
        self.login()

        app_id = 13
        STUDENT = 'user70.test'

        # reset
        app1 = adminApi.get_application(app_id)
        self.assertEqual(app1.instructor_preference, Application.ACCEPTABLE)
        self.assertFalse(app1.is_declined_reassigned)
        self.assertFalse(app1.is_terminated)

        FULL_PATH = reverse('administrators:selected_applications') + '?page=1'

        data1 = {
            'application': app1.id,
            'next': FULL_PATH
        }
        response = self.client.post(reverse('administrators:reset_application'), data=urlencode(data1), content_type=ContentType)
        messages = self.messages(response)
        self.assertEqual(messages[0], 'Success! User70 Test - the following information (ID: 13, 2019 W2 - APBI 200 001) have been reset. <ul><li>Instructor Preference</li><li>Assigned Status</li><li>Assigned Hours</li></ul>')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        app2 = adminApi.get_application(app_id)
        self.assertEqual(app2.instructor_preference, Application.NONE)
        self.assertFalse(app2.is_declined_reassigned)
        self.assertFalse(app2.is_terminated)

        expected2 = [
            {'id': 13, 'assigned': ApplicationStatus.NONE, 'created_at': datetime.date(2019, 9, 1)},
            {'id': 36, 'assigned': ApplicationStatus.SELECTED, 'created_at': datetime.date(2019, 9, 5)},
            {'id': 79, 'assigned': ApplicationStatus.NONE, 'created_at': datetime.date.today()},
        ]

        count2 = 0
        for status in app2.applicationstatus_set.all():
            self.assertEqual(expected2[count2]['id'], status.id)
            self.assertEqual(expected2[count2]['assigned'], status.assigned)
            self.assertEqual(expected2[count2]['created_at'], status.created_at)
            count2 += 1


        # re-select
        self.login('user52.ins', PASSWORD)
        SESSION = '2019-w2'
        JOB = 'apbi-200-001-introduction-to-soil-science-w2'
        JOBS_NEXT = '?next=' + reverse('instructors:show_jobs') + '?page=2'

        data3 = {
            'assigned': ApplicationStatus.SELECTED,
            'application': app_id,
            'instructor_preference': Application.REQUESTED,
            'assigned_hours': 65
        }
        response = self.client.post( reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT, data=urlencode(data3), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue(messages[0], 'Success! User70 Test (CWL: user70.test) is selected.')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT )
        self.assertEqual(response.status_code, 200)

        this_app = None
        for app in response.context['job'].application_set.all():
            if app.id == app_id:
                this_app = app
                break

        self.assertEqual(this_app.instructor_preference, Application.REQUESTED)

        self.assertEqual( len(response.context['apps']) , 3 )
        app4 = None
        for app in response.context['apps']:
            if app.id == app_id:
                app4 = app
                break

        self.assertEqual(app4.id, app_id)
        self.assertEqual(app4.applicant.username, STUDENT)
        self.assertEqual(app4.applicationstatus_set.last().get_assigned_display(), 'Selected')
        self.assertEqual(app4.applicationstatus_set.last().assigned_hours, 65)
        self.assertEqual(app4.applicationstatus_set.last().created_at, datetime.date.today())


        # offer
        self.login()
        response = self.client.get( reverse('administrators:selected_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['apps']), 20)

        app5 = None
        for app in response.context['apps']:
            if app.id == app_id:
                app5 = app
                break

        self.assertIsNotNone(app5)
        self.assertIsNotNone(app5.selected)
        self.assertEqual(app5.selected.id, 80)
        self.assertEqual(app5.selected.assigned, ApplicationStatus.SELECTED)
        self.assertEqual(app5.selected.created_at, datetime.date.today())

        FULL_PATH = reverse('administrators:selected_applications') + '?page=1'

        data5 = {
            'note': 'this is a note',
            'assigned_hours': app5.selected.assigned_hours,
            'application': app5.id,
            'assigned': ApplicationStatus.OFFERED,
            'applicant': '70',
            'classification': '2',
            'next': FULL_PATH
        }
        response = self.client.post(reverse('administrators:offer_job', args=[app5.job.session.slug, app5.job.course.slug]), data=urlencode(data5), content_type=ContentType)
        messages = self.messages(response)
        self.assertEqual(messages[0], 'Success! You offered this user (User70 Test) 65 hours for this job (2019 W2 - APBI 200 001)')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        app6 = adminApi.get_application(app5.id)
        self.assertEqual(app6.instructor_preference, Application.REQUESTED)
        self.assertEqual(app6.classification.id, int(data5['classification']))
        self.assertEqual(app6.note, data5['note'])

        offered_app = adminApi.get_offered(app6)
        self.assertFalse(offered_app.has_contract_read)
        self.assertTrue(offered_app.assigned, ApplicationStatus.OFFERED)
        self.assertEqual(offered_app.assigned_hours, float(data5['assigned_hours']))


        # accept the offer
        self.login(STUDENT, PASSWORD)

        self.submit_confiential_information_international_complete(STUDENT)

        SESSION = '2019-w2'
        STUDENT_JOB = 'apbi-200-001-introduction-to-soil-science-w2'

        data7 = {
            'application': app6.id,
            'assigned_hours': offered_app.assigned_hours,
            'decision': 'accept',
            'has_contract_read': 'true',
            'next': reverse('students:history_jobs')
        }
        response = self.client.post( reverse('students:make_decision', args=[SESSION, STUDENT_JOB]), data=urlencode(data7), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue(messages[0], 'Success! You accepted the job offer - 2019 W2: APBI 200 001')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:history_jobs'))
        self.assertRedirects(response, response.url)

        final_app = adminApi.get_application(data7['application'])
        self.assertEqual(final_app.instructor_preference, Application.REQUESTED)
        self.assertFalse(final_app.is_declined_reassigned)
        self.assertFalse(final_app.is_terminated)

        expected7 = [
            {'id': 13, 'assigned': ApplicationStatus.NONE, 'created_at': datetime.date(2019, 9, 1)},
            {'id': 36, 'assigned': ApplicationStatus.SELECTED, 'created_at': datetime.date(2019, 9, 5)},
            {'id': 79, 'assigned': ApplicationStatus.NONE, 'created_at': datetime.date.today()},
            {'id': 80, 'assigned': ApplicationStatus.SELECTED, 'created_at': datetime.date.today()},
            {'id': 81, 'assigned': ApplicationStatus.OFFERED, 'created_at': datetime.date.today()},
            {'id': 82, 'assigned': ApplicationStatus.ACCEPTED, 'created_at': datetime.date.today()},
        ]

        count5 = 0
        for status in final_app.applicationstatus_set.all():
            self.assertEqual(expected7[count5]['id'], status.id)
            self.assertEqual(expected7[count5]['assigned'], status.assigned)
            self.assertEqual(expected7[count5]['created_at'], status.created_at)
            count5 += 1

        self.delete_document(STUDENT, ['sin', 'study_permit'], 'international')


    def test_reset_application_twice(self):
        print('- Test: reset an application twice')
        self.login()

        app_id = 25
        STUDENT = 'user100.test'

        # reset
        app1 = adminApi.get_application(app_id)
        self.assertEqual(app1.instructor_preference, Application.REQUESTED)
        self.assertFalse(app1.is_declined_reassigned)
        self.assertFalse(app1.is_terminated)

        FULL_PATH = reverse('administrators:selected_applications') + '?page=1'

        data1 = {
            'application': app1.id,
            'next': FULL_PATH
        }
        response = self.client.post(reverse('administrators:reset_application'), data=urlencode(data1), content_type=ContentType)
        messages = self.messages(response)
        self.assertEqual(messages[0], 'Success! User100 Test - the following information (ID: 25, 2019 S - APBI 200 001) have been reset. <ul><li>Instructor Preference</li><li>Assigned Status</li><li>Assigned Hours</li></ul>')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        app2 = adminApi.get_application(app_id)
        self.assertEqual(app2.instructor_preference, Application.NONE)
        self.assertFalse(app2.is_declined_reassigned)
        self.assertFalse(app2.is_terminated)

        expected2 = [
            {'id': 25, 'assigned': ApplicationStatus.NONE, 'created_at': datetime.date(2019, 9, 1)},
            {'id': 31, 'assigned': ApplicationStatus.SELECTED, 'created_at': datetime.date(2019, 9, 5)},
            {'id': 46, 'assigned': ApplicationStatus.OFFERED, 'created_at': datetime.date(2019, 9, 10)},
            {'id': 58, 'assigned': ApplicationStatus.DECLINED, 'created_at': datetime.date(2019, 9, 20)},
            {'id': 87, 'assigned': ApplicationStatus.NONE, 'created_at': datetime.date.today()}
        ]

        count2 = 0
        for status in app2.applicationstatus_set.all():
            self.assertEqual(expected2[count2]['id'], status.id)
            self.assertEqual(expected2[count2]['assigned'], status.assigned)
            self.assertEqual(expected2[count2]['created_at'], status.created_at)
            count2 += 1


        # re-select
        self.login('user22.ins', PASSWORD)
        SESSION = '2019-s'
        JOB = 'apbi-200-001-introduction-to-soil-science-s'
        JOBS_NEXT = '?next=' + reverse('instructors:show_jobs') + '?page=2'

        data3 = {
            'assigned': ApplicationStatus.SELECTED,
            'application': app_id,
            'instructor_preference': Application.REQUESTED,
            'assigned_hours': 65
        }
        response = self.client.post( reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT, data=urlencode(data3), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue(messages[0], 'Success! User100 Test (CWL: user100.test) is selected.')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('instructors:show_applications', args=[SESSION, JOB]) + JOBS_NEXT )
        self.assertEqual(response.status_code, 200)

        this_app = None
        for app in response.context['job'].application_set.all():
            if app.id == app_id:
                this_app = app
                break

        self.assertEqual(this_app.instructor_preference, Application.REQUESTED)

        self.assertEqual( len(response.context['apps']) , 2 )
        app4 = None
        for app in response.context['apps']:
            if app.id == app_id:
                app4 = app
                break

        self.assertEqual(app4.id, app_id)
        self.assertEqual(app4.applicant.username, STUDENT)
        self.assertEqual(app4.applicationstatus_set.last().get_assigned_display(), 'Selected')
        self.assertEqual(app4.applicationstatus_set.last().assigned_hours, 65)
        self.assertEqual(app4.applicationstatus_set.last().created_at, datetime.date.today())


        # offer
        self.login()
        response = self.client.get( reverse('administrators:selected_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['apps']), 20)

        app5 = None
        for app in response.context['apps']:
            if app.id == app_id:
                app5 = app
                break

        self.assertIsNotNone(app5)
        self.assertIsNotNone(app5.selected)
        self.assertEqual(app5.selected.id, 88)
        self.assertEqual(app5.selected.assigned, ApplicationStatus.SELECTED)
        self.assertEqual(app5.selected.created_at, datetime.date.today())

        FULL_PATH = reverse('administrators:selected_applications') + '?page=1'

        data5 = {
            'note': 'this is a note',
            'assigned_hours': app5.selected.assigned_hours,
            'application': app5.id,
            'assigned': ApplicationStatus.OFFERED,
            'applicant': '100',
            'classification': '2',
            'next': FULL_PATH
        }
        response = self.client.post(reverse('administrators:offer_job', args=[app5.job.session.slug, app5.job.course.slug]), data=urlencode(data5), content_type=ContentType)
        messages = self.messages(response)
        self.assertEqual(messages[0], 'Success! You offered this user (User100 Test) 65 hours for this job (2019 S - APBI 200 001)')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        app6 = adminApi.get_application(app5.id)
        self.assertEqual(app6.instructor_preference, Application.REQUESTED)
        self.assertEqual(app6.classification.id, int(data5['classification']))
        self.assertEqual(app6.note, data5['note'])

        offered_app = adminApi.get_offered(app6)
        self.assertFalse(offered_app.has_contract_read)
        self.assertTrue(offered_app.assigned, ApplicationStatus.OFFERED)
        self.assertEqual(offered_app.assigned_hours, float(data5['assigned_hours']))


        self.login(STUDENT, PASSWORD)

        self.submit_confiential_information_international_complete(STUDENT)

        SESSION = '2019-s'
        STUDENT_JOB = 'apbi-200-001-introduction-to-soil-science-s'

        data7 = {
            'application': app6.id,
            'assigned_hours': offered_app.assigned_hours,
            'decision': 'decline',
            'has_contract_read': 'true',
            'next': reverse('students:history_jobs')
        }
        response = self.client.post( reverse('students:make_decision', args=[SESSION, STUDENT_JOB]), data=urlencode(data7), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue(messages[0], 'Success! You declined the job offer - 2019 W2: APBI 200 001')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:history_jobs'))
        self.assertRedirects(response, response.url)

        app7 = adminApi.get_application(data7['application'])
        self.assertEqual(app7.instructor_preference, Application.REQUESTED)
        self.assertFalse(app7.is_declined_reassigned)
        self.assertFalse(app7.is_terminated)

        expected7 = [
            {'id': 25, 'assigned': ApplicationStatus.NONE, 'created_at': datetime.date(2019, 9, 1)},
            {'id': 31, 'assigned': ApplicationStatus.SELECTED, 'created_at': datetime.date(2019, 9, 5)},
            {'id': 46, 'assigned': ApplicationStatus.OFFERED, 'created_at': datetime.date(2019, 9, 10)},
            {'id': 58, 'assigned': ApplicationStatus.DECLINED, 'created_at': datetime.date(2019, 9, 20)},
            {'id': 87, 'assigned': ApplicationStatus.NONE, 'created_at': datetime.date.today()},
            {'id': 88, 'assigned': ApplicationStatus.SELECTED, 'created_at': datetime.date.today()},
            {'id': 89, 'assigned': ApplicationStatus.OFFERED, 'created_at': datetime.date.today()},
            {'id': 90, 'assigned': ApplicationStatus.DECLINED, 'created_at': datetime.date.today()},
        ]

        count5 = 0
        for status in app7.applicationstatus_set.all():
            self.assertEqual(expected7[count5]['id'], status.id)
            self.assertEqual(expected7[count5]['assigned'], status.assigned)
            self.assertEqual(expected7[count5]['created_at'], status.created_at)
            count5 += 1

        self.delete_document(STUDENT, ['sin', 'study_permit'], 'international')


        self.login()

        response = self.client.get( reverse('administrators:all_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])

        apps = response.context['apps']
        self.assertEqual(len(apps), 26)

        app8 = None
        for app in apps:
            if app.id == app_id:
                app8 = app
                break

        self.assertTrue(app8.can_reset)
        self.assertEqual(app8.applicationstatus_set.last().assigned, ApplicationStatus.DECLINED)
        self.assertEqual(app8.applicationreset_set.count(), 1)
        self.assertEqual(app8.applicationreset_set.last().created_at, datetime.date.today())
        self.assertEqual(app8.applicationreset_set.last().user, 'User2 Admin')


    def test_selected_applications(self):
        print('- Test: Display applications selected by instructors')
        self.login()

        response = self.client.get( reverse('administrators:selected_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['apps']), 20)
        self.assertEqual( len(response.context['classification_choices']), 6)
        self.assertEqual(response.context['app_status']['offered'], ApplicationStatus.OFFERED)

    def test_offer_job_wrong_next(self):
        print('- Test: Admin can offer a job to each job - wrong next')
        self.login()

        app_id = '2'
        app = adminApi.get_application(app_id)
        self.assertFalse(adminApi.get_offered(app))

        FULL_PATH = reverse('administrators:selected_applications') + '?page=2'

        data = {
            'note': 'this is a note',
            'assigned_hours': 'abcde',
            'application': app_id,
            'has_contract_read': False,
            'assigned': ApplicationStatus.OFFERED,
            'applicant': '65',
            'classification': '2',
            'next': '/administrators/applications/selectedd/?page=2'
        }
        response = self.client.post(reverse('administrators:offer_job', args=[app.job.session.slug, app.job.course.slug]), data=urlencode(data), content_type=ContentType)
        self.assertEqual(response.status_code, 404)


    def test_offer_job_wrong_assigned_hours(self):
        print('- Test: Admin can offer a job to each job - wrong assigned hours')
        self.login()

        app_id = '2'
        app = adminApi.get_application(app_id)
        self.assertFalse(adminApi.get_offered(app))

        FULL_PATH = reverse('administrators:selected_applications') + '?page=2'

        data = {
            'note': 'this is a note',
            'assigned_hours': 'abcde',
            'application': app_id,
            'has_contract_read': False,
            'assigned': ApplicationStatus.OFFERED,
            'applicant': '65',
            'classification': '2',
            'next': FULL_PATH
        }
        response = self.client.post(reverse('administrators:offer_job', args=[app.job.session.slug, app.job.course.slug]), data=urlencode(data), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)


    def test_offer_job_minus_assigned_hours(self):
        print('- Test: Admin can offer a job to each job - minus assigned hours')
        self.login()

        app_id = '2'
        app = adminApi.get_application(app_id)
        self.assertFalse(adminApi.get_offered(app))

        FULL_PATH = reverse('administrators:selected_applications') + '?page=2'

        data = {
            'note': 'this is a note',
            'assigned_hours': '-20.0',
            'application': app_id,
            'has_contract_read': False,
            'assigned': ApplicationStatus.OFFERED,
            'applicant': '65',
            'classification': '2',
            'next': FULL_PATH
        }
        response = self.client.post(reverse('administrators:offer_job', args=[app.job.session.slug, app.job.course.slug]), data=urlencode(data), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)


    def test_offer_job_none_classification(self):
        print('- Test: Admin can offer a job to each job - none classification')
        self.login()

        app_id = '2'
        app = adminApi.get_application(app_id)
        self.assertFalse(adminApi.get_offered(app))

        FULL_PATH = reverse('administrators:selected_applications') + '?page=2'

        data = {
            'note': 'this is a note',
            'assigned_hours': '20.0',
            'application': app_id,
            'has_contract_read': False,
            'assigned': ApplicationStatus.OFFERED,
            'applicant': '65',
            'next': FULL_PATH
        }
        response = self.client.post(reverse('administrators:offer_job', args=[app.job.session.slug, app.job.course.slug]), data=urlencode(data), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)


    def test_offer_job_empty_classification(self):
        print('- Test: Admin can offer a job to each job - empty classification')
        self.login()

        app_id = '2'
        app = adminApi.get_application(app_id)
        self.assertFalse(adminApi.get_offered(app))

        FULL_PATH = reverse('administrators:selected_applications') + '?page=2'

        data = {
            'note': 'this is a note',
            'assigned_hours': '20.0',
            'application': app_id,
            'has_contract_read': False,
            'assigned': ApplicationStatus.OFFERED,
            'applicant': '65',
            'classification': '',
            'next': FULL_PATH
        }
        response = self.client.post(reverse('administrators:offer_job', args=[app.job.session.slug, app.job.course.slug]), data=urlencode(data), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)


    def test_offer_job_max_assigned_hours(self):
        print('- Test: Admin can offer a job to each job - assigned hours are greater than total hours (200.0 hours)')
        self.login()

        app_id = '2'
        app = adminApi.get_application(app_id)
        self.assertFalse(adminApi.get_offered(app))

        FULL_PATH = reverse('administrators:selected_applications') + '?page=2'


        data = {
            'note': 'this is a note',
            'assigned_hours': '210.0',
            'application': app_id,
            'has_contract_read': False,
            'assigned': ApplicationStatus.OFFERED,
            'applicant': '65',
            'classification': '2',
            'next': FULL_PATH
        }
        response = self.client.post(reverse('administrators:offer_job', args=[app.job.session.slug, app.job.course.slug]), data=urlencode(data), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)


    def test_offer_job_success(self):
        print('- Test: Admin can offer a job to each job - success')
        self.login()

        app_id = '2'
        app = adminApi.get_application(app_id)
        self.assertFalse(adminApi.get_offered(app))

        FULL_PATH = reverse('administrators:selected_applications') + '?page=2'

        data = {
            'note': 'this is a note',
            'assigned_hours': '20.0',
            'application': app_id,
            'has_contract_read': False,
            'assigned': ApplicationStatus.OFFERED,
            'applicant': '65',
            'classification': '2',
            'next': FULL_PATH
        }
        response = self.client.post(reverse('administrators:offer_job', args=[app.job.session.slug, app.job.course.slug]), data=urlencode(data), content_type=ContentType)
        messages = self.messages(response)
        self.assertEqual(messages[0], 'Success! You offered this user (User65 Test) 20 hours for this job (2019 W1 - APBI 200 001)')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        app = adminApi.get_application(app_id)
        offered_app = adminApi.get_offered(app)
        self.assertEqual(app.classification.id, int(data['classification']))
        self.assertEqual(app.note, data['note'])
        self.assertFalse(offered_app.has_contract_read)
        self.assertTrue(offered_app.assigned, ApplicationStatus.OFFERED)
        self.assertEqual(offered_app.assigned_hours, float(data['assigned_hours']))

        # edit the offer job
        app = adminApi.add_app_info_into_application(app, ['offered'])

        # very large assigned hours
        data8 = {
            'classification': '2',
            'note': 'this is a note',
            'assigned_hours': '2000.0',
            'application': app_id,
            'applicationstatus': app.offered.id,
            'applicant': '65',
            'next': FULL_PATH
        }
        response = self.client.post(reverse('administrators:selected_applications'), data=urlencode(data8), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue(messages[0], 'An error occurred. Please you cannot assign 2000 hours Total Assigned TA Hours is 200, then try again.')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        data9 = {
            'classification': '3',
            'note': 'this is a note edited',
            'assigned_hours': '45.0',
            'application': app_id,
            'applicationstatus': app.offered.id,
            'applicant': '65',
            'next': FULL_PATH
        }
        response = self.client.post(reverse('administrators:selected_applications'), data=urlencode(data9), content_type=ContentType)
        messages = self.messages(response)
        self.assertEqual(messages[0], 'Success! Updated this application (ID: 2)')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        edited_app = adminApi.get_application(app_id)
        edited_app = adminApi.add_app_info_into_application(edited_app, ['offered'])
        self.assertEqual(edited_app.classification.id, int(data9['classification']))
        self.assertEqual(edited_app.note, data9['note'])
        self.assertEqual(edited_app.offered.assigned_hours, float(data9['assigned_hours']))


    def test_offered_applications(self):
        print('- Test: Display applications offered by admins')
        self.login()

        response = self.client.get( reverse('administrators:offered_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['apps']), 11)
        self.assertEqual( len(response.context['admin_emails']), 3)


    def test_offered_applications_no_response(self):
        print('- Test: Display applications offered by admins with no response')
        self.login()

        response = self.client.get( reverse('administrators:offered_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['apps']), 11)

        apps = response.context['apps']
        no_response = 0
        for app in apps:
            if app.accepted == None and app.declined == None:
                no_response += 1

        self.assertEqual(no_response, 3)


    def test_offered_applications_send_email(self):
        print('- Test: Send an email to offered applications')
        self.login()

        curr_emails = adminApi.get_emails()
        self.assertEqual( len(curr_emails), 6 )
        admin_emails = adminApi.get_admin_emails()

        data1 = {
            'application': [],
            'type': admin_emails.first().slug
        }

        response = self.client.post(reverse('administrators:applications_send_email') + OFFERED_APP, data=urlencode(data1, True), content_type=ContentType)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)
        self.assertEqual(response.url, reverse('administrators:offered_applications') + '?page=2')
        response = self.client.get(response.url)

        data2 = {
            'application': ['1', '25'],
            'type': admin_emails.first().slug
        }
        response = self.client.post(reverse('administrators:applications_send_email') + OFFERED_APP, data=urlencode(data2, True), content_type=ContentType)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)
        self.assertEqual(response.url, reverse('administrators:applications_send_email_confirmation') + OFFERED_APP)

        response = self.client.get(response.url)
        session = self.client.session
        self.assertEqual(session['applications_form_data']['applications'], data2['application'])

        app_ids = []
        user_emails = []
        for app in response.context['applications']:
            app_ids.append( str(app.id) )
            user_emails.append(app.applicant.email)

        self.assertEqual(len(response.context['applications']), len(data2['application']))
        self.assertEqual(response.context['sender'], settings.EMAIL_FROM)
        self.assertEqual(app_ids, data2['application'])
        self.assertFalse(response.context['form'].is_bound)
        self.assertEqual(response.context['admin_email'], admin_emails.first())

        data3 = {
            'sender': settings.EMAIL_FROM,
            'receiver': user_emails,
            'title': 'Congratulations!',
            'message': 'You have got an job offer',
            'type': response.context['admin_email'].type,
            'next': reverse('administrators:offered_applications') + '?page=2'
        }
        response = self.client.post(reverse('administrators:applications_send_email_confirmation') + OFFERED_APP, data=urlencode(data3, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertEqual(messages[0], 'Success! Email has been sent to user100.test@example.com')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual( len(adminApi.get_emails()), len(curr_emails) + len(user_emails) )


    def test_email_history(self):
        print('- Test: Display all of email sent by admins to let them know job offers')
        self.login()

        response = self.client.get(reverse('administrators:email_history') + '?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['emails']), 6 )

    def test_send_reminder(self):
        print('- Test: Send a reminder email')
        self.login()

        total_emails = len(adminApi.get_emails())

        FULL_PATH = reverse('administrators:email_history') + '?page=2'
        NEXT = '?next=' + FULL_PATH + '&p=Email%20History'

        email_id = '1'

        response = self.client.get(reverse('administrators:send_reminder', args=[email_id]) + '?next=' + FULL_PATH + '&p=Email%20Histor')
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse('administrators:send_reminder', args=[email_id]) + NEXT)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        email = response.context['form'].instance
        self.assertEqual( email.id, int(email_id) )

        data0 = {
            'application': email.application.id,
            'sender': email.sender,
            'receiver': email.receiver,
            'type': email.type,
            'title': email.title,
            'message': email.message,
            'next': '/administrators/application/email_history/?page=2'
        }
        response = self.client.post( reverse('administrators:send_reminder', args=[email_id]) + NEXT, data=urlencode(data0), content_type=ContentType )
        self.assertEqual(response.status_code, 404)

        data1 = {
            'application': email.application.id,
            'sender': email.sender,
            'receiver': email.receiver,
            'type': email.type,
            'title': email.title,
            'message': email.message,
            'next': FULL_PATH
        }
        response = self.client.post( reverse('administrators:send_reminder', args=[email_id]) + NEXT, data=urlencode(data1), content_type=ContentType )
        messages = self.messages(response)
        self.assertEqual(messages[0], 'Success! Email has sent to User100 Test <user100.test@example.com>')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)
        self.assertEqual(adminApi.get_emails().first().application.id, data1['application'])
        self.assertEqual(len(adminApi.get_emails()), total_emails + 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_accepted_applications(self):
        print('- Test: Display applications accepted by students')
        self.login()

        response = self.client.get( reverse('administrators:accepted_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['apps']), 5)

    def test_admin_docs_pin_invalid(self):
        print('- Test: Admin or HR can have update admin docs - pin invalid')
        self.login()

        FULL_PATH = reverse('administrators:accepted_applications') + '?page=2'
        NEXT = '?next=' + FULL_PATH

        app_id = 1

        data = {
            'application': app_id,
            'pin': '12377',
            'tasm': True,
            'processed': 'Done',
            'worktag': 'adsfabcde',
            'processing_note': 'this is a processing note'
        }
        response = self.client.post(reverse('administrators:update_admin_docs'), data=urlencode(data), content_type=ContentType)
        messages = self.json_messages(response)
        self.assertTrue('error', messages['status'])
        self.assertTrue('An error occurred' in messages['message'])
        self.assertEqual(response.status_code, 400)


    def test_admin_docs_worktag_invalid(self):
        print('- Test: Admin or HR can have update admin docs - worktag invalid')
        self.login()

        FULL_PATH = reverse('administrators:accepted_applications') + '?page=2'
        NEXT = '?next=' + FULL_PATH

        app_id = 1

        data = {
            'application': app_id,
            'pin': '12377',
            'tasm': True,
            'processed': 'Done',
            'worktag': 'adsfabcdedfaf',
            'processing_note': 'this is a processing note'
        }
        response = self.client.post(reverse('administrators:update_admin_docs'), data=urlencode(data), content_type=ContentType)
        messages = self.json_messages(response)
        self.assertTrue('error', messages['status'])
        self.assertTrue('An error occurred' in messages['message'])
        self.assertEqual(response.status_code, 400)



    def test_admin_docs_success(self):
        print('- Test: Admin or HR can have update admin docs - success')
        self.login()

        FULL_PATH = reverse('administrators:accepted_applications') + '?page=2'
        NEXT = '?next=' + FULL_PATH

        app_id = 1

        data = {
            'application': app_id,
            'pin': '1237',
            'tasm': True,
            'processed': 'Done',
            'worktag': 'adsffddf',
            'processing_note': 'this is a processing note'
        }
        response = self.client.post(reverse('administrators:update_admin_docs'), data=urlencode(data), content_type=ContentType)
        messages = self.json_messages(response)
        self.assertTrue('success', messages['status'])
        self.assertTrue('Success' in messages['message'])
        self.assertEqual(response.status_code, 200)

        response = self.client.get(FULL_PATH)
        self.assertEqual(response.status_code, 200)
        accepted_applications = response.context['apps']

        app = None
        for appl in accepted_applications:
            if appl.id == app_id:
                app = appl

        self.assertTrue(app.id, app_id)
        self.assertTrue(app.admindocuments.pin, data['pin'])
        self.assertTrue(app.admindocuments.tasm, data['tasm'])
        self.assertTrue(app.admindocuments.processed, data['processed'])
        self.assertTrue(app.admindocuments.worktag, data['worktag'])
        self.assertTrue(app.admindocuments.processing_note, data['processing_note'])


    def test_declined_applications(self):
        print('- Test: Display applications declined by students')
        self.login()

        response = self.client.get( reverse('administrators:declined_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['apps']), 4)

    def test_declined_applications_send_email(self):
        print('- Test: Send an email to declined applications')
        self.login()

        curr_emails = adminApi.get_emails()
        self.assertEqual( len(curr_emails), 6 )
        admin_emails = adminApi.get_admin_emails()

        data1 = {
            'application': [],
            'type': admin_emails.first().slug
        }

        response = self.client.post(reverse('administrators:applications_send_email') + DECLINED_APP, data=urlencode(data1, True), content_type=ContentType)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)
        self.assertEqual(response.url, reverse('administrators:declined_applications') + '?page=2')
        response = self.client.get(response.url)

        data2 = {
            'application': ['7', '24'],
            'type': admin_emails.first().slug
        }
        response = self.client.post(reverse('administrators:applications_send_email') + DECLINED_APP, data=urlencode(data2, True), content_type=ContentType)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)
        self.assertEqual(response.url, reverse('administrators:applications_send_email_confirmation') + DECLINED_APP)

        response = self.client.get(response.url)
        session = self.client.session
        self.assertEqual(session['applications_form_data']['applications'], data2['application'])

        app_ids = []
        user_emails = []
        for app in response.context['applications']:
            app_ids.append( str(app.id) )
            user_emails.append(app.applicant.email)

        self.assertEqual(len(response.context['applications']), len(data2['application']))
        self.assertEqual(response.context['sender'], settings.EMAIL_FROM)
        self.assertEqual(app_ids, data2['application'])
        self.assertFalse(response.context['form'].is_bound)
        self.assertEqual(response.context['admin_email'], admin_emails.first())

        data3 = {
            'sender': settings.EMAIL_FROM,
            'receiver': user_emails,
            'title': 'You are declined!',
            'message': 'You are declined an job offer',
            'type': response.context['admin_email'].type,
            'next': reverse('administrators:declined_applications') + '?page=2'
        }
        response = self.client.post(reverse('administrators:applications_send_email_confirmation') + DECLINED_APP, data=urlencode(data3, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertEqual(messages[0], 'Success! Email has been sent to user100.test@example.com')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual( len(adminApi.get_emails()), len(curr_emails) + len(user_emails) )


    def test_decline_reassign(self):
        print('- Test: Decline and reassign a job offer with new assigned hours')
        self.login()

        FULL_PATH = reverse('administrators:accepted_applications') + '?page=2'
        NEXT = '?next=' + FULL_PATH
        app_id = 1

        response = self.client.get(FULL_PATH)
        self.assertEqual(response.status_code, 200)
        accepted_applications = response.context['apps']

        application = None
        for app in accepted_applications:
            if app.id == app_id:
                application = app
                break

        data1 = {
            'application': str(application.id),
            'new_assigned_hours': 'abcde',
            'old_assigned_hours': str(application.accepted.assigned_hours)
        }
        response = self.client.post(reverse('administrators:decline_reassign') + NEXT, data=urlencode(data1), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        data2 = {
            'application': str(application.id),
            'new_assigned_hours': '-10.0',
            'old_assigned_hours': str(application.accepted.assigned_hours)
        }
        response = self.client.post(reverse('administrators:decline_reassign') + NEXT, data=urlencode(data2), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        data3 = {
            'application': str(application.id),
            'new_assigned_hours': '0.0',
            'old_assigned_hours': str(application.accepted.assigned_hours)
        }
        response = self.client.post(reverse('administrators:decline_reassign') + NEXT, data=urlencode(data3), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        data4 = {
            'application': str(application.id),
            'new_assigned_hours': '201.0',
            'old_assigned_hours': str(application.accepted.assigned_hours)
        }
        response = self.client.post(reverse('administrators:decline_reassign') + NEXT, data=urlencode(data4), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        accumulated_ta_hours = app.job.accumulated_ta_hours
        data5 = {
            'application': str(application.id),
            'new_assigned_hours': '20.0',
            'old_assigned_hours': str(application.accepted.assigned_hours)
        }
        response = self.client.post(reverse('administrators:decline_reassign') + NEXT, data=urlencode(data5), content_type=ContentType)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(response.url)
        session = self.client.session
        self.assertEqual(session['decline_reassign_form_data'], data5)

        data6 = {
            'application': str(application.id),
            'new_assigned_hours': '20.0',
            'old_assigned_hours': str(application.accepted.assigned_hours),
            'next' : 'administrator/applications/accepted/?page=2'
        }
        response = self.client.post( reverse('administrators:decline_reassign_confirmation') + NEXT, data=urlencode(data6), content_type=ContentType )
        self.assertEqual(response.status_code, 404)

        data7 = {
            'application': str(application.id),
            'new_assigned_hours': '20.0',
            'old_assigned_hours': str(application.accepted.assigned_hours),
            'next' : FULL_PATH
        }
        response = self.client.post( reverse('administrators:decline_reassign_confirmation') + NEXT, data=urlencode(data7), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        data8 = {
            'application': str(application.id),
            'new_assigned_hours': '20.0',
            'old_assigned_hours': str(application.accepted.assigned_hours),
            'is_declined_reassigned': True,
            'next' : FULL_PATH
        }
        response = self.client.post( reverse('administrators:decline_reassign_confirmation') + NEXT, data=urlencode(data8), content_type=ContentType )
        messages = self.messages(response)
        self.assertEqual(messages[0], 'Success! The status of Application (ID: 1) updated')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        response = self.client.get(FULL_PATH)
        self.assertEqual(response.status_code, 200)
        accepted_applications = response.context['apps']

        updated_app = None
        for app in accepted_applications:
            if app.id == app_id:
                updated_app = app
                break

        self.assertEqual(str(updated_app.id), data8['application'])
        self.assertTrue(updated_app.is_declined_reassigned)
        self.assertEqual(updated_app.applicationstatus_set.last().get_assigned_display(), 'Declined')
        self.assertEqual(str(updated_app.applicationstatus_set.last().assigned_hours), data8['new_assigned_hours'])

    def test_decline_reassign_processed_processing_note(self):
        print('- Test: Decline and reassign a job offer with new assigned hours and processed data moves to processing note')
        self.login()

        FULL_PATH = reverse('administrators:accepted_applications') + '?page=2'
        NEXT = '?next=' + FULL_PATH
        app_id = 1

        response = self.client.get(FULL_PATH)
        self.assertEqual(response.status_code, 200)
        accepted_applications = response.context['apps']

        application = None
        for app in accepted_applications:
            if app.id == app_id:
                application = app
                break

        self.assertFalse( hasattr(application, 'admindocuments') )

        # no processed exists
        data1 = {
            'application': str(application.id),
            'new_assigned_hours': '20.0',
            'old_assigned_hours': str(application.accepted.assigned_hours),
            'is_declined_reassigned': True,
            'next' : FULL_PATH
        }
        response = self.client.post( reverse('administrators:decline_reassign_confirmation') + NEXT, data=urlencode(data1), content_type=ContentType )
        messages = self.messages(response)
        self.assertEqual(messages[0], 'Success! The status of Application (ID: 1) updated')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        response = self.client.get(FULL_PATH)
        self.assertEqual(response.status_code, 200)
        accepted_applications = response.context['apps']

        updated_app = None
        for app in accepted_applications:
            if app.id == app_id:
                updated_app = app
                break

        self.assertEqual(str(updated_app.id), data1['application'])
        self.assertTrue(updated_app.is_declined_reassigned)
        self.assertEqual(updated_app.applicationstatus_set.last().get_assigned_display(), 'Declined')
        self.assertEqual(str(updated_app.applicationstatus_set.last().assigned_hours), data1['new_assigned_hours'])

        # processed exists
        data2 = {
            'application': app_id,
            'pin': '1237',
            'tasm': True,
            'processed': 'Done',
            'worktag': 'adsfggrr',
            'processing_note': '<p>this is a processing note.</p>'
        }
        response = self.client.post(reverse('administrators:update_admin_docs'), data=urlencode(data2), content_type=ContentType)
        messages = self.json_messages(response)
        self.assertTrue('success', messages['status'])
        self.assertTrue('Success' in messages['message'])
        self.assertEqual(response.status_code, 200)

        response = self.client.get(FULL_PATH)
        self.assertEqual(response.status_code, 200)
        accepted_applications = response.context['apps']

        app = None
        for appl in accepted_applications:
            if appl.id == app_id:
                app = appl

        self.assertTrue(app.id, app_id)
        self.assertTrue(app.admindocuments.pin, data2['pin'])
        self.assertTrue(app.admindocuments.tasm, data2['tasm'])
        self.assertTrue(app.admindocuments.processed, data2['processed'])
        self.assertTrue(app.admindocuments.worktag, data2['worktag'])
        self.assertTrue(app.admindocuments.processing_note, data2['processing_note'])

        data3 = {
            'application': str(application.id),
            'new_assigned_hours': '30.0',
            'old_assigned_hours': str(application.accepted.assigned_hours),
            'is_declined_reassigned': True,
            'next' : FULL_PATH
        }
        response = self.client.post( reverse('administrators:decline_reassign_confirmation') + NEXT, data=urlencode(data3), content_type=ContentType )
        messages = self.messages(response)
        self.assertEqual(messages[0], 'Success! The status of Application (ID: 1) updated')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        response = self.client.get(FULL_PATH)
        self.assertEqual(response.status_code, 200)
        accepted_applications = response.context['apps']

        updated_app = None
        for app in accepted_applications:
            if app.id == app_id:
                updated_app = app
                break

        self.assertEqual(str(updated_app.id), data3['application'])
        self.assertTrue(updated_app.is_declined_reassigned)
        self.assertEqual(updated_app.applicationstatus_set.last().get_assigned_display(), 'Declined')
        self.assertEqual(str(updated_app.applicationstatus_set.last().assigned_hours), data3['new_assigned_hours'])

        self.assertTrue( hasattr(updated_app, 'admindocuments') )
        self.assertTrue(updated_app.admindocuments.pin, data2['pin'])
        self.assertTrue(updated_app.admindocuments.tasm, data2['tasm'])
        self.assertIsNone(updated_app.admindocuments.processed)
        self.assertTrue(updated_app.admindocuments.worktag, data2['worktag'])
        self.assertEqual(updated_app.admindocuments.processing_note, "<p>this is a processing note.</p><p>Auto update: Processed - <strong class='text-primary'>Done</strong> on {0}</p>".format( datetime.date.today().strftime('%Y-%m-%d') ))


    def test_decline_reassign_empty_processed(self):
        print('- Test: Decline and reassign a job offer with new assigned hours - empty processed')
        self.login()

        FULL_PATH = reverse('administrators:accepted_applications') + '?page=2'
        NEXT = '?next=' + FULL_PATH
        app_id = 8

        response = self.client.get(FULL_PATH)
        self.assertEqual(response.status_code, 200)
        accepted_applications = response.context['apps']

        application = None
        for app in accepted_applications:
            if app.id == app_id:
                application = app
                break

        self.assertTrue( hasattr(application, 'admindocuments') )

        data = {
            'application': str(application.id),
            'new_assigned_hours': '31.0',
            'old_assigned_hours': str(application.accepted.assigned_hours),
            'is_declined_reassigned': 'true',
            'next' : FULL_PATH
        }
        response = self.client.post( reverse('administrators:decline_reassign_confirmation') + NEXT, data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertEqual(messages[0], 'Success! The status of Application (ID: 8) updated')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        found_app = adminApi.get_application(application.id)
        self.assertEqual(found_app.admindocuments.processing_note, 'This is a processing note')


    def test_terminate(self):
        print('- Test: terminate an application')
        self.login()

        app_id = '22'
        appl = adminApi.get_application(app_id)
        self.assertTrue(appl.is_terminated)

        FULL_PATH = reverse('administrators:accepted_applications') + '?page=2'
        NEXT = '?next=' + FULL_PATH

        data1 = {
            'note': 'terminated note',
            'is_terminated': True,
            'next': FULL_PATH
        }
        response = self.client.post(reverse('administrators:terminate', args=[appl.slug]), data=urlencode(data1), content_type=ContentType)
        self.assertEqual(response.status_code, 404)

        app_id = 8
        appl = adminApi.get_application(app_id)
        self.assertFalse(appl.is_terminated)

        data2 = {
            'note': 'terminated note',
            'next': '/Administrators/applications/accepted/?page=2'
        }
        response = self.client.post(reverse('administrators:terminate', args=[appl.slug]) + NEXT, data=urlencode(data2), content_type=ContentType)
        self.assertEqual(response.status_code, 404)

        data3 = {
            'note': 'terminated note',
            'next': FULL_PATH
        }
        response = self.client.post(reverse('administrators:terminate', args=[appl.slug]) + NEXT, data=urlencode(data3), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:terminate', args=[appl.slug]) + NEXT)
        self.assertRedirects(response, response.url)

        data4 = {
            'note': 'terminated note',
            'is_terminated': True,
            'next': FULL_PATH
        }
        response = self.client.post(reverse('administrators:terminate', args=[appl.slug]) + NEXT, data=urlencode(data4), content_type=ContentType)
        messages = self.messages(response)
        self.assertEqual(messages[0], 'Success! Application (ID: 8) terminated.')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        response = self.client.get(FULL_PATH)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('administrators:terminated_applications'))
        apps = response.context['apps']

        application = None
        for app in apps:
            if app.id == app_id:
                application = app
                break

        self.assertTrue(application.is_terminated)

    def test_terminated_applications(self):
        print('- Test: Display applications terminated by students')
        self.login()

        response = self.client.get( reverse('administrators:terminated_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['apps']), 1)

    def test_terminated_applications_send_email(self):
        print('- Test: Send an email to terminated applications')
        self.login()

        curr_emails = adminApi.get_emails()
        self.assertEqual( len(curr_emails), 6 )
        admin_emails = adminApi.get_admin_emails()

        data1 = {
            'application': [],
            'type': admin_emails.first().slug
        }

        response = self.client.post(reverse('administrators:applications_send_email') + TERMINATED_APP, data=urlencode(data1, True), content_type=ContentType)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)
        self.assertEqual(response.url, reverse('administrators:terminated_applications') + '?page=2')
        response = self.client.get(response.url)

        data2 = {
            'application': ['22'],
            'type': admin_emails.first().slug
        }
        response = self.client.post(reverse('administrators:applications_send_email') + TERMINATED_APP, data=urlencode(data2, True), content_type=ContentType)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)
        self.assertEqual(response.url, reverse('administrators:applications_send_email_confirmation') + TERMINATED_APP)

        response = self.client.get(response.url)
        session = self.client.session
        self.assertEqual(session['applications_form_data']['applications'], data2['application'])

        app_ids = []
        user_emails = []
        for app in response.context['applications']:
            app_ids.append( str(app.id) )
            user_emails.append(app.applicant.email)

        self.assertEqual(len(response.context['applications']), len(data2['application']))
        self.assertEqual(response.context['sender'], settings.EMAIL_FROM)
        self.assertEqual(app_ids, data2['application'])
        self.assertFalse(response.context['form'].is_bound)
        self.assertEqual(response.context['admin_email'], admin_emails.first())
        email = response.context['admin_email']

        data3 = {
            'sender': settings.EMAIL_FROM,
            'receiver': user_emails,
            'title': 'You are terminated!',
            'message': 'You are terminated an job offer',
            'type': email.type,
            'next': '/administrators/applications/terminatted/?page=2'
        }
        response = self.client.post(reverse('administrators:applications_send_email_confirmation') + TERMINATED_APP, data=urlencode(data3), content_type=ContentType)
        self.assertEqual(response.status_code, 404)

        data4 = {
            'sender': settings.EMAIL_FROM,
            'receiver': user_emails,
            'title': 'You are terminated!',
            'message': 'You are terminated an job offer',
            'type': email.type,
            'next': reverse('administrators:terminated_applications') + '?page=2'
        }
        response = self.client.post(reverse('administrators:applications_send_email_confirmation') + TERMINATED_APP, data=urlencode(data4), content_type=ContentType)
        messages = self.messages(response)
        self.assertEqual(messages[0], "Success! Email has been sent to ['user100.test@example.com']")
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual( len(adminApi.get_emails()), len(curr_emails) + len(user_emails) )


class SchedulingTaskTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        print('\nScheduling Task testing has started ==>')
        cls.user = userApi.get_user(USERS[0], 'username')
        cls.testing_sin = os.path.join(settings.BASE_DIR, 'users', 'tests', 'files', 'karsten-wurth-9qvZSH_NOQs-unsplash.jpg')
        cls.testing_study_permit = os.path.join(settings.BASE_DIR, 'users', 'tests', 'files', 'lucas-davies-3aubsNmGuLE-unsplash.jpg')

    def login(self, username=None, password=None):
        if username and password:
            self.client.post(LOGIN_URL, data={'username': username, 'password': password})
        else:
            self.client.post(LOGIN_URL, data={'username': self.user.username, 'password': PASSWORD})

    def messages(self, res):
        return [m.message for m in get_messages(res.wsgi_request)]

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


    def delete_document(self, user, list, option='domestic'):
        ''' Delete a list of document '''
        if 'resume' in list:
            userApi.delete_user_resume(user)

        if 'sin' in list:
            if option == 'international':
                userApi.delete_user_sin(user, '1')
            else:
                userApi.delete_user_sin(user)

        if 'study_permit' in list:
            if option == 'international':
                userApi.delete_user_study_permit(user, '1')
            else:
                userApi.delete_user_study_permit(user)


    def accept_offer_user65(self):
        STUDENT = 'user65.test'

        self.login(STUDENT, PASSWORD)

        self.submit_confiential_information_international_complete(STUDENT)

        response = self.client.get( reverse('students:accept_decline_job', args=[SESSION, STUDENT_JOB]) + HISTORY_NEXT )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, STUDENT)
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        app = response.context['app']
        self.assertEqual(app.job.course.slug, STUDENT_JOB)
        self.assertEqual(app.applicant.username, STUDENT)

        data = {
            'application': app.id,
            'assigned_hours': app.offered.assigned_hours,
            'decision': 'accept',
            'has_contract_read': 'true',
            'next': reverse('students:history_jobs')
        }
        response = self.client.post( reverse('students:make_decision', args=[SESSION, STUDENT_JOB]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:history_jobs'))
        self.assertRedirects(response, response.url)

        self.delete_document(STUDENT, ['sin', 'study_permit'], 'international')


    def terminated_offer_user100(self):

        STUDENT_JOB = 'apbi-260-001-agroecology-i-introduction-to-principles-and-techniques-w1'
        self.login(USERS[2], PASSWORD)
        app_id = '22'

        data = {
            'application': app_id,
            'assigned_hours':70.0,
            'assigned': ApplicationStatus.CANCELLED,
            'parent_id': '57',
            'next': reverse('students:history_jobs')
        }
        response = self.client.post( reverse('students:terminate_job', args=[SESSION, STUDENT_JOB]) + HISTORY_NEXT, data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Application of 2019 W1 - APBI 260 001 terminated.' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('students:history_jobs'))
        self.assertRedirects(response, response.url)


    def test_send_accepted_apps(self):
        print('- Test: send accepted apps')

        self.accept_offer_user65()

        self.login()

        app_statuses = adminApi.get_today_accepted_apps()

        app_list = [
            { 'app_status_id': 73, 'assigned': '3', 'assigned_hours': 15.0, 'app_id': 3, 'full_name': 'User65 Test', 'session_term': '2019 W1 - APBI 265 001' }
        ]

        c = 0
        for app_status in app_statuses:
            self.assertEqual(app_status.id, app_list[0]['app_status_id'])
            self.assertEqual(app_status.assigned, app_list[0]['assigned'])
            self.assertEqual(app_status.assigned_hours, app_list[0]['assigned_hours'])
            self.assertEqual(app_status.application.id, app_list[0]['app_id'])
            self.assertEqual(app_status.application.applicant.get_full_name(), app_list[0]['full_name'])
            self.assertEqual(adminApi.get_session_term_full_name(app_status.application), app_list[0]['session_term'])
            c += 1


    def test_send_terminated_apps(self):
        print('- Test: send terminated apps')
        self.login()

        self.terminated_offer_user100()

        self.login()

        app_statuses = adminApi.get_today_terminated_apps()

        app_list = [
            { 'app_status_id': 74, 'assigned': '5', 'assigned_hours': 70.0, 'app_id': 22, 'full_name': 'User100 Test', 'session_term': '2019 W1 - APBI 260 001' }
        ]

        c = 0
        for app_status in app_statuses:
            self.assertEqual(app_status.id, app_list[0]['app_status_id'])
            self.assertEqual(app_status.assigned, app_list[0]['assigned'])
            self.assertEqual(app_status.assigned_hours, app_list[0]['assigned_hours'])
            self.assertEqual(app_status.application.id, app_list[0]['app_id'])
            self.assertEqual(app_status.application.applicant.get_full_name(), app_list[0]['full_name'])
            self.assertEqual(adminApi.get_session_term_full_name(app_status.application), app_list[0]['session_term'])
            c += 1
