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

LOGIN_URL = '/accounts/local_login/'
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

    def test_view_url_exists_at_desired_location(self):
        self.login(USERS[1], 'password')

        response = self.client.get( reverse('administrators:current_sessions') )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('administrators:show_session', args=[SESSION]) + CURRENT_SESSION )
        self.assertEqual(response.status_code, 403)

        self.login(USERS[2], 'password')

        response = self.client.get( reverse('administrators:current_sessions') )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('administrators:show_session', args=[SESSION]) + CURRENT_SESSION )
        self.assertEqual(response.status_code, 403)

        self.login('user3.admin', 'password')

        response = self.client.get( reverse('administrators:current_sessions') )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('administrators:show_session', args=[SESSION]) + CURRENT_SESSION )
        self.assertEqual(response.status_code, 403)

        self.login()

        response = self.client.get( reverse('administrators:current_sessions') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:archived_sessions') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:create_session') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:create_session_confirmation') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:show_session', args=[SESSION]) + CURRENT_SESSION )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:edit_session', args=[SESSION]) + CURRENT_SESSION )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:show_session', args=[SESSION]) + ARCHIVED_SESSION )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:edit_session', args=[SESSION]) + ARCHIVED_SESSION )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:show_session', args=[SESSION]) + '?next=/administrators/sessions/currentt/&p=Current%20Sessions' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:edit_session', args=[SESSION]) + '?next=/administrators/sessions/archive/&p=Archived%20Sessions' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:show_report_applicants', args=[SESSION]) )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:show_report_summary', args=[SESSION]) )
        self.assertEqual(response.status_code, 200)

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

        jobs = response.context['jobs']

        accepted_apps = [
            { 'course': 'APBI 200 001', 'instructors': 'User10 Ins,User56 Ins', 'tas': 'User100 Test, 30.0, GTA I, $33.1, $248.25, International, Other Program - Master of Science in Statistics' },
            { 'course': 'APBI 200 002', 'instructors': 'User42 Ins', 'tas': 'User70 Test, 65.0, GTA I, $33.1, $537.88, International, Doctor of Philosophy in Soil Science (PhD)' }
        ]

        for i in range(2):
            job = jobs[i]

            course = '{0} {1} {2}'.format( job.course.code.name, job.course.number.name, job.course.section.name )
            self.assertEqual(course, accepted_apps[i]['course'])

            instructors = [ins.first_name + ' ' + ins.last_name for ins in job.instructors.all()]
            self.assertEqual(','.join(instructors), accepted_apps[i]['instructors'])

            tas = ''
            for app in job.accepted_apps:
                str = app.applicant.first_name + ' ' + app.applicant.last_name + ', '
                str += '{}, '.format(app.accepted.assigned_hours)
                str += app.classification.name + ', '
                str += '${}, '.format(app.classification.wage)
                str += '${}, '.format(app.salary)
                str += 'Domestic, ' if app.applicant.confidentiality.nationality == '0' else 'International, '
                str += 'Other Program - ' + app.applicant.profile.program_others if app.applicant.profile.program.slug == 'other' else app.applicant.profile.program.name
            tas += str

            self.assertEqual(tas, accepted_apps[i]['tas'])

        self.delete_document(USERS[2], ['sin', 'study_permit'], 'international')


    def test_create_session(self):
        print('- Test: create a session')
        self.login()
        data = {
            'year': '2020',
            'term': '2',
            'title': 'New TA Application',
            'description': 'new description',
            'note': 'new note'
        }
        total_sessions = len( adminApi.get_sessions() )
        sessions = adminApi.get_sessions_by_year(data['year'])
        self.assertEqual( sessions.count(), 0 )

        response = self.client.post(reverse('administrators:create_session'), data=urlencode(data), content_type=ContentType)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(response.url)
        self.assertEqual( len(response.context['error_messages']), 0)
        session = self.client.session
        self.assertEqual(session['session_form_data'], data)
        self.assertEqual(response.context['courses'].count(), 104)

        data['courses'] = [ str(course.id) for course in response.context['courses'] ]
        data['is_visible'] = False
        data['is_archived'] = False
        response = self.client.post(reverse('administrators:create_session_confirmation'), data=urlencode(data, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        sessions = adminApi.get_sessions_by_year(data['year'])
        self.assertEqual( sessions.count(), 1 )
        self.assertEqual( len(adminApi.get_sessions()), total_sessions + 1 )
        self.assertEqual(sessions[0].year, data['year'])
        self.assertEqual(sessions[0].term.code, 'W1')
        self.assertEqual(sessions[0].term.name, 'Winter Term 1')
        self.assertEqual(sessions[0].title, data['title'])
        self.assertEqual(sessions[0].description, data['description'])
        self.assertEqual(sessions[0].is_visible, data['is_visible'])
        self.assertEqual(sessions[0].is_archived, data['is_archived'])
        self.assertEqual(sessions[0].job_set.count(), 104)


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
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(response.url)
        self.assertEqual(response.context['error_messages'], ['Session with this Year and Term already exists.'])

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
