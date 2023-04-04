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

from datetime import datetime
from random import randint

LOGIN_URL = '/accounts/local-login/'
ContentType='application/x-www-form-urlencoded'

DATA = [
    'ta_app/fixtures/admin_emails.json',
    'ta_app/fixtures/classifications.json',
    'ta_app/fixtures/course_codes.json',
    'ta_app/fixtures/course_numbers.json',
    'ta_app/fixtures/course_sections.json',
    'ta_app/fixtures/degrees.json',
    'ta_app/fixtures/landing_pages.json',
    'ta_app/fixtures/programs.json',
    'ta_app/fixtures/roles.json',
    'ta_app/fixtures/statuses.json',
    'ta_app/fixtures/terms.json',
    'ta_app/fixtures/trainings.json',
    'administrators/fixtures/admindocuments.json',
    'administrators/fixtures/applicationreset.json',
    'administrators/fixtures/applications.json',
    'administrators/fixtures/applicationstatus.json',
    'administrators/fixtures/courses.json',
    'administrators/fixtures/emails.json',
    'administrators/fixtures/favourites.json',
    'administrators/fixtures/job_instructors.json',
    'administrators/fixtures/jobs.json',
    'administrators/fixtures/sessions.json',
    'users/fixtures/alertemails.json',
    'users/fixtures/alerts.json',
    'users/fixtures/confidentialities.json',
    'users/fixtures/profile_roles.json',
    'users/fixtures/profiles.json',
    'users/fixtures/users.json'
]


USERS = [ 'user2.admin', 'user56.ins', 'user100.test']
USER_IDS = [2, 56, 100]

PASSWORD = 'password'

SESSION = '2019-w1'
JOB = 'apbi-200-001-introduction-to-soil-science-w1'
APP = '2019-w1-apbi-200-001-introduction-to-soil-science-w1-application-by-user100test'
COURSE = 'apbi-200-001-introduction-to-soil-science-w'

CURRENT_NEXT = reverse('administrators:current_sessions') + '?page=2'
CURRENT_SESSION = '?next=' + CURRENT_NEXT + '&p=Current%20Sessions'
ARCHIVED_SESSION = '?next=' + reverse('administrators:archived_sessions') + '?page=2&p=Archived%20Sessions'

PREPARE_JOB = '?next=' + reverse('administrators:prepare_jobs') + '?page=2&p=Prepare%20Jobs'
INSTRUCTOR_JOB = '?next=' + reverse('administrators:instructor_jobs') + '?page=2&p=Jobs%20by%20Instructor'
STUDENT_JOB = '?next=' + reverse('administrators:student_jobs') + '?page=2&p=Jobs%20by%20Student&t=all'

DASHBOARD_APP = '?next=' + reverse('administrators:applications_dashboard') + '?page=2&p=Dashboard'
ALL_APP = '?next=' + reverse('administrators:all_applications') + '?page=2&p=All%20Applications'
SELECTED_APP = '?next=' + reverse('administrators:selected_applications') + '?page=2&p=Selected%20Applications'
OFFERED_APP = '?next=' + reverse('administrators:offered_applications') + '?page=2&p=Offered%20Applications'
ACCEPTED_APP = '?next=' + reverse('administrators:accepted_applications') + '?page=2&p=Accepted%20Applications'
DECLINED_APP = '?next=' + reverse('administrators:declined_applications') + '?page=2&p=Declined%20Applications'
TERMINATED_APP = '?next=' + reverse('administrators:terminated_applications') + '?page=2&p=Terminated%20Applications'

ALL_USER = '?next=' + reverse('administrators:all_users') + '?page=2&p=All%20Users&t=basic'
DASHBOARD_USER = '?next=' + reverse('administrators:applications_dashboard') + '?page=2&p=Dashboard&t=basic'


def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

class SessionTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        print('\nSession testing has started ==>')
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

    def test_view_url_exists_at_desired_location_ins(self):
        self.login(USERS[1], 'password')

        response = self.client.get( reverse('administrators:current_sessions') )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('administrators:show_session', args=[SESSION]) + CURRENT_SESSION )
        self.assertEqual(response.status_code, 403)

    def test_view_url_exists_at_desired_location_student(self):
        self.login(USERS[2], 'password')

        response = self.client.get( reverse('administrators:current_sessions') )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('administrators:show_session', args=[SESSION]) + CURRENT_SESSION )
        self.assertEqual(response.status_code, 403)

    def test_view_url_exists_at_desired_location_admin3(self):
        self.login('user3.admin', 'password')

        response = self.client.get( reverse('administrators:current_sessions') )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('administrators:show_session', args=[SESSION]) + CURRENT_SESSION )
        self.assertEqual(response.status_code, 403)

    def test_view_url_exists_at_desired_location_admin(self):
        self.login()

        response = self.client.get( reverse('administrators:current_sessions') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:archived_sessions') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:create_session') )
        self.assertEqual(response.status_code, 200)

        #response = self.client.get( reverse('administrators:create_session_setup_courses') )
        #self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:show_session', args=[SESSION]) + CURRENT_SESSION )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:edit_session', args=[SESSION]) + CURRENT_SESSION )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:show_session', args=[SESSION]) + ARCHIVED_SESSION )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:edit_session', args=[SESSION]) + ARCHIVED_SESSION )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:show_session', args=[SESSION]) + '?next=/app/administrators/sessions/currentt/&p=Current%20Sessions' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:edit_session', args=[SESSION]) + '?next=/app/administrators/sessions/archive/&p=Archived%20Sessions' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:show_report_applicants', args=[SESSION]) )
        self.assertEqual(response.status_code, 200)

        #response = self.client.get( reverse('administrators:show_report_summary', args=[SESSION]) )
        #self.assertEqual(response.status_code, 200)

    def test_show_session(self):
        print('- Test: show a session')
        self.login()

        session = adminApi.get_session(SESSION, 'slug')

        response = self.client.get(reverse('administrators:show_session', args=[session.slug]))
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse('administrators:show_session', args=[session.slug]) + '?nex=/administrators/sessions/current/?page=2&p=Current%20Session')
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse('administrators:show_session', args=[session.slug]) + '?next=/administrator/sessions/current/?page=2&p=Current%20Session')
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse('administrators:show_session', args=[session.slug]) + '?next=/administrators/sessions/current/&a=Current%20Sessions')
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse('administrators:show_session', args=[session.slug]) + '?next=/administrators/sessions/current/&p=Current%20Session')
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse('administrators:show_session', args=[session.slug]) + CURRENT_SESSION)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['session'].id, session.id)
        self.assertEqual(response.context['session'].slug, SESSION)
        self.assertEqual(response.context['next'], CURRENT_NEXT)


    def test_view_session_report_applicants(self):
        print('- Test: view a session report - applicants')
        self.login()

        client_session = self.client.session
        client_session['next_session'] = reverse('administrators:current_sessions') + '?page=1'
        client_session.save()

        session = adminApi.get_session(SESSION, 'slug')

        response = self.client.get(reverse('administrators:show_report_applicants', args=[session.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['session'].id, session.id)
        self.assertEqual(response.context['session'].slug, SESSION)
        self.assertEqual(response.context['total_applicants'], 5)
        self.assertEqual(response.context['next_session'], reverse('administrators:current_sessions') + '?page=1')
        self.assertEqual(response.context['back_to_word'], 'Current Sessions')

        applicants = [
            { 'username': 'user100.test', 'accepted_apps': ['APBI 200 001 (30.0 hours)'] },
            { 'username': 'user65.test', 'accepted_apps': [] },
            { 'username': 'user66.test', 'accepted_apps': ['APBI 260 001 (45.0 hours)'] },
            { 'username': 'user70.test', 'accepted_apps': ['APBI 200 002 (65.0 hours)'] },
            { 'username': 'user80.test', 'accepted_apps': [] }
        ]

        c = 0
        for applicant in response.context['applicants']:
            self.assertEqual(applicant.username, applicants[c]['username'])

            if len(applicant.accepted_apps) > 0:
                d = 0
                for accepted_app in applicant.accepted_apps:
                    self.assertEqual(accepted_app.job.course.code.name + ' ' + accepted_app.job.course.number.name + ' ' + accepted_app.job.course.section.name + ' ('+ str(accepted_app.accepted.assigned_hours) + ' hours)', applicants[c]['accepted_apps'][d])
                    d += 1
            c += 1


    def test_view_session_report_summary(self):
        print('- Test: view a session report - summary')

        self.login(USERS[2], PASSWORD)
        self.submit_confiential_information_international_complete(USERS[2])

        self.login('user66.test', PASSWORD)
        self.submit_confiential_information_international_complete('user66.test')

        self.login()

        client_session = self.client.session
        client_session['next_session'] = reverse('administrators:current_sessions') + '?page=1'
        client_session.save()

        session = adminApi.get_session(SESSION, 'slug')

        response = self.client.get(reverse('administrators:show_report_summary', args=[session.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['session'].id, session.id)
        self.assertEqual(response.context['session'].slug, SESSION)
        self.assertEqual( len(response.context['jobs']), 104)
        self.assertEqual(response.context['next_session'], reverse('administrators:current_sessions') + '?page=1')
        self.assertEqual(response.context['back_to_word'], 'Current Sessions')

        ta_hours_stat = {
            'total_lfs_grad': 1,
            'total_lfs_grad_ta_hours': 65.0,
            'total_others': 2,
            'total_others_ta_hours': 75.0
        }
        self.assertEqual(response.context['ta_hours_stat'], ta_hours_stat)

        jobs = response.context['jobs']
        self.assertEqual(len(jobs), 104)

        accepted_apps = [
            {
                'course': 'APBI 200 001',
                'instructors': 'User10 Ins,User56 Ins',
                'stat': {'lfs_grad': 0, 'lfs_grad_ta_hours': 0.0, 'others': 1, 'others_ta_hours': 30.0},
                'tas': 'User100 Test, 30.0, GTA I, $33.1, $248.25, International, Master student, Other Program - Master of Science in Statistics'
            },
            {
                'course': 'APBI 200 002',
                'instructors': 'User42 Ins',
                'stat': {'lfs_grad': 1, 'lfs_grad_ta_hours': 65.0, 'others': 0, 'others_ta_hours': 0.0},
                'tas': 'User70 Test, 65.0, GTA I, $33.1, $537.88, International, Ph.D student, Doctor of Philosophy in Soil Science (PhD)'
            },
            {
                'course': 'APBI 260 001',
                'instructors': 'User48 Ins',
                'stat': {'lfs_grad': 0, 'lfs_grad_ta_hours': 0.0, 'others': 1, 'others_ta_hours': 45.0},
                'tas': 'User66 Test, 45.0, GTA I, $33.1, $372.38, International, Undergraduate student, Other Program - Bachelor of Science, Mathematics'
            }
        ]

        for i in range(3):
            job = jobs[i]

            course = '{0} {1} {2}'.format( job.course.code.name, job.course.number.name, job.course.section.name )
            self.assertEqual(course, accepted_apps[i]['course'])

            instructors = [ins.first_name + ' ' + ins.last_name for ins in job.instructors.all()]
            self.assertEqual(','.join(instructors), accepted_apps[i]['instructors'])

            self.assertEqual(job.stat, accepted_apps[i]['stat'])

            tas = ''
            for app in job.accepted_apps:
                str = app.applicant.first_name + ' ' + app.applicant.last_name + ', '
                str += '{}, '.format(app.accepted.assigned_hours)
                str += app.classification.name + ', '
                str += '${}, '.format(app.classification.wage)
                str += '${}, '.format(app.salary)
                str += 'Domestic, ' if app.applicant.confidentiality.nationality == '0' else 'International, '
                str += app.applicant.profile.status.name + ', '
                str += 'Other Program - ' + app.applicant.profile.program_others if app.applicant.profile.program.slug == 'other' else app.applicant.profile.program.name
            tas += str

            self.assertEqual(tas, accepted_apps[i]['tas'])

        self.delete_document(USERS[2], ['sin', 'study_permit'], 'international')
        self.delete_document('user66.test', ['sin', 'study_permit'], 'international')


    def test_create_session_check_form_1(self):
        print('- Test: create a session - check form 1')
        self.login()

        data = {
            'year': '2020',
            'term': 2,
            'title': 'New TA Application',
            'description': 'new description',
            'note': 'new note',
            'is_visible': False,
            'is_archived': False
        }
        response = self.client.post(reverse('administrators:create_session'), data=urlencode(data), content_type=ContentType)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        session = self.client.session
        self.assertEqual(session['session_form_data'], data)

    def test_create_session_check_form_2(self):
        print('- Test: create a session - check form 2')
        self.login()

        data = {
            'year': '2020',
            'term': 2,
            'title': 'New TA Application',
            'description': 'new description',
            'note': 'new note',
            'is_visible': True,
            'is_archived': True
        }
        response = self.client.post(reverse('administrators:create_session'), data=urlencode(data), content_type=ContentType)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        session = self.client.session
        self.assertEqual(session['session_form_data'], {
            'year': '2020',
            'term': 2,
            'title': 'New TA Application',
            'description': 'new description',
            'note': 'new note',
            'is_visible': False,
            'is_archived': True
        })

    def test_create_session_check_form_3(self):
        print('- Test: create a session - check form 3')
        self.login()

        data = {
            'year': '2020',
            'term': 2,
            'title': 'New TA Application',
            'description': 'new description',
            'note': 'new note',
            'is_visible': True,
            'is_archived': False
        }
        response = self.client.post(reverse('administrators:create_session'), data=urlencode(data), content_type=ContentType)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        session = self.client.session
        self.assertEqual(session['session_form_data'], data)

    def test_create_session_check_form_4(self):
        print('- Test: create a session - check form 4')
        self.login()

        data = {
            'year': '2020',
            'term': 2,
            'title': 'New TA Application',
            'description': 'new description',
            'note': 'new note',
            'is_visible': False,
            'is_archived': True
        }
        response = self.client.post(reverse('administrators:create_session'), data=urlencode(data), content_type=ContentType)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        session = self.client.session
        self.assertEqual(session['session_form_data'], data)

    def test_create_session_check_form_5_year_error(self):
        print('- Test: create a session - check form 5 - year error')
        self.login()

        data = {
            'year': '',
            'term': 2,
            'title': 'New TA Application',
            'description': 'new description',
            'note': 'new note',
            'is_visible': False,
            'is_archived': False
        }
        response = self.client.post(reverse('administrators:create_session'), data=urlencode(data), content_type=ContentType)
        messages = self.messages(response)
        self.assertEqual(messages[0], 'An error occurred. Form is invalid. YEAR: This field is required.')

    def test_create_session_check_form_6_term_error(self):
        print('- Test: create a session - check form 6 - term error')
        self.login()

        data = {
            'year': '2020',
            'term': '',
            'title': 'New TA Application',
            'description': 'new description',
            'note': 'new note',
            'is_visible': False,
            'is_archived': False
        }
        response = self.client.post(reverse('administrators:create_session'), data=urlencode(data), content_type=ContentType)
        messages = self.messages(response)
        self.assertEqual(messages[0], 'An error occurred. Form is invalid. TERM: This field is required.')

    def test_create_session_check_form_7_term_error(self):
        print('- Test: create a session - check form 7 - term error')
        self.login()

        data = {
            'year': '2020',
            'term': 100,
            'title': 'New TA Application',
            'description': 'new description',
            'note': 'new note',
            'is_visible': False,
            'is_archived': False
        }
        response = self.client.post(reverse('administrators:create_session'), data=urlencode(data), content_type=ContentType)
        messages = self.messages(response)
        self.assertEqual(messages[0], 'An error occurred. Form is invalid. TERM: Select a valid choice. That choice is not one of the available choices.')

    def test_create_session_check_form_8_title_error(self):
        print('- Test: create a session - check form 8 - title error')
        self.login()

        data = {
            'year': '2020',
            'term': 2,
            'title': '',
            'description': 'new description',
            'note': 'new note',
            'is_visible': False,
            'is_archived': False
        }
        response = self.client.post(reverse('administrators:create_session'), data=urlencode(data), content_type=ContentType)
        messages = self.messages(response)
        self.assertEqual(messages[0], 'An error occurred. Form is invalid. TITLE: This field is required.')


    def test_create_session_setup_courses_error(self):
        print('- Test: create a session - setup_courses - error')
        self.login()

        data = {
            'year': '2020',
            'term': 2,
            'title': 'New TA Application',
            'description': 'new description',
            'note': 'new note',
            'is_visible': False,
            'is_archived': False
        }
        total_sessions = len( adminApi.get_sessions() )
        sessions = adminApi.get_sessions_by_year(data['year'])
        self.assertEqual( sessions.count(), 0 )

        response = self.client.post(reverse('administrators:create_session'), data=urlencode(data), content_type=ContentType)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        session = self.client.session
        self.assertEqual(session['session_form_data'], data)

        session['session_form_data'] = None
        session.save()

        res2 = self.client.get( reverse('administrators:create_session_setup_courses') )
        messages = self.messages(res2)
        self.assertEqual(messages[0], 'Oops! Something went wrong for some reason. No data found.')
        self.assertEqual(res2.status_code, 302)
        self.assertEqual(res2.url, reverse('administrators:create_session'))
        self.assertRedirects(res2, res2.url)


    def test_create_session_setup_courses_success(self):
        print('- Test: create a session - setup_courses - success')
        self.login()

        data = {
            'year': '2020',
            'term': 2,
            'title': 'New TA Application',
            'description': 'new description',
            'note': 'new note',
            'is_visible': False,
            'is_archived': False
        }
        total_sessions = len( adminApi.get_sessions() )
        sessions = adminApi.get_sessions_by_year(data['year'])
        self.assertEqual( sessions.count(), 0 )

        response = self.client.post(reverse('administrators:create_session'), data=urlencode(data), content_type=ContentType)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:create_session_setup_courses'))
        self.assertRedirects(response, response.url)

        session = self.client.session
        self.assertEqual(session['session_form_data'], data)

        res2 = self.client.get( reverse('administrators:create_session_setup_courses') )
        self.assertEqual(res2.context['session'], [('Year', '2020'), ('Term', 'Winter Term 1 (W1)'), ('Title', 'New TA Application'), ('Description', 'new description'), ('Note', 'new note'), ('Is visible', False), ('Is archived', False)])
        self.assertEqual(res2.context['term'].id, data['term'])
        self.assertEqual(len(res2.context['courses']), 106)


    def test_create_session_setup_courses_post_data_error(self):
        print('- Test: create a session - setup_courses - post data - error')
        self.login()

        data = {
            'year': '2020',
            'term': 2,
            'title': 'New TA Application',
            'description': 'new description',
            'note': 'new note',
            'is_visible': False,
            'is_archived': False
        }
        total_sessions = len( adminApi.get_sessions() )
        sessions = adminApi.get_sessions_by_year(data['year'])
        self.assertEqual( sessions.count(), 0 )

        response = self.client.post(reverse('administrators:create_session'), data=urlencode(data), content_type=ContentType)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:create_session_setup_courses'))
        self.assertRedirects(response, response.url)

        session = self.client.session
        self.assertEqual(session['session_form_data'], data)

        res2 = self.client.get( reverse('administrators:create_session_setup_courses') )
        self.assertEqual(res2.context['session'], [('Year', '2020'), ('Term', 'Winter Term 1 (W1)'), ('Title', 'New TA Application'), ('Description', 'new description'), ('Note', 'new note'), ('Is visible', False), ('Is archived', False)])
        self.assertEqual(res2.context['term'].id, data['term'])
        self.assertEqual(len(res2.context['courses']), 106)

        is_course_selected = []
        is_copied = []
        for course in res2.context['courses']:
            if course.id != 711:
                is_course_selected.append(course.id)
            if course.id != 470 and course.id != 272:
                is_copied.append(course.id)

        self.assertEqual(len(is_course_selected), 105)
        self.assertEqual(len(is_copied), 104)

        data3 = {
            'is_course_selected': is_course_selected,
            'id_copied': is_copied,
            'submit_path': ''
        }
        res3 = self.client.post( reverse('administrators:create_session_setup_courses'), data=urlencode(data3, True), content_type=ContentType)
        messages = self.messages(res3)
        self.assertEqual(messages[0], 'Oops! Something went wrong for some reason. No valid path found.')
        self.assertEqual(res3.status_code, 302)
        self.assertEqual(res3.url, reverse('administrators:create_session'))
        self.assertRedirects(res3, res3.url)

    def test_create_session_setup_courses_post_data_success(self):
        print('- Test: create a session - setup_courses - post data - success')
        self.login()

        data = {
            'year': '2020',
            'term': 2,
            'title': 'New TA Application',
            'description': 'new description',
            'note': 'new note',
            'is_visible': False,
            'is_archived': False
        }
        total_sessions = len( adminApi.get_sessions() )
        sessions = adminApi.get_sessions_by_year(data['year'])
        self.assertEqual( sessions.count(), 0 )

        response = self.client.post(reverse('administrators:create_session'), data=urlencode(data), content_type=ContentType)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:create_session_setup_courses'))
        self.assertRedirects(response, response.url)

        session = self.client.session
        self.assertEqual(session['session_form_data'], data)

        res2 = self.client.get( reverse('administrators:create_session_setup_courses') )
        self.assertEqual(res2.context['session'], [('Year', '2020'), ('Term', 'Winter Term 1 (W1)'), ('Title', 'New TA Application'), ('Description', 'new description'), ('Note', 'new note'), ('Is visible', False), ('Is archived', False)])
        self.assertEqual(res2.context['term'].id, data['term'])
        self.assertEqual(len(res2.context['courses']), 106)

        is_course_selected = []
        is_copied = []
        for course in res2.context['courses']:
            if course.id != 711:
                is_course_selected.append(course.id)
            if course.id != 470 and course.id != 272:
                is_copied.append(course.id)

        self.assertEqual(len(is_course_selected), 105)
        self.assertEqual(len(is_copied), 104)

        data3 = {
            'is_course_selected': is_course_selected,
            'is_copied': is_copied,
            'submit_path': 'Save Changes'
        }
        res3 = self.client.post( reverse('administrators:create_session_setup_courses'), data=urlencode(data3, True), content_type=ContentType)
        self.assertEqual(res3.status_code, 302)

        session2 = self.client.session
        self.assertEqual(session2['session_form_data']['year'], data['year'])
        self.assertEqual(session2['session_form_data']['term'], data['term'])
        self.assertEqual(session2['session_form_data']['title'], data['title'])
        self.assertEqual(session2['session_form_data']['description'], data['description'])
        self.assertEqual(session2['session_form_data']['note'], data['note'])
        self.assertFalse(session2['session_form_data']['is_visible'])
        self.assertFalse(session2['session_form_data']['is_archived'])

        self.assertEqual(res3.url, reverse('administrators:create_session_confirmation'))
        self.assertRedirects(res3, res3.url)


    def test_create_session_confirmation_error(self):
        print('- Test: create a session - confirmation - error')
        self.login()

        data = {
            'year': '2020',
            'term': 2,
            'title': 'New TA Application',
            'description': 'new description',
            'note': 'new note',
            'is_visible': False,
            'is_archived': False
        }
        total_sessions = len( adminApi.get_sessions() )
        sessions = adminApi.get_sessions_by_year(data['year'])
        self.assertEqual( sessions.count(), 0 )

        response = self.client.post(reverse('administrators:create_session'), data=urlencode(data), content_type=ContentType)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:create_session_setup_courses'))
        self.assertRedirects(response, response.url)

        session = self.client.session
        self.assertEqual(session['session_form_data'], data)

        res2 = self.client.get( reverse('administrators:create_session_setup_courses') )
        self.assertEqual(res2.context['session'], [('Year', '2020'), ('Term', 'Winter Term 1 (W1)'), ('Title', 'New TA Application'), ('Description', 'new description'), ('Note', 'new note'), ('Is visible', False), ('Is archived', False)])
        self.assertEqual(res2.context['term'].id, data['term'])
        self.assertEqual(len(res2.context['courses']), 106)

        is_course_selected = []
        is_copied = []
        for course in res2.context['courses']:
            if course.id != 711:
                is_course_selected.append(course.id)
            if course.id != 470 and course.id != 272:
                is_copied.append(course.id)

        self.assertEqual(len(is_course_selected), 105)
        self.assertEqual(len(is_copied), 104)

        data3 = {
            'is_course_selected': is_course_selected,
            'is_copied': is_copied,
            'submit_path': 'Save Changes'
        }
        res3 = self.client.post( reverse('administrators:create_session_setup_courses'), data=urlencode(data3, True), content_type=ContentType)
        self.assertEqual(res3.status_code, 302)

        session2 = self.client.session
        self.assertEqual(session2['session_form_data']['year'], data['year'])
        self.assertEqual(session2['session_form_data']['term'], data['term'])
        self.assertEqual(session2['session_form_data']['title'], data['title'])
        self.assertEqual(session2['session_form_data']['description'], data['description'])
        self.assertEqual(session2['session_form_data']['note'], data['note'])
        self.assertFalse(session2['session_form_data']['is_visible'])
        self.assertFalse(session2['session_form_data']['is_archived'])

        self.assertEqual(res3.url, reverse('administrators:create_session_confirmation'))
        self.assertRedirects(res3, res3.url)

        session2['session_form_data'] = []
        session2.save()

        res4 = self.client.get( reverse('administrators:create_session_confirmation') )
        messages = self.messages(res4)
        self.assertEqual(messages[0], 'Oops! Something went wrong for some reason. No data found.')
        self.assertEqual(res4.status_code, 302)
        self.assertEqual(res4.url, reverse('administrators:create_session_setup_courses'))
        #self.assertRedirects(res4, res4.url)


    def test_create_session_confirmation_error(self):
        print('- Test: create a session - confirmation - error')
        self.login()

        data = {
            'year': '2020',
            'term': 2,
            'title': 'New TA Application',
            'description': 'new description',
            'note': 'new note',
            'is_visible': False,
            'is_archived': False
        }
        total_sessions = len( adminApi.get_sessions() )
        sessions = adminApi.get_sessions_by_year(data['year'])
        self.assertEqual( sessions.count(), 0 )

        response = self.client.post(reverse('administrators:create_session'), data=urlencode(data), content_type=ContentType)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:create_session_setup_courses'))
        self.assertRedirects(response, response.url)

        session = self.client.session
        self.assertEqual(session['session_form_data'], data)

        res2 = self.client.get( reverse('administrators:create_session_setup_courses') )
        self.assertEqual(res2.context['session'], [('Year', '2020'), ('Term', 'Winter Term 1 (W1)'), ('Title', 'New TA Application'), ('Description', 'new description'), ('Note', 'new note'), ('Is visible', False), ('Is archived', False)])
        self.assertEqual(res2.context['term'].id, data['term'])
        self.assertEqual(len(res2.context['courses']), 106)

        is_course_selected = []
        is_copied = []
        for course in res2.context['courses']:
            if course.id != 711:
                is_course_selected.append(course.id)
            if course.id != 470 and course.id != 272:
                is_copied.append(course.id)

        self.assertEqual(len(is_course_selected), 105)
        self.assertEqual(len(is_copied), 104)

        data3 = {
            'is_course_selected': is_course_selected,
            'is_copied': is_copied,
            'submit_path': 'Save Changes'
        }
        res3 = self.client.post( reverse('administrators:create_session_setup_courses'), data=urlencode(data3, True), content_type=ContentType)
        self.assertEqual(res3.status_code, 302)

        session2 = self.client.session
        self.assertEqual(session2['session_form_data']['year'], data['year'])
        self.assertEqual(session2['session_form_data']['term'], data['term'])
        self.assertEqual(session2['session_form_data']['title'], data['title'])
        self.assertEqual(session2['session_form_data']['description'], data['description'])
        self.assertEqual(session2['session_form_data']['note'], data['note'])
        self.assertFalse(session2['session_form_data']['is_visible'])
        self.assertFalse(session2['session_form_data']['is_archived'])

        self.assertEqual(res3.url, reverse('administrators:create_session_confirmation'))
        self.assertRedirects(res3, res3.url)

        res4 = self.client.get( reverse('administrators:create_session_confirmation') )
        self.assertEqual(res4.context['session'], [('Year', '2020'), ('Term', 'Winter Term 1 (W1)'), ('Title', 'New TA Application'), ('Description', 'new description'), ('Note', 'new note'), ('Is visible', False), ('Is archived', False)])
        self.assertEqual(res4.context['term'].id, data['term'])
        self.assertEqual(len(res4.context['courses']), 105)
        self.assertEqual(res4.context['num_courses'], 105)
        self.assertEqual(res4.context['num_copied_ids'], 104)

        session3 = self.client.session
        session3['session_form_data']['selected_jobs'] = []
        session3.save()

        data4 = {}
        res4 = self.client.post( reverse('administrators:create_session_confirmation'), data=urlencode(data4), content_type=ContentType)
        messages = self.messages(res4)
        self.assertEqual(messages[0], 'Oops! Something went wrong for some reason. No data found.')
        self.assertEqual(res4.status_code, 302)
        self.assertEqual(res4.url, reverse('administrators:create_session_setup_courses'))
        self.assertRedirects(res4, res4.url)


    def test_create_session_confirmation_with_copy_success(self):
        print('- Test: create a session - confirmation with copy - success')
        self.login()

        data = {
            'year': '2020',
            'term': 2,
            'title': 'New TA Application',
            'description': 'new description',
            'note': 'new note',
            'is_visible': False,
            'is_archived': False
        }
        total_sessions = len( adminApi.get_sessions() )
        sessions = adminApi.get_sessions_by_year(data['year'])
        self.assertEqual( sessions.count(), 0 )

        response = self.client.post(reverse('administrators:create_session'), data=urlencode(data), content_type=ContentType)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:create_session_setup_courses'))
        self.assertRedirects(response, response.url)

        session = self.client.session
        self.assertEqual(session['session_form_data'], data)

        res2 = self.client.get( reverse('administrators:create_session_setup_courses') )
        self.assertEqual(res2.context['session'], [('Year', '2020'), ('Term', 'Winter Term 1 (W1)'), ('Title', 'New TA Application'), ('Description', 'new description'), ('Note', 'new note'), ('Is visible', False), ('Is archived', False)])
        self.assertEqual(res2.context['term'].id, data['term'])
        self.assertEqual(len(res2.context['courses']), 106)

        is_course_selected = []
        is_copied = []
        for course in res2.context['courses']:
            if course.id != 711:
                is_course_selected.append(course.id)
                if course.id != 272 and course.id != 470 and course.id != 710:
                    is_copied.append(course.id)

        self.assertEqual(len(is_course_selected), 105)
        self.assertEqual(len(is_copied), 102)

        data3 = {
            'is_course_selected': is_course_selected,
            'is_copied': is_copied,
            'submit_path': 'Save Changes'
        }
        res3 = self.client.post( reverse('administrators:create_session_setup_courses'), data=urlencode(data3, True), content_type=ContentType)
        self.assertEqual(res3.status_code, 302)

        session2 = self.client.session
        self.assertEqual(session2['session_form_data']['year'], data['year'])
        self.assertEqual(session2['session_form_data']['term'], data['term'])
        self.assertEqual(session2['session_form_data']['title'], data['title'])
        self.assertEqual(session2['session_form_data']['description'], data['description'])
        self.assertEqual(session2['session_form_data']['note'], data['note'])
        self.assertFalse(session2['session_form_data']['is_visible'])
        self.assertFalse(session2['session_form_data']['is_archived'])

        self.assertEqual(res3.url, reverse('administrators:create_session_confirmation'))
        self.assertRedirects(res3, res3.url)

        res4 = self.client.get( reverse('administrators:create_session_confirmation') )
        self.assertEqual(res4.context['session'], [('Year', '2020'), ('Term', 'Winter Term 1 (W1)'), ('Title', 'New TA Application'), ('Description', 'new description'), ('Note', 'new note'), ('Is visible', False), ('Is archived', False)])
        self.assertEqual(res4.context['term'].id, data['term'])
        self.assertEqual(len(res4.context['courses']), 105)
        self.assertEqual(res4.context['num_courses'], 105)
        self.assertEqual(res4.context['num_copied_ids'], 102)

        session3 = self.client.session
        self.assertTrue('selected_jobs' in session3['session_form_data'])
        self.assertTrue(len(session3['session_form_data']['selected_jobs']), 105)

        selected_jobs = session3['session_form_data']['selected_jobs']

        data4 = {}
        res4 = self.client.post( reverse('administrators:create_session_confirmation'), data=urlencode(data4), content_type=ContentType)
        messages = self.messages(res4)
        self.assertEqual(messages[0], 'Success! 2020 W1 - New TA Application created')
        self.assertEqual(res4.status_code, 302)
        self.assertEqual(res4.url, reverse('administrators:current_sessions'))
        self.assertRedirects(res4, res4.url)

        sessions = adminApi.get_sessions_by_year(data['year'])
        self.assertEqual( sessions.count(), 1 )
        self.assertEqual( len(adminApi.get_sessions()), total_sessions + 1 )

        sess = adminApi.get_session('2020-w1', 'slug')
        self.assertEqual(sess.year, data['year'])
        self.assertEqual(sess.term.code, 'W1')
        self.assertEqual(sess.term.name, 'Winter Term 1')
        self.assertEqual(sess.title, data['title'])
        self.assertEqual(sess.description, data['description'])
        self.assertEqual(sess.is_visible, data['is_visible'])
        self.assertEqual(sess.is_archived, data['is_archived'])
        self.assertEqual(sess.job_set.count(), 105)

        jobs = sess.job_set.all()
        flag = False
        for job in jobs:
            if job.course.id == 711:
                flag = True
                break
        self.assertFalse(flag)

        selected_job_26 = None
        selected_job_260 = None
        selected_job_272 = None
        selected_job_470 = None
        for j in selected_jobs:
            if j['id'] == 26: selected_job_26 = j
            if j['id'] == 260: selected_job_260 = j
            if j['id'] == 272: selected_job_272 = j
            if j['id'] == 470: selected_job_470 = j

        self.assertIsNotNone(selected_job_260)
        self.assertIsNotNone(selected_job_272)
        self.assertIsNotNone(selected_job_470)

        job_26 = adminApi.get_job_by_session_id_and_course_id(sess.id, 26)
        self.assertEqual(job_26.course.id, selected_job_26['id'])
        self.assertEqual([inst.id for inst in job_26.instructors.all()], selected_job_26['instructors'])
        self.assertEqual(job_26.assigned_ta_hours, selected_job_26['assigned_ta_hours'])
        self.assertEqual(job_26.course_overview, selected_job_26['course_overview'])
        self.assertEqual(job_26.description, selected_job_26['description'])
        self.assertEqual(job_26.note, selected_job_26['note'])
        self.assertEqual(job_26.is_active, selected_job_26['is_active'])

        job_260 = adminApi.get_job_by_session_id_and_course_id(sess.id, 260)
        self.assertEqual(job_260.course.id, selected_job_260['id'])
        self.assertEqual([inst.id for inst in job_260.instructors.all()], selected_job_260['instructors'])
        self.assertEqual(job_260.assigned_ta_hours, selected_job_260['assigned_ta_hours'])
        self.assertEqual(job_260.course_overview, selected_job_260['course_overview'])
        self.assertEqual(job_260.description, selected_job_260['description'])
        self.assertEqual(job_260.note, selected_job_260['note'])
        self.assertEqual(job_260.is_active, selected_job_260['is_active'])

        job_272 = adminApi.get_job_by_session_id_and_course_id(sess.id, 272)
        self.assertEqual(job_272.course.id, selected_job_272['id'])
        self.assertEqual([inst.id for inst in job_272.instructors.all()], selected_job_272['instructors'])
        self.assertEqual(job_272.assigned_ta_hours, selected_job_272['assigned_ta_hours'])
        self.assertEqual(job_272.course_overview, selected_job_272['course_overview'])
        self.assertEqual(job_272.description, selected_job_272['description'])
        self.assertEqual(job_272.note, selected_job_272['note'])
        self.assertEqual(job_272.is_active, selected_job_272['is_active'])

        job_470 = adminApi.get_job_by_session_id_and_course_id(sess.id, 470)
        self.assertEqual(job_470.course.id, selected_job_470['id'])
        self.assertEqual([inst.id for inst in job_470.instructors.all()], selected_job_470['instructors'])
        self.assertEqual(job_470.assigned_ta_hours, selected_job_470['assigned_ta_hours'])
        self.assertEqual(job_470.course_overview, selected_job_470['course_overview'])
        self.assertEqual(job_470.description, selected_job_470['description'])
        self.assertEqual(job_470.note, selected_job_470['note'])
        self.assertEqual(job_470.is_active, selected_job_470['is_active'])

        session4 = self.client.session
        self.assertFalse('session_form_data' in session4)


    def test_create_session_confirmation_without_copy_success(self):
        print('- Test: create a session - confirmation without copy - success')
        self.login()

        data = {
            'year': '2020',
            'term': 2,
            'title': 'New TA Application',
            'description': 'new description',
            'note': 'new note',
            'is_visible': False,
            'is_archived': False
        }

        total_sessions = len( adminApi.get_sessions() )
        sessions = adminApi.get_sessions_by_year(data['year'])
        self.assertEqual( sessions.count(), 0 )

        response = self.client.post(reverse('administrators:create_session'), data=urlencode(data), content_type=ContentType)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:create_session_setup_courses'))
        self.assertRedirects(response, response.url)

        session = self.client.session
        self.assertEqual(session['session_form_data'], data)

        res2 = self.client.get( reverse('administrators:create_session_setup_courses') )
        self.assertEqual(res2.context['session'], [('Year', '2020'), ('Term', 'Winter Term 1 (W1)'), ('Title', 'New TA Application'), ('Description', 'new description'), ('Note', 'new note'), ('Is visible', False), ('Is archived', False)])
        self.assertEqual(res2.context['term'].id, data['term'])
        self.assertEqual(len(res2.context['courses']), 106)

        is_course_selected = []
        is_copied = []
        for course in res2.context['courses']:
            is_course_selected.append(course.id)
            if course.id != 272 and course.id != 470:
                is_copied.append(course.id)

        self.assertEqual(len(is_course_selected), 106)
        self.assertEqual(len(is_copied), 104)

        data3 = {
            'is_course_selected': is_course_selected,
            'is_copied': is_copied,
            'submit_path': 'Save without Copy'
        }
        res3 = self.client.post( reverse('administrators:create_session_setup_courses'), data=urlencode(data3, True), content_type=ContentType)
        self.assertEqual(res3.status_code, 302)

        session2 = self.client.session
        self.assertEqual(session2['session_form_data']['year'], data['year'])
        self.assertEqual(session2['session_form_data']['term'], data['term'])
        self.assertEqual(session2['session_form_data']['title'], data['title'])
        self.assertEqual(session2['session_form_data']['description'], data['description'])
        self.assertEqual(session2['session_form_data']['note'], data['note'])
        self.assertFalse(session2['session_form_data']['is_visible'])
        self.assertFalse(session2['session_form_data']['is_archived'])

        self.assertEqual(res3.url, reverse('administrators:create_session_confirmation'))
        self.assertRedirects(res3, res3.url)

        res4 = self.client.get( reverse('administrators:create_session_confirmation') )
        self.assertEqual(res4.context['session'], [('Year', '2020'), ('Term', 'Winter Term 1 (W1)'), ('Title', 'New TA Application'), ('Description', 'new description'), ('Note', 'new note'), ('Is visible', False), ('Is archived', False)])
        self.assertEqual(res4.context['term'].id, data['term'])
        self.assertEqual(len(res4.context['courses']), 106)
        self.assertEqual(res4.context['num_courses'], 106)
        self.assertEqual(res4.context['num_copied_ids'], 0)

        session3 = self.client.session
        self.assertTrue('selected_jobs' in session3['session_form_data'])
        self.assertEqual(len(session3['session_form_data']['selected_jobs']), 106)

        selected_jobs = session3['session_form_data']['selected_jobs']

        data5 = {}
        res5 = self.client.post( reverse('administrators:create_session_confirmation'), data=urlencode(data5), content_type=ContentType)
        messages5 = self.messages(res5)
        self.assertEqual(messages5[0], 'Success! 2020 W1 - New TA Application created')
        self.assertEqual(res5.status_code, 302)
        self.assertEqual(res5.url, reverse('administrators:current_sessions'))
        self.assertRedirects(res5, res5.url)

        sessions = adminApi.get_sessions_by_year(data['year'])
        self.assertEqual( sessions.count(), 1 )
        self.assertEqual( len(adminApi.get_sessions()), total_sessions + 1 )

        sess = adminApi.get_session('2020-w1', 'slug')
        self.assertEqual(sess.year, data['year'])
        self.assertEqual(sess.term.code, 'W1')
        self.assertEqual(sess.term.name, 'Winter Term 1')
        self.assertEqual(sess.title, data['title'])
        self.assertEqual(sess.description, data['description'])
        self.assertEqual(sess.is_visible, data['is_visible'])
        self.assertEqual(sess.is_archived, data['is_archived'])
        self.assertEqual(sess.job_set.count(), 106)

        selected_job_26 = None
        selected_job_260 = None
        selected_job_272 = None
        selected_job_470 = None
        selected_job_711 = None
        for j in selected_jobs:
            if j['id'] == 26: selected_job_26 = j
            if j['id'] == 260: selected_job_260 = j
            if j['id'] == 272: selected_job_272 = j
            if j['id'] == 470: selected_job_470 = j
            if j['id'] == 711: selected_job_711 = j

        self.assertIsNotNone(selected_job_260)
        self.assertIsNotNone(selected_job_272)
        self.assertIsNotNone(selected_job_470)
        self.assertIsNotNone(selected_job_711)

        job_26 = adminApi.get_job_by_session_id_and_course_id(sess.id, 26)
        self.assertEqual(job_26.course.id, selected_job_26['id'])
        self.assertEqual([inst.id for inst in job_26.instructors.all()], selected_job_26['instructors'])
        self.assertEqual(job_26.assigned_ta_hours, selected_job_26['assigned_ta_hours'])
        self.assertEqual(job_26.course_overview, selected_job_26['course_overview'])
        self.assertEqual(job_26.description, selected_job_26['description'])
        self.assertEqual(job_26.note, selected_job_26['note'])
        self.assertEqual(job_26.is_active, selected_job_26['is_active'])

        self.assertEqual(job_26.instructors.count(), 0)
        self.assertEqual(job_26.assigned_ta_hours, 0.0)
        self.assertTrue(job_26.is_active)

        job_260 = adminApi.get_job_by_session_id_and_course_id(sess.id, 260)
        self.assertEqual(job_260.course.id, selected_job_260['id'])
        self.assertEqual([inst.id for inst in job_260.instructors.all()], selected_job_260['instructors'])
        self.assertEqual(job_260.assigned_ta_hours, selected_job_260['assigned_ta_hours'])
        self.assertEqual(job_260.course_overview, selected_job_260['course_overview'])
        self.assertEqual(job_260.description, selected_job_260['description'])
        self.assertEqual(job_260.note, selected_job_260['note'])
        self.assertEqual(job_260.is_active, selected_job_260['is_active'])

        self.assertEqual(job_260.instructors.count(), 0)
        self.assertEqual(job_260.assigned_ta_hours, 0.0)
        self.assertTrue(job_260.is_active)

        job_272 = adminApi.get_job_by_session_id_and_course_id(sess.id, 272)
        self.assertEqual(job_272.course.id, selected_job_272['id'])
        self.assertEqual([inst.id for inst in job_272.instructors.all()], selected_job_272['instructors'])
        self.assertEqual(job_272.assigned_ta_hours, selected_job_272['assigned_ta_hours'])
        self.assertEqual(job_272.course_overview, selected_job_272['course_overview'])
        self.assertEqual(job_272.description, selected_job_272['description'])
        self.assertEqual(job_272.note, selected_job_272['note'])
        self.assertEqual(job_272.is_active, selected_job_272['is_active'])

        self.assertEqual(job_272.instructors.count(), 0)
        self.assertEqual(job_272.assigned_ta_hours, 0.0)
        self.assertIsNone(job_272.course_overview)
        self.assertIsNone(job_272.description)
        self.assertIsNone(job_272.note)
        self.assertTrue(job_272.is_active)

        job_470 = adminApi.get_job_by_session_id_and_course_id(sess.id, 470)
        self.assertEqual(job_470.course.id, selected_job_470['id'])
        self.assertEqual([inst.id for inst in job_470.instructors.all()], selected_job_470['instructors'])
        self.assertEqual(job_470.assigned_ta_hours, selected_job_470['assigned_ta_hours'])
        self.assertEqual(job_470.course_overview, selected_job_470['course_overview'])
        self.assertEqual(job_470.description, selected_job_470['description'])
        self.assertEqual(job_470.note, selected_job_470['note'])
        self.assertEqual(job_470.is_active, selected_job_470['is_active'])

        self.assertEqual(job_470.instructors.count(), 0)
        self.assertEqual(job_470.assigned_ta_hours, 0.0)
        self.assertIsNone(job_470.course_overview)
        self.assertIsNone(job_470.description)
        self.assertIsNone(job_470.note)
        self.assertTrue(job_470.is_active)

        job_711 = adminApi.get_job_by_session_id_and_course_id(sess.id, 711)
        self.assertEqual(job_711.course.id, selected_job_711['id'])
        self.assertEqual([inst.id for inst in job_711.instructors.all()], selected_job_711['instructors'])
        self.assertEqual(job_711.assigned_ta_hours, selected_job_711['assigned_ta_hours'])
        self.assertEqual(job_711.course_overview, selected_job_711['course_overview'])
        self.assertEqual(job_711.description, selected_job_711['description'])
        self.assertEqual(job_711.note, selected_job_711['note'])
        self.assertEqual(job_711.is_active, selected_job_711['is_active'])

        self.assertEqual(job_711.instructors.count(), 0)
        self.assertEqual(job_711.assigned_ta_hours, 0.0)
        self.assertTrue(job_711.is_active)

        session4 = self.client.session
        self.assertFalse('session_form_data' in session4)


    def test_create_existing_session(self):
        print('- Test: create an existing session for checking duplicates')
        self.login()

        data = {
            'year': '2019',
            'term': '2',
            'title': 'New TA Application',
            'description': 'new description',
            'note': 'new note'
        }
        response = self.client.post(reverse('administrators:create_session'), data=urlencode(data), content_type=ContentType)
        messages = self.messages(response)
        self.assertEqual(messages[0], 'An error occurred. Form is invalid. ALL  : Session with this Year and Term already exists.')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:create_session'))
        self.assertRedirects(response, response.url)


    def test_delete_session(self):
        print('- Test: delete a session')
        self.login()
        session_id = '6'
        session = adminApi.get_session(session_id)
        data = {
            'session': session_id,
            'next': CURRENT_NEXT
        }
        response = self.client.post(reverse('administrators:delete_session_confirmation', args=[session.slug]) + CURRENT_SESSION, data=urlencode(data), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)
        self.assertFalse( adminApi.session_exists(session_id) )


    def test_delete_not_existing_sessinon(self):
        print('- Test: delete a not existing session')
        self.login()

        data = {
            'session': '1000',
            'next': CURRENT_NEXT
        }
        response = self.client.post(reverse('administrators:delete_session_confirmation', args=['2019-w9']) + CURRENT_SESSION, data=urlencode(data), content_type=ContentType)
        self.assertEqual(response.status_code, 404)


    def test_edit_session(self):
        print('- Test: edit a session')
        self.login()
        session_id = '6'
        session = adminApi.get_session(session_id)
        courses = adminApi.get_courses_by_term('6')

        data1 = {
            'session': session_id,
            'year': '2019',
            'term': '6',
            'title': 'Edited TA Application',
            'description': 'Edited description',
            'note': 'Edited note',
            'is_visible': 'True',
            'courses': [ str(courses[0].id), str(courses[1].id) ],
            'next': '/administrators/sessions/currentt/?page=2'
        }
        response = self.client.post(reverse('administrators:edit_session', args=[session.slug]) + CURRENT_SESSION, data=urlencode(data1, True), content_type=ContentType)
        self.assertEqual(response.status_code, 404)

        data2 = {
            'session': session_id,
            'year': '2019',
            'term': '6',
            'title': 'Edited TA Application',
            'description': 'Edited description',
            'note': 'Edited note',
            'is_visible': 'True',
            'courses': [ str(courses[0].id), str(courses[1].id) ],
            'next': CURRENT_NEXT
        }
        response = self.client.post(reverse('administrators:edit_session', args=[session.slug]) + CURRENT_SESSION, data=urlencode(data2, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:current_sessions') + '?page=2')
        self.assertRedirects(response, response.url)

        updated_session = adminApi.get_session(session_id)
        self.assertEqual( updated_session.id, int(data2['session']) )
        self.assertEqual( updated_session.year, data2['year'] )
        self.assertEqual( updated_session.title, data2['title'] )
        self.assertEqual( updated_session.description, data2['description'] )
        self.assertEqual( updated_session.note, data2['note'] )
        self.assertEqual( updated_session.is_visible, eval(data2['is_visible']) )
        self.assertEqual( updated_session.job_set.count(), len(data2['courses']) )

    def test_edit_not_existing_session(self):
        print('- Test: edit a not existing session')
        self.login()

        session_id = '1116'
        data = {
            'session': session_id,
            'year': '2019',
            'term': '6',
            'title': 'Edited TA Application',
            'description': 'Edited description',
            'note': 'Edited note',
            'is_visible': 'True',
            'courses': [],
            'next': CURRENT_NEXT
        }

        response = self.client.post(reverse('administrators:edit_session', args=['2019-w9']) + CURRENT_SESSION, data=urlencode(data, True), content_type=ContentType)
        self.assertEqual(response.status_code, 404)

    def test_remove_courses_in_session(self):
        print('- Test: remove courses in a session')
        self.login()

        session_id = '5'
        term_id = '3'
        session = adminApi.get_session(session_id)
        courses = adminApi.get_courses_by_term(term_id)
        num_courses = len(courses)

        course_ids = []
        for course in courses:
            if course.id != 3 and course.id != 27: course_ids.append(str(course.id))

        data = {
            'session': session_id,
            'year': session.year,
            'term': term_id,
            'title': 'Edited TA Application',
            'description': 'Edited description',
            'note': 'Edited note',
            'is_visible': 'True',
            'courses': course_ids,
            'next': CURRENT_NEXT
        }

        response = self.client.post(reverse('administrators:edit_session', args=[session.slug]) + CURRENT_SESSION, data=urlencode(data, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        updated_session = adminApi.get_session(session_id)
        self.assertEqual( updated_session.id, int(data['session']) )
        self.assertEqual( updated_session.year, data['year'] )
        self.assertEqual( updated_session.title, data['title'] )
        self.assertEqual( updated_session.description, data['description'] )
        self.assertEqual( updated_session.note, data['note'] )
        self.assertEqual( updated_session.is_visible, eval(data['is_visible']) )
        self.assertEqual( updated_session.job_set.count(), len(data['courses']) )
        self.assertEqual( updated_session.job_set.count(), num_courses-2)

        # re-enter courses

        data = {
            'session': session_id,
            'year': session.year,
            'term': term_id,
            'title': 'Edited TA Application',
            'description': 'Edited description',
            'note': 'Edited note',
            'is_visible': 'True',
            'courses': [ str(course.id) for course in courses ],
            'next': CURRENT_NEXT
        }

        response = self.client.post(reverse('administrators:edit_session', args=[session.slug]) + CURRENT_SESSION, data=urlencode(data, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        updated_session = adminApi.get_session(session_id)
        self.assertEqual( updated_session.id, int(data['session']) )
        self.assertEqual( updated_session.year, data['year'] )
        self.assertEqual( updated_session.title, data['title'] )
        self.assertEqual( updated_session.description, data['description'] )
        self.assertEqual( updated_session.note, data['note'] )
        self.assertEqual( updated_session.is_visible, eval(data['is_visible']) )
        self.assertEqual( updated_session.job_set.count(), len(data['courses']) )
        self.assertEqual( updated_session.job_set.count(), num_courses)

    def test_add_empty_courses_in_session(self):
        print('- Test: add empty courses in a session')
        self.login()

        session_id = '5'
        term_id = '3'
        session = adminApi.get_session(session_id)

        data = {
            'session': session_id,
            'year': session.year,
            'term': term_id,
            'title': 'Edited TA Application',
            'description': 'Edited description',
            'note': 'Edited note',
            'is_visible': 'True',
            'courses': [],
            'next': CURRENT_NEXT
        }

        response = self.client.post(reverse('administrators:edit_session', args=[session.slug]) + CURRENT_SESSION, data=urlencode(data, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)
