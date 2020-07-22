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
    'administrators/fixtures/applications.json',
    'administrators/fixtures/applicationstatus.json',
    'administrators/fixtures/courses.json',
    'administrators/fixtures/emails.json',
    'administrators/fixtures/favourites.json',
    'administrators/fixtures/job_instructors.json',
    'administrators/fixtures/jobs.json',
    'administrators/fixtures/sessions.json',
    'users/fixtures/profile_roles.json',
    'users/fixtures/profiles.json',
    'users/fixtures/users.json'
]


USERS = [ 'user2.admin', 'User56.Ins', 'user100.test']
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


class SessionTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        print('\nSession testing has started ==>')
        cls.user = userApi.get_user(USERS[0], 'username')

    def login(self, username=None, password=None):
        if username and password:
            self.client.post(LOGIN_URL, data={'username': username, 'password': password})
        else:
            self.client.post(LOGIN_URL, data={'username': self.user.username, 'password': PASSWORD})

    def messages(self, res):
        return [m.message for m in get_messages(res.wsgi_request)]

    def test_view_url_exists_at_desired_location(self):
        self.login(USERS[1], 'password')

        response = self.client.get( reverse('administrators:current_sessions') )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('administrators:show_session', args=['2019-w1']) + CURRENT_SESSION )
        self.assertEqual(response.status_code, 403)

        self.login(USERS[2], 'password')

        response = self.client.get( reverse('administrators:current_sessions') )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('administrators:show_session', args=['2019-w1']) + CURRENT_SESSION )
        self.assertEqual(response.status_code, 403)

        self.login('user3.admin', 'password')

        response = self.client.get( reverse('administrators:current_sessions') )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('administrators:show_session', args=['2019-w1']) + CURRENT_SESSION )
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

        response = self.client.get( reverse('administrators:show_session', args=['2019-w1']) + CURRENT_SESSION )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:edit_session', args=['2019-w1']) + CURRENT_SESSION )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:show_session', args=['2019-w1']) + ARCHIVED_SESSION )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:edit_session', args=['2019-w1']) + ARCHIVED_SESSION )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:show_session', args=['2019-w1']) + '?next=/administrators/sessions/currentt/&p=Current%20Sessions' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:edit_session', args=['2019-w1']) + '?next=/administrators/sessions/archive/&p=Archived%20Sessions' )
        self.assertEqual(response.status_code, 404)

    def test_show_session(self):
        print('\n- Test: show a session')
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


    def test_create_session(self):
        print('\n- Test: create a session')
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
        print('\n- Test: create an existing session for checking duplicates')
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
        print('\n- Test: delete a session')
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
        print('\n- Test: delete a not existing session')
        self.login()

        data = {
            'session': '1000',
            'next': CURRENT_NEXT
        }
        response = self.client.post(reverse('administrators:delete_session_confirmation', args=['2019-w9']) + CURRENT_SESSION, data=urlencode(data), content_type=ContentType)
        self.assertEqual(response.status_code, 404)


    def test_edit_session(self):
        print('\n- Test: edit a session')
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
        print('\n- Test: edit a not existing session')
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
        print('\n- Test: remove courses in a session')
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
        print('\n- Test: add empty courses in a session')
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


class JobTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        print('\nJob testing has started ==>')
        cls.user = userApi.get_user(USERS[0], 'username')

    def login(self, username=None, password=None):
        if username and password:
            self.client.post(LOGIN_URL, data={'username': username, 'password': password})
        else:
            self.client.post(LOGIN_URL, data={'username': self.user.username, 'password': PASSWORD})

    def messages(self, res):
        return [m.message for m in get_messages(res.wsgi_request)]

    def test_view_url_exists_at_desired_location(self):
        print('\n- Test: view url exists at desired location')
        self.login()

        response = self.client.get( reverse('administrators:show_job', args=[SESSION, JOB]) + PREPARE_JOB )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:show_job', args=[SESSION, JOB]) + '?next=/administrators/jobs/preparee/?page=2&p=Prepare%20Jobs' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:prepare_jobs') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:progress_jobs') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:instructor_jobs') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:student_jobs') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:show_job_applications', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:instructor_jobs_details', args=[ USERS[1] ]) + INSTRUCTOR_JOB )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:student_jobs_details', args=[USERS[2]]) + STUDENT_JOB )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:student_jobs_details', args=[USERS[2]]) + '?next=/administrators/jobs/student/?page=2&p=Jobs%20by%20Student&t=alll' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:edit_job', args=[SESSION, JOB]) + PREPARE_JOB )
        self.assertEqual(response.status_code, 200)

    def test_show_job(self):
        print('\n- Test: display a job')
        self.login()
        job = adminApi.get_job_by_session_slug_job_slug(SESSION, JOB)

        response = self.client.get( reverse('administrators:show_job', args=[SESSION, JOB]) + '?next=/administrators/jobs/prepare/?page=2' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:show_job', args=[SESSION, JOB]) + '?nex=/administrators/jobs/prepare/?page=2&p=Prepare%20Jobs' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:show_job', args=[SESSION, JOB]) + '?next=/administrator/jobs/prepare/?page=2&p=Prepare%20Jobs' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:show_job', args=[SESSION, JOB]) + '?next=/administrators/jobs/prepare/?page=2&a=Prepare%20Jobs' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:show_job', args=[SESSION, JOB]) + '?next=/administrators/jobs/prepare/?page=2&p=Prepare%20Job' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:show_job', args=[SESSION, JOB]) + PREPARE_JOB )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['job'].id, job.id)
        self.assertEqual(response.context['job'].session.slug, SESSION)
        self.assertEqual(response.context['job'].course.slug, JOB)



    def test_prepare_jobs(self):
        print('\n- Test: display all prepare jobs')
        self.login()

        response = self.client.get( reverse('administrators:prepare_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, self.user.username)
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['jobs']), settings.PAGE_SIZE )
        self.assertEqual( len(adminApi.get_jobs()), 450 )

    def test_edit_job(self):
        print('\n- Test: edit a job')
        self.login()

        job = adminApi.get_job_by_session_slug_job_slug(SESSION, JOB)

        response = self.client.get( reverse('administrators:edit_job', args=[SESSION, JOB]) + PREPARE_JOB)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, self.user.username)
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        form = response.context['form']
        self.assertFalse(form.is_bound)
        self.assertEqual(form.instance.id, job.id)

        data1 = {
            'course_overview': 'new course overview',
            'description': 'new description',
            'note': 'new note',
            'assigned_ta_hours': '180.00',
            'accumulated_ta_hours': '35.0',
            'is_active': False,
            'next': '/administrators/Jobs/prepare/?page=2'
        }
        response = self.client.post( reverse('administrators:edit_job', args=[SESSION, JOB]) + PREPARE_JOB, data=urlencode(data1, True), content_type=ContentType )
        self.assertEqual(response.status_code, 404)

        data2 = {
            'course_overview': 'new course overview',
            'description': 'new description',
            'note': 'new note',
            'assigned_ta_hours': '180.00',
            'accumulated_ta_hours': '35.0',
            'is_active': False,
            'next': reverse('administrators:prepare_jobs') + '?page=2'
        }
        response = self.client.post( reverse('administrators:edit_job', args=[SESSION, JOB]) + PREPARE_JOB, data=urlencode(data2, True), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEquals(response.url, reverse('administrators:prepare_jobs') + '?page=2')
        self.assertRedirects(response, response.url)

        updated_job = adminApi.get_job_by_session_slug_job_slug(SESSION, JOB)
        self.assertEqual(updated_job.course_overview, data2['course_overview'])
        self.assertEqual(updated_job.description, data2['description'])
        self.assertEqual(updated_job.note, data2['note'])
        self.assertEqual(updated_job.assigned_ta_hours, float(data2['assigned_ta_hours']))
        self.assertEqual(updated_job.accumulated_ta_hours, float(data2['accumulated_ta_hours']))
        self.assertEqual(updated_job.is_active, data2['is_active'])


    def test_add_instructors(self):
        print('\n- Test: add instructors')
        self.login()

        job = adminApi.get_job_by_session_slug_job_slug(SESSION, JOB)
        self.assertEqual( len(job.instructors.all()), 1 )

        data1 = {
            'instructors': ['10']
        }
        response = self.client.post( reverse('administrators:add_job_instructors', args=[SESSION, JOB]), data=urlencode(data1, True), content_type=ContentType )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(content['status'], 'success')
        self.assertTrue('Success' in content['message'])

        job = adminApi.get_job_by_session_slug_job_slug(SESSION, JOB)
        self.assertEqual( len(job.instructors.all()), 2 )

        data2 = {
            'instructors': ['11']
        }
        response = self.client.post( reverse('administrators:add_job_instructors', args=[SESSION, JOB]), data=urlencode(data2, True), content_type=ContentType )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(content['status'], 'success')
        self.assertTrue('Success' in content['message'])

        job = adminApi.get_job_by_session_slug_job_slug(SESSION, JOB)
        self.assertEqual( len(job.instructors.all()), 3 )

        data3 = {
            'instructors': ['11']
        }
        response = self.client.post( reverse('administrators:add_job_instructors', args=[SESSION, JOB]), data=urlencode(data3, True), content_type=ContentType )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(content['status'], 'error')
        self.assertTrue('An error occurred' in content['message'])

        job = adminApi.get_job_by_session_slug_job_slug(SESSION, JOB)
        self.assertEqual( len(job.instructors.all()), 3 )


    def test_delete_instructors(self):
        print('\n- Test: delete instructors')
        self.login()
        job = adminApi.get_job_by_session_slug_job_slug(SESSION, JOB)
        self.assertEqual( len(job.instructors.all()), 1 )

        data1 = {
            'instructors': ['10']
        }
        response = self.client.post( reverse('administrators:delete_job_instructors', args=[SESSION, JOB]), data=urlencode(data1, True), content_type=ContentType )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(content['status'], 'error')
        self.assertTrue('An error occurred' in content['message'])

        data2 = {
            'instructors': ['56']
        }
        response = self.client.post( reverse('administrators:delete_job_instructors', args=[SESSION, JOB]), data=urlencode(data2, True), content_type=ContentType )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(content['status'], 'success')
        self.assertTrue('Success' in content['message'])

        job = adminApi.get_job_by_session_slug_job_slug(SESSION, JOB)
        self.assertEqual( len(job.instructors.all()), 0 )

        data3 = {
            'instructors': ['56']
        }
        response = self.client.post( reverse('administrators:delete_job_instructors', args=[SESSION, JOB]), data=urlencode(data3, True), content_type=ContentType )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(content['status'], 'error')
        self.assertTrue('An error occurred' in content['message'])

    def test_edit_not_existing_job(self):
        print('\n- Test: display all progress jobs')
        self.login()

        data = {
            'title': 'new title',
            'description': 'new description',
            'quallification': 'new quallification',
            'note': 'new note',
            'assigned_ta_hours': '180.00',
            'accumulated_ta_hours': '30.0',
            'is_active': False,
            'instructors': ['4', '5', '6']
        }

        response = self.client.post(reverse('administrators:edit_job', args=['2010-w1', JOB]), data=urlencode(data, True), content_type=ContentType)
        self.assertEqual(response.status_code, 404)


    def test_progress_jobs(self):
        print('\n- Test: display all progress jobs')
        self.login()

        response = self.client.get( reverse('administrators:progress_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, self.user.username)
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['jobs']), settings.PAGE_SIZE )
        self.assertEqual( len(adminApi.get_jobs()), 450 )

    def test_instructor_jobs(self):
        print('\n- Test: display all instructor jobs')
        self.login()

        response = self.client.get( reverse('administrators:instructor_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, self.user.username)
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['users']), 50 )
        self.assertEqual( len(userApi.get_users_by_role('Instructor')), 57 )


    def test_student_jobs(self):
        print('\n- Test: display all student jobs')
        self.login()

        response = self.client.get( reverse('administrators:student_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, self.user.username)
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['users']), settings.PAGE_SIZE )
        self.assertEqual( len(userApi.get_users_by_role('Student')), 100 )

    def test_show_job_applications(self):
        print('\n- Test: display a job applications')
        self.login()

        response = self.client.get( reverse('administrators:show_job_applications', args=[SESSION, JOB]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        job = response.context['job']
        self.assertEqual(job.session.year, '2019')
        self.assertEqual(job.session.term.code, 'W1')
        self.assertEqual(job.session.slug, SESSION)
        self.assertEqual(job.course.slug, JOB)

    def test_instructor_jobs_details(self):
        print('\n- Test: display jobs that an instructor has')
        self.login()

        response = self.client.get( reverse('administrators:instructor_jobs_details', args=[ USERS[1] ]) + '?next=/administrators/jobs/instructor/?page=2' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:instructor_jobs_details', args=[ USERS[1] ]) + '?nex=/administrators/jobs/instructor/?page=2&p=Jobs%20by%20Instructor' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:instructor_jobs_details', args=[ USERS[1] ]) + '?next=/administrator/jobs/instructor/?page=2&p=Jobs%20by%20Instructor' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:instructor_jobs_details', args=[ USERS[1] ]) + '?next=/administrators/jobs/instructor/?page=2&a=Jobs%20by%20Instructor' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:instructor_jobs_details', args=[ USERS[1] ]) + '?next=/administrators/jobs/instructor/?page=2&p=Jobs%20by%20Instructorr' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:instructor_jobs_details', args=[ USERS[1] ]) + INSTRUCTOR_JOB )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual(response.context['user'].username, USERS[1])

    def test_student_jobs_details(self):
        print('\n- Test: display jobs that a student has')
        self.login()

        response = self.client.get( reverse('administrators:student_jobs_details', args=[ USERS[2] ]) + '?next=/administrators/jobs/student/?page=2' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:student_jobs_details', args=[ USERS[2] ]) + '?next=/administrators/jobs/student/?page=2&p=Jobs%20by%20Student' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:student_jobs_details', args=[ USERS[2] ]) + '?next=/administrators/jobs/student/?page=2&t=all' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:student_jobs_details', args=[ USERS[2] ]) + '?nex=/administrators/jobs/student/?page=2&p=Jobs%20by%20Student&t=all' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:student_jobs_details', args=[ USERS[2] ]) + '?next=/administrator/jobs/student/?page=2&p=Jobs%20by%20Student&t=all' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:student_jobs_details', args=[ USERS[2] ]) + '?next=/administrators/jobs/student/?page=2&a=Jobs%20by%20Student&t=all' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:student_jobs_details', args=[ USERS[2] ]) + '?next=/administrators/jobs/student/?page=2&p=Jobs%20by%20Studentt&t=all' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:student_jobs_details', args=[ USERS[2] ]) + '?next=/administrators/jobs/student/?page=2&p=Jobs%20by%20Student&y=all' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:student_jobs_details', args=[ USERS[2] ]) + '?next=/administrators/jobs/student/?page=2&p=Jobs%20by%20Student&t=alll' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('administrators:student_jobs_details', args=[ USERS[2] ]) + STUDENT_JOB )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual(response.context['user'].username, USERS[2])

        apps = response.context['apps']
        num_offered = 0
        num_accepted = 0
        for app in apps:
            if app.offered is not None: num_offered += 1
            if app.accepted is not None: num_accepted += 1

        total_assigned_hours = response.context['total_assigned_hours']
        self.assertEqual( total_assigned_hours['offered'], {'2019-W1': 100.0, '2019-W2': 20.0, '2019-S': 35.0} )
        self.assertEqual( total_assigned_hours['accepted'], {'2019-W1': 100.0, '2019-W2': 50.0} )
        self.assertEqual(len(apps), 7)
        self.assertEqual(num_offered, 4)
        self.assertEqual(num_accepted, 3)


class ApplicationTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        print('\nApplication testing has started ==>')
        cls.user = userApi.get_user(USERS[0], 'username')

    def login(self, username=None, password=None):
        if username and password:
            self.client.post(LOGIN_URL, data={'username': username, 'password': password})
        else:
            self.client.post(LOGIN_URL, data={'username': self.user.username, 'password': PASSWORD})

    def messages(self, res):
        return [m.message for m in get_messages(res.wsgi_request)]

    def test_view_url_exists_at_desired_location(self):
        print('\n- Test: view url exists at desired location')
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
        print('\n- Test: Display an application details')
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
        print('\n- Test: Display a dashboard to take a look at updates')
        self.login()

    def test_all_applications(self):
        print('\n- Test: Display all applications')
        self.login()

        response = self.client.get( reverse('administrators:all_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['apps']), 26)

    def test_selected_applications(self):
        print('\n- Test: Display applications selected by instructors')
        self.login()

        response = self.client.get( reverse('administrators:selected_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['apps']), 20)
        self.assertEqual( len(response.context['classification_choices']), 6)
        self.assertEqual(response.context['app_status']['offered'], ApplicationStatus.OFFERED)

    def test_offer_job(self):
        print('\n- Test: Admin can offer a job to each job')
        self.login()

        app_id = '2'
        app = adminApi.get_application(app_id)
        self.assertFalse(adminApi.get_offered(app))

        FULL_PATH = reverse('administrators:selected_applications') + '?page=2'

        data1 = {
            'note': 'this is a note',
            'assigned_hours': 'abcde',
            'application': app_id,
            'has_contract_read': False,
            'assigned': ApplicationStatus.OFFERED,
            'applicant': '65',
            'classification': '2',
            'next': '/administrators/applications/selectedd/?page=2'
        }
        response = self.client.post(reverse('administrators:offer_job', args=[app.job.session.slug, app.job.course.slug]), data=urlencode(data1), content_type=ContentType)
        self.assertEqual(response.status_code, 404)

        data2 = {
            'note': 'this is a note',
            'assigned_hours': 'abcde',
            'application': app_id,
            'has_contract_read': False,
            'assigned': ApplicationStatus.OFFERED,
            'applicant': '65',
            'classification': '2',
            'next': FULL_PATH
        }
        response = self.client.post(reverse('administrators:offer_job', args=[app.job.session.slug, app.job.course.slug]), data=urlencode(data2), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        data3 = {
            'note': 'this is a note',
            'assigned_hours': '-20.0',
            'application': app_id,
            'has_contract_read': False,
            'assigned': ApplicationStatus.OFFERED,
            'applicant': '65',
            'classification': '2',
            'next': FULL_PATH
        }
        response = self.client.post(reverse('administrators:offer_job', args=[app.job.session.slug, app.job.course.slug]), data=urlencode(data3), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        data4 = {
            'note': 'this is a note',
            'assigned_hours': '20.0',
            'application': app_id,
            'has_contract_read': False,
            'assigned': ApplicationStatus.OFFERED,
            'applicant': '65',
            'next': FULL_PATH
        }
        response = self.client.post(reverse('administrators:offer_job', args=[app.job.session.slug, app.job.course.slug]), data=urlencode(data4), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        data5 = {
            'note': 'this is a note',
            'assigned_hours': '20.0',
            'application': app_id,
            'has_contract_read': False,
            'assigned': ApplicationStatus.OFFERED,
            'applicant': '65',
            'classification': '',
            'next': FULL_PATH
        }
        response = self.client.post(reverse('administrators:offer_job', args=[app.job.session.slug, app.job.course.slug]), data=urlencode(data5), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        data6 = {
            'note': 'this is a note',
            'assigned_hours': '210.0',
            'application': app_id,
            'has_contract_read': False,
            'assigned': ApplicationStatus.OFFERED,
            'applicant': '65',
            'classification': '2',
            'next': FULL_PATH
        }
        response = self.client.post(reverse('administrators:offer_job', args=[app.job.session.slug, app.job.course.slug]), data=urlencode(data6), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        data7 = {
            'note': 'this is a note',
            'assigned_hours': '20.0',
            'application': app_id,
            'has_contract_read': False,
            'assigned': ApplicationStatus.OFFERED,
            'applicant': '65',
            'classification': '2',
            'next': FULL_PATH
        }
        response = self.client.post(reverse('administrators:offer_job', args=[app.job.session.slug, app.job.course.slug]), data=urlencode(data7), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        app = adminApi.get_application(app_id)
        offered_app = adminApi.get_offered(app)[0]
        self.assertEqual(app.classification.id, int(data7['classification']))
        self.assertEqual(app.note, data7['note'])
        self.assertFalse(offered_app.has_contract_read)
        self.assertTrue(offered_app.assigned, ApplicationStatus.OFFERED)
        self.assertEqual(offered_app.assigned_hours, float(data7['assigned_hours']))

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
        self.assertTrue('An error occurred' in messages[0])
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
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        edited_app = adminApi.get_application(app_id)
        edited_app = adminApi.add_app_info_into_application(edited_app, ['offered'])
        self.assertEqual(edited_app.classification.id, int(data9['classification']))
        self.assertEqual(edited_app.note, data9['note'])
        self.assertEqual(edited_app.offered.assigned_hours, float(data9['assigned_hours']))


    def test_offered_applications(self):
        print('\n- Test: Display applications offered by admins')
        self.login()

        response = self.client.get( reverse('administrators:offered_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['apps']), 10)
        self.assertEqual( len(response.context['admin_emails']), 3)

    def test_offered_applications_send_email(self):
        print('\n- Test: Send an email to offered applications')
        self.login()

        curr_emails = adminApi.get_emails()
        self.assertEqual( len(curr_emails), 5 )
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
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual( len(adminApi.get_emails()), len(curr_emails) + len(user_emails) )


    def test_email_history(self):
        print('\n- Test: Display all of email sent by admins to let them know job offers')
        self.login()

        response = self.client.get(reverse('administrators:email_history') + '?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['emails']), 5 )

    def test_send_reminder(self):
        print('\n- Test: Send a reminder email')
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
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)
        self.assertEqual(adminApi.get_emails().first().application.id, data1['application'])
        self.assertEqual(len(adminApi.get_emails()), total_emails + 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_accepted_applications(self):
        print('\n- Test: Display applications accepted by students')
        self.login()

        response = self.client.get( reverse('administrators:accepted_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['apps']), 5)

    def test_admin_docs(self):
        print('\n- Test: Admin or HR can have update admin docs')
        self.login()

        FULL_PATH = reverse('administrators:accepted_applications') + '?page=2'
        NEXT = '?next=' + FULL_PATH

        app_id = 1

        data0 = {
            'application': app_id,
            'pin': '12377',
            'tasm': True,
            'eform': 'af3343',
            'speed_chart': 'adsf',
            'processing_note': 'this is a processing note',
            'next': '/administrators/applications/Accepted/?page=2'
        }
        response = self.client.post(reverse('administrators:accepted_applications'), data=urlencode(data0), content_type=ContentType)
        self.assertEqual(response.status_code, 404)

        data1 = {
            'application': app_id,
            'pin': '12377',
            'tasm': True,
            'eform': 'af3343',
            'speed_chart': 'adsf',
            'processing_note': 'this is a processing note',
            'next': FULL_PATH
        }
        response = self.client.post(reverse('administrators:accepted_applications'), data=urlencode(data1), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        data2 = {
            'application': app_id,
            'pin': '1237',
            'tasm': True,
            'eform': 'af3343',
            'speed_chart': 'adsf',
            'processing_note': 'this is a processing note',
            'next': FULL_PATH
        }
        response = self.client.post(reverse('administrators:accepted_applications'), data=urlencode(data2), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

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
        self.assertTrue(app.admindocuments.eform, data2['eform'])
        self.assertTrue(app.admindocuments.speed_chart, data2['speed_chart'])
        self.assertTrue(app.admindocuments.processing_note, data2['processing_note'])


    def test_declined_applications(self):
        print('\n- Test: Display applications declined by students')
        self.login()

        response = self.client.get( reverse('administrators:declined_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['apps']), 4)

    def test_declined_applications_send_email(self):
        print('\n- Test: Send an email to declined applications')
        self.login()

        curr_emails = adminApi.get_emails()
        self.assertEqual( len(curr_emails), 5 )
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
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual( len(adminApi.get_emails()), len(curr_emails) + len(user_emails) )


    def test_decline_reassign(self):
        print('\n- Test: Decline and reassign a job offer with new assigned hours')
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
        self.assertTrue('Success' in messages[0])
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


    def test_terminate(self):
        print('\n- Test: terminate an application')
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
        self.assertTrue('Success' in messages[0])
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
        print('\n- Test: Display applications terminated by students')
        self.login()

        response = self.client.get( reverse('administrators:terminated_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['apps']), 1)

    def test_terminated_applications_send_email(self):
        print('\n- Test: Send an email to terminated applications')
        self.login()

        curr_emails = adminApi.get_emails()
        self.assertEqual( len(curr_emails), 5 )
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
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual( len(adminApi.get_emails()), len(curr_emails) + len(user_emails) )


class HRTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        print('\nHR testing has started ==>')
        cls.user = userApi.get_user(USERS[0], 'username')

    def login(self, username=None, password=None):
        if username and password:
            self.client.post(LOGIN_URL, data={'username': username, 'password': password})
        else:
            self.client.post(LOGIN_URL, data={'username': self.user.username, 'password': PASSWORD})

    def messages(self, res):
        return [m.message for m in get_messages(res.wsgi_request)]

    def test_view_url_exists_at_desired_location(self):
        print('\n- Test: view url exists at desired location')

        response = self.client.get( reverse('administrators:all_users') )
        self.assertEqual(response.status_code, 302)

        response = self.client.get( reverse('administrators:create_user') )
        self.assertEqual(response.status_code, 302)

        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + ALL_USER )
        self.assertEqual(response.status_code, 302)

        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + DASHBOARD_USER )
        self.assertEqual(response.status_code, 302)

        self.login()

        response = self.client.get( reverse('administrators:all_users') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:create_user') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + ALL_USER )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + '?next=/administrators/hr/users/all/?page=2&p=all%20Users&t=basic' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + '?next=/administrators/hr/users/all/?page=2&p=All%20User&t=basic' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + '?next=/administrators/applications/dashboard/&p=Dashboardd&t=basic' )
        self.assertEqual(response.status_code, 404)

        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + '?next=/administrators/applications/dashboard/&p=Dashboard&t=basicd' )
        self.assertEqual(response.status_code, 404)

    def test_all_users(self):
        print('\n- Test: get all users')
        self.login()
        response = self.client.get(reverse('administrators:all_users'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['users']), settings.PAGE_SIZE )
        self.assertEqual( len(userApi.get_users()), 164 )

    def test_show_user(self):
        print('\n- Test: show a user')
        self.login()

        next = '?next=/administrators/{0}/&p={1}&t={2}'
        next_wrong = '?nex=/administrators/{0}/&p={1}&t={2}'
        next_page_wrong = '?next=/administrators/{0}/&a={1}&t={2}'
        next_tab_wrong = '?next=/administrators/{0}/&p={1}&j={2}'

        # Dashboard
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_wrong.format('applications/dashboard', 'Dashboard', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_page_wrong.format('applications/dashboard', 'Dashboard', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_tab_wrong.format('applications/dashboard', 'Dashboard', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/dashboarrd', 'Dashboard', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/dashboard', 'Dashboar', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/dashboard', 'Dashboard', 'basid') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/dashboard', 'Dashboard', 'basic') )
        self.assertEqual(response.status_code, 200)

        # All Applications
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_wrong.format('applications/all', 'All Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_page_wrong.format('applications/all', 'All Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_tab_wrong.format('applications/all', 'All Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/alll', 'All Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/all', 'All Application', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/all', 'All Applications', 'basid') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/all', 'All Applications', 'basic') )
        self.assertEqual(response.status_code, 200)

        # Selected Applications
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_wrong.format('applications/selected', 'Selected Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_page_wrong.format('applications/selected', 'Selected Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_tab_wrong.format('applications/selected', 'Selected Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/selectedd', 'Selected Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/selected', 'SelectedApplications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/selected', 'Selected Applications', 'basid') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/selected', 'Selected Applications', 'basic') )
        self.assertEqual(response.status_code, 200)

        # Offered Applications
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_wrong.format('applications/offered', 'Offered Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_page_wrong.format('applications/offered', 'Offered Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_tab_wrong.format('applications/offered', 'Offered Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/offere', 'Offered Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/offered', 'Offerd Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/offered', 'Offered Applications', 'basid') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/offered', 'Offered Applications', 'basic') )
        self.assertEqual(response.status_code, 200)

        # Accepted Applications
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_wrong.format('applications/accepted', 'Accepted Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_page_wrong.format('applications/accepted', 'Accepted Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_tab_wrong.format('applications/accepted', 'Accepted Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/acceped', 'Accepted Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/accepted', 'Accepted Applicatons', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/accepted', 'Accepted Applications', 'basid') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/accepted', 'Accepted Applications', 'basic') )
        self.assertEqual(response.status_code, 200)

        # Declined Applications
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_wrong.format('applications/declined', 'Declined Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_page_wrong.format('applications/declined', 'Declined Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_tab_wrong.format('applications/declined', 'Declined Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/dclined', 'Declined Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/declined', 'Decined Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/declined', 'Declined Applications', 'basid') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/declined', 'Declined Applications', 'basic') )
        self.assertEqual(response.status_code, 200)

        # Terminated Applications
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_wrong.format('applications/terminated', 'Terminated Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_page_wrong.format('applications/terminated', 'Terminated Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_tab_wrong.format('applications/terminated', 'Terminated Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/terminatedd', 'Terminated Applications', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/terminated', 'Terminated Application', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/terminated', 'Terminated Applications', 'basid') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('applications/terminated', 'Terminated Applications', 'basic') )
        self.assertEqual(response.status_code, 200)

        # All Users
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_wrong.format('hr/users/all', 'All Users', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_page_wrong.format('hr/users/all', 'All Users', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_tab_wrong.format('hr/users/all', 'All Users', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('hr/users/alll', 'All Users', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('hr/users/all', 'All User', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('hr/users/all', 'All Users', 'basid') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('hr/users/all', 'All Users', 'basic') )
        self.assertEqual(response.status_code, 200)

        # Jobs by Instructor
        response = self.client.get( reverse('users:show_user', args=[USERS[1]]) + next_wrong.format('jobs/instructor', 'Jobs by Instructor', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[1]]) + next_page_wrong.format('jobs/instructor', 'Jobs by Instructor', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[1]]) + next_tab_wrong.format('jobs/instructor', 'Jobs by Instructor', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[1]]) + next.format('jobs/instructorr', 'Jobs by Instructor', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[1]]) + next.format('jobs/instructor', 'Jobs byInstructor', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[1]]) + next.format('jobs/instructor', 'Jobs by Instructor', 'basid') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[1]]) + next.format('jobs/instructor', 'Jobs by Instructor', 'basic') )
        self.assertEqual(response.status_code, 200)
        response = self.client.get( reverse('users:show_user', args=[USERS[1]]) + next.format('jobs/instructor', 'Jobs by Instructor', 'additional') )
        self.assertEqual(response.status_code, 200)
        response = self.client.get( reverse('users:show_user', args=[USERS[1]]) + next.format('jobs/instructor', 'Jobs by Instructor', 'confidential') )
        self.assertEqual(response.status_code, 200)
        response = self.client.get( reverse('users:show_user', args=[USERS[1]]) + next.format('jobs/instructor', 'Jobs by Instructor', 'resume') )
        self.assertEqual(response.status_code, 404)

        # Jobs by Student
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_wrong.format('jobs/student', 'Jobs by Student', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_page_wrong.format('jobs/student', 'Jobs by Student', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next_tab_wrong.format('jobs/student', 'Jobs by Student', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('job/student', 'Jobs by Student', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('jobs/student', 'Jobs by tudent', 'basic') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('jobs/student', 'Jobs by Student', 'basid') )
        self.assertEqual(response.status_code, 404)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('jobs/student', 'Jobs by Student', 'basic') )
        self.assertEqual(response.status_code, 200)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('jobs/student', 'Jobs by Student', 'additional') )
        self.assertEqual(response.status_code, 200)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('jobs/student', 'Jobs by Student', 'confidential') )
        self.assertEqual(response.status_code, 200)
        response = self.client.get( reverse('users:show_user', args=[USERS[2]]) + next.format('jobs/student', 'Jobs by Student', 'resume') )
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse('users:show_user', args=[USERS[2]]) + ALL_USER)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['selected_user'].username, USERS[2])

    def test_show_user_not_exists(self):
        print('\n- Test: show no existing user ')
        self.login()

        response = self.client.get(reverse('users:show_user', args=['user10000.test']) + ALL_USER)
        self.assertEqual(response.status_code, 404)


    def test_edit_user_role_change(self):
        print('\n- Test: edit a user with role change')
        self.login()

        user = userApi.get_user(USERS[2], 'username')
        user_first_role = user.profile.roles.all()[0]
        self.assertEqual(user_first_role.name, Role.STUDENT)

        data1 = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'username': user.username,
            'user': user.id,
            'roles': [],
            'next': reverse('administrators:all_users') + '?page=2'
        }
        response = self.client.post(reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER, data=urlencode(data1, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER)
        self.assertRedirects(response, response.url)

        data2 = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'username': user.username,
            'user': user.id,
            'roles': ['2', '3'],
            'next': reverse('administrators:all_users') + '?page=2'
        }

        response = self.client.post(reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER, data=urlencode(data2, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:all_users') + '?page=2')
        self.assertRedirects(response, response.url)

    def test_edit_user(self):
        print('\n- Test: edit an user')
        self.login()

        user = userApi.get_user(USERS[2], 'username')
        user_first_role = user.profile.roles.all()[0]
        self.assertEqual(user_first_role.name, Role.STUDENT)

        # Missing first name, last name, email, username
        data0 = {
            'user': user.id,
            'student_number': '12222222',
            'employee_number': '12345678',
            'is_superuser': False,
            'preferred_name': 'new name',
            'roles': ['4'],
            'next': '/administrators/hr/user/all/?page=2'
        }
        response = self.client.post(reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER, data=urlencode(data0, True), content_type=ContentType)
        self.assertEqual(response.status_code, 404)

        # Missing first name, last name, email, username
        data1 = {
            'user': user.id,
            'student_number': '12222222',
            'employee_number': '12345678',
            'is_superuser': False,
            'preferred_name': 'new name',
            'roles': ['4'],
            'next': reverse('administrators:all_users') + '?page=2'
        }
        response = self.client.post(reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER, data=urlencode(data1, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER)
        self.assertRedirects(response, response.url)

        # Missing last name, username, email
        data2 = {
            'user': user.id,
            'first_name': 'change first name',
            'student_number': '12222222',
            'is_new_employee': True,
            'employee_number': '12345678',
            'is_superuser': False,
            'preferred_name': 'new name',
            'roles': ['4'],
            'next': reverse('administrators:all_users') + '?page=2'
        }
        response = self.client.post(reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER, data=urlencode(data2, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER)
        self.assertRedirects(response, response.url)

        # Missing email and username
        data3 = {
            'user': user.id,
            'first_name': 'change first name',
            'last_name': 'change last name',
            'student_number': '12222222',
            'is_new_employee': True,
            'employee_number': '12345678',
            'is_superuser': False,
            'preferred_name': 'new name',
            'roles': ['4'],
            'next': reverse('administrators:all_users') + '?page=2'
        }
        response = self.client.post(reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER, data=urlencode(data3, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER)
        self.assertRedirects(response, response.url)

        # Missing username
        data4 = {
            'user': user.id,
            'first_name': 'change first name',
            'last_name': 'change last name',
            'email': 'new.email@example.com',
            'student_number': '12222222',
            'is_new_employee': True,
            'employee_number': '12345678',
            'is_superuser': False,
            'preferred_name': 'new name',
            'roles': ['4'],
            'next': reverse('administrators:all_users') + '?page=2'
        }
        response = self.client.post(reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER, data=urlencode(data4, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER)
        self.assertRedirects(response, response.url)

        # Wrong employee number
        data5 = {
            'user': user.id,
            'first_name': 'change first name',
            'last_name': 'change last name',
            'email': 'new.email@example.com',
            'username': 'new.username',
            'student_number': '12222222',
            'is_new_employee': True,
            'employee_number': '12345678',
            'is_superuser': False,
            'preferred_name': 'new name',
            'roles': ['4'],
            'next': reverse('administrators:all_users') + '?page=2'
        }
        response = self.client.post(reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER, data=urlencode(data5, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER)
        self.assertRedirects(response, response.url)

        # Wrong employee number
        data6 = {
            'user': user.id,
            'first_name': 'change first name',
            'last_name': 'change last name',
            'email': 'new.email@example.com',
            'username': 'new.username',
            'student_number': '12222222',
            'is_new_employee': True,
            'employee_number': 'new.employee',
            'is_superuser': False,
            'preferred_name': 'new name',
            'roles': ['4'],
            'next': reverse('administrators:all_users') + '?page=2'
        }
        response = self.client.post(reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER, data=urlencode(data6, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER)
        self.assertRedirects(response, response.url)

        # Wrong employee number
        data7 = {
            'user': user.id,
            'first_name': 'change first name',
            'last_name': 'change last name',
            'email': 'new.email@example.com',
            'username': 'new.username',
            'student_number': '12222222',
            'is_new_employee': True,
            'employee_number': '123',
            'is_superuser': False,
            'preferred_name': 'new name',
            'roles': ['4'],
            'next': reverse('administrators:all_users') + '?page=2'
        }
        response = self.client.post(reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER, data=urlencode(data7, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER)
        self.assertRedirects(response, response.url)

        # Wrong student number
        data8 = {
            'user': user.id,
            'first_name': 'change first name',
            'last_name': 'change last name',
            'email': 'new.email@example.com',
            'username': 'new.username',
            'student_number': 'new.student',
            'is_new_employee': True,
            'employee_number': '1234777',
            'is_superuser': False,
            'preferred_name': 'new name',
            'roles': ['4'],
            'next': reverse('administrators:all_users') + '?page=2'
        }
        response = self.client.post(reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER, data=urlencode(data8, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER)
        self.assertRedirects(response, response.url)

        # Wrong student number
        data9 = {
            'user': user.id,
            'first_name': 'change first name',
            'last_name': 'change last name',
            'email': 'new.email@example.com',
            'username': 'new.username',
            'student_number': '123',
            'is_new_employee': True,
            'employee_number': '1234777',
            'is_superuser': False,
            'preferred_name': 'new name',
            'roles': ['4'],
            'next': reverse('administrators:all_users') + '?page=2'
        }
        response = self.client.post(reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER, data=urlencode(data9, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER)
        self.assertRedirects(response, response.url)

        data10 = {
            'user': user.id,
            'first_name': 'change first name',
            'last_name': 'change last name',
            'email': 'new.email@example.com',
            'username': 'new.username',
            'student_number': '12345670',
            'is_new_employee': False,
            'employee_number': '1234567',
            'is_superuser': False,
            'preferred_name': 'new name',
            'roles': ['4'],
            'next': reverse('administrators:all_users') + '?page=2'
        }
        response = self.client.post(reverse('administrators:edit_user', args=[ USERS[2] ]) + ALL_USER, data=urlencode(data10, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:all_users') + '?page=2')
        self.assertRedirects(response, response.url)

        u = userApi.get_user(user.id)
        self.assertEqual(u.id, data10['user'])
        self.assertEqual(u.first_name, data10['first_name'])
        self.assertEqual(u.last_name, data10['last_name'])
        self.assertEqual(u.email, data10['email'])
        self.assertEqual(u.username, data10['username'])
        self.assertEqual(u.profile.student_number, data10['student_number'])
        self.assertFalse(u.confidentiality.is_new_employee)
        self.assertEqual(u.confidentiality.employee_number, data10['employee_number'])
        self.assertFalse(u.is_superuser)
        self.assertEqual(u.profile.preferred_name, data10['preferred_name'])
        self.assertEqual(u.profile.roles.all()[0].name, Role.INSTRUCTOR)
        self.assertIsNotNone( userApi.has_user_confidentiality_created(u) )


    def test_delete_user(self):
        print('\n- Test: delete an user')
        self.login()

        user = userApi.get_user(USERS[2], 'username')

        response = self.client.get(reverse('administrators:delete_user_confirmation', args=[USERS[2]]) + ALL_USER)
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['users']), 164 )
        self.assertEqual( len(response.context['apps']), 7 )
        apps = response.context['apps']

        items = []
        for app in apps:
            accepted = app.applicationstatus_set.filter(assigned=ApplicationStatus.ACCEPTED)
            if accepted.exists():
                items.append({ 'job': app.job, 'assigned_hours': accepted.last().assigned_hours })
            else:
                items.append({ 'job': app.job, 'assigned_hours': 0.0 })

        data = {
            'user': user.id,
            'next': reverse('administrators:all_users') + '?page=2'
        }
        response = self.client.post(reverse('administrators:delete_user_confirmation', args=[USERS[2]]) + ALL_USER, data=urlencode(data), content_type=ContentType)

        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        for item in items:
            new_job = adminApi.get_job_by_session_slug_job_slug(item['job'].session.slug, item['job'].course.slug)
            self.assertEqual(item['job'].accumulated_ta_hours - item['assigned_hours'], new_job.accumulated_ta_hours)

        response = self.client.get(reverse('users:show_user', args=[USERS[2]]) + ALL_USER)
        self.assertEqual(response.status_code, 404)

        self.assertIsNone(userApi.user_exists_username(user.username))
        self.assertFalse(userApi.resume_exists(user))
        self.assertFalse(userApi.confidentiality_exists(user))

        # Check user's profile, profile-degrees, profile-trainings
        self.assertFalse(userApi.profile_exists(user))
        degree_found = False
        for degree in userApi.get_degrees():
            if degree.profile_set.filter(user_id=user.id ).exists():
                degree_found = True
        self.assertFalse(degree_found)

        training_found = False
        for training in userApi.get_trainings():
            if training.profile_set.filter(user_id=user.id ).exists():
                training_found = True
        self.assertFalse(degree_found)

        self.assertIsNone( userApi.has_user_profile_created(user) )
        self.assertIsNone( userApi.has_user_resume_created(user) )
        self.assertIsNone( userApi.has_user_confidentiality_created(user) )


    def test_create_user(self):
        print('\n- Test: create an user')
        self.login()

        data = {
            'first_name': 'firstname',
            'last_name': 'lastname',
            'email': 'email@example.com',
            'username': 'firstname_lastname',
            'is_new_employee': True,
            'employee_number': '1233344',
            'student_number': '12345667',
            'is_superuser': False,
            'preferred_name': 'preferredname',
            'roles': ['5']
        }

        response = self.client.post(reverse('administrators:create_user'), data=urlencode(data, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        u = userApi.get_user(data['username'], 'username')
        self.assertEqual(u.username, data['username'])
        self.assertTrue(userApi.profile_exists_by_username(u.username))
        self.assertEqual(u.first_name, data['first_name'])
        self.assertEqual(u.last_name, data['last_name'])
        self.assertEqual(u.email, data['email'])
        self.assertEqual(u.username, data['username'])
        self.assertEqual(u.profile.student_number, data['student_number'])
        self.assertTrue(u.confidentiality.is_new_employee)
        self.assertEqual(u.confidentiality.employee_number, data['employee_number'])
        self.assertFalse(u.is_superuser)
        self.assertEqual(u.profile.preferred_name, data['preferred_name'])
        self.assertEqual(u.profile.roles.all()[0].name, Role.STUDENT)
        self.assertIsNotNone( userApi.has_user_confidentiality_created(u) )


    def test_create_user_missing_values(self):
        print('\n- Test: create an user with missing values')
        self.login()

        data = {
            'student_number': '923423434',
            'preferred_name': 'new preferred name'
        }
        response = self.client.post(reverse('administrators:create_user'), data=urlencode(data, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:create_user'))
        self.assertRedirects(response, response.url)

        data2 = {
            'student_number': 'abcdefg',
            'preferred_name': 'new preferred name'
        }
        response = self.client.post(reverse('administrators:create_user'), data=urlencode(data2, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:create_user'))
        self.assertRedirects(response, response.url)

        data3 = {
            'student_number': '92342343',
            'preferred_name': 'new preferred name',
            'first_name': 'new first name'
        }
        response = self.client.post(reverse('administrators:create_user'), data=urlencode(data3, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:create_user'))
        self.assertRedirects(response, response.url)

        data4 = {
            'student_number': '92342343',
            'preferred_name': 'new preferred name',
            'first_name': 'new first name',
            'last_name': 'new last name'
        }
        response = self.client.post(reverse('administrators:create_user'), data=urlencode(data4, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:create_user'))
        self.assertRedirects(response, response.url)

        data5 = {
            'student_number': '92342343',
            'preferred_name': 'new preferred name',
            'first_name': 'new first name',
            'last_name': 'new last name',
            'email': 'new.email@example.com'
        }
        response = self.client.post(reverse('administrators:create_user'), data=urlencode(data5, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:create_user'))
        self.assertRedirects(response, response.url)

        data6 = {
            'student_number': '92342343',
            'preferred_name': 'new preferred name',
            'first_name': 'new first name',
            'last_name': 'new last name',
            'email': 'new.email@example.com',
            'roles': ['5']
        }
        response = self.client.post(reverse('administrators:create_user'), data=urlencode(data6, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:create_user'))
        self.assertRedirects(response, response.url)

        data7 = {
            'student_number': '92342343',
            'preferred_name': 'new preferred name',
            'first_name': 'new first name',
            'last_name': 'new last name',
            'email': 'new.email@example.com',
            'roles': ['5'],
            'employee_number': '5'
        }
        response = self.client.post(reverse('administrators:create_user'), data=urlencode(data7, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:create_user'))
        self.assertRedirects(response, response.url)

        data8 = {
            'student_number': '92342343',
            'preferred_name': 'new preferred name',
            'first_name': 'new first name',
            'last_name': 'new last name',
            'email': 'new.email@example.com',
            'roles': ['5'],
            'employee_number': 'gdsddfds',
            'is_new_employee': True
        }
        response = self.client.post(reverse('administrators:create_user'), data=urlencode(data8, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:create_user'))
        self.assertRedirects(response, response.url)


    def test_create_user_with_duplicates(self):
        print('\n- Test: create a user with duplicates')
        self.login()
        data = {
            'first_name': 'user101',
            'last_name': 'test',
            'email': 'user101.test@example.com',
            'username': 'user100.test',
            'roles': ['5'],
            'student_number': None,
            'employee_number': None,
            'is_new_employee': True
        }

        # Check username
        self.assertIsNotNone(userApi.user_exists_username(data['username']))
        self.assertTrue(userApi.profile_exists_by_username(data['username']))

        response = self.client.post(reverse('administrators:create_user'), data=urlencode(data, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        # Check Student Number
        data = {
            'first_name': 'test555',
            'last_name': 'user555',
            'email': 'test.user555@example.com',
            'username': 'test.user555',
            'preferred_name': None,
            'student_number': 'AJWUGNUE',
            'employee_number': '1234567',
            'is_new_employee': True,
            'roles': ['5']
        }
        self.assertIsNone(userApi.user_exists_username(data['username']))
        self.assertFalse(userApi.profile_exists_by_username(data['username']))
        response = self.client.post(reverse('administrators:create_user'), data=urlencode(data, True), content_type=ContentType)
        messages = self.messages(response)

        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

    def test_create_user_via_api(self):
        print('\n- Test: create a user via api when the function added in SAML')

        data = {
            'first_name': 'test5',
            'last_name': 'user55',
            'email': 'test.user55@example.com',
            'username': 'test.user55',
            'password': 'password',
            'preferred_name': None,
            'student_number': '12345678',
            'employee_number': '9876521',
            'roles': ['5']
        }
        self.assertIsNone(userApi.user_exists_username(data['username']))
        self.assertFalse(userApi.profile_exists_by_username(data['username']))

        u = userApi.create_user(data)
        self.assertIsNotNone(userApi.user_exists_username(u.username))
        self.assertTrue(userApi.profile_exists_by_username(u.username))
        self.assertEqual(u.username, data['username'])
        self.assertEqual(u.first_name, data['first_name'])
        self.assertEqual(u.last_name, data['last_name'])
        self.assertEqual(u.email, data['email'])
        self.assertEqual(u.username, data['username'])
        self.assertEqual(u.profile.student_number, data['student_number'])
        self.assertFalse(u.confidentiality.is_new_employee)
        self.assertEqual(u.confidentiality.employee_number, data['employee_number'])
        self.assertFalse(u.is_superuser)
        self.assertEqual(u.profile.preferred_name, data['preferred_name'])
        self.assertEqual(u.profile.roles.all()[0].name, Role.STUDENT)
        self.assertIsNotNone( userApi.has_user_confidentiality_created(u) )

        # if employee number is none, is_new_employee = false
        data2 = {
            'first_name': 'test6',
            'last_name': 'user66',
            'email': 'test.user66@example.com',
            'username': 'test.user66',
            'password': 'password',
            'preferred_name': None,
            'student_number': '12345655',
            'employee_number': None,
            'roles': ['5']
        }
        self.assertIsNone(userApi.user_exists_username(data2['username']))
        self.assertFalse(userApi.profile_exists_by_username(data2['username']))

        u2 = userApi.create_user(data2)
        self.assertIsNotNone(userApi.user_exists_username(u2.username))
        self.assertTrue(userApi.profile_exists_by_username(u2.username))
        self.assertEqual(u2.username, data2['username'])
        self.assertEqual(u2.first_name, data2['first_name'])
        self.assertEqual(u2.last_name, data2['last_name'])
        self.assertEqual(u2.email, data2['email'])
        self.assertEqual(u2.username, data2['username'])
        self.assertEqual(u2.profile.student_number, data2['student_number'])
        self.assertTrue(u2.confidentiality.is_new_employee)
        self.assertEqual(u2.confidentiality.employee_number, data2['employee_number'])
        self.assertFalse(u2.is_superuser)
        self.assertEqual(u2.profile.preferred_name, data2['preferred_name'])
        self.assertEqual(u2.profile.roles.all()[0].name, Role.STUDENT)
        self.assertIsNotNone( userApi.has_user_confidentiality_created(u) )


    def test_user_exists_via_saml(self):
        print('\n- Test: user exists via SAML')
        self.login()

        data = {
            'first_name': 'test',
            'last_name': 'user5050',
            'email': 'test.user5050@example.com',
            'username': 'test.user5050',
            'student_number': None,
            'employee_number': None
        }

        # user is not present
        user = userApi.user_exists(data)
        self.assertIsNone(user)

        # user is created
        user = userApi.create_user(data)
        self.assertIsNotNone(user)
        self.assertEqual(user.username, data['username'])
        self.assertEqual(user.email, data['email'])
        self.assertEqual(user.first_name, data['first_name'])
        self.assertEqual(user.last_name, data['last_name'])
        self.assertIsNotNone(user.profile)
        self.assertIsNone(user.profile.student_number)
        roles = userApi.get_user_roles(user)
        self.assertEqual(roles, ['Student'])
        self.assertIsNotNone(user.confidentiality)
        self.assertIsNone(user.confidentiality.employee_number)
        self.assertTrue(user.confidentiality.is_new_employee)

        # no exising employee number
        data2 = {
            'first_name': 'test',
            'last_name': 'user5050',
            'email': 'test.user5050@example.com',
            'username': 'test.user5050',
            'student_number': '09988776',
            'employee_number': '9998888'
        }
        user2 = userApi.user_exists(data2)
        self.assertEqual(user2.profile.student_number, data2['student_number'])
        self.assertFalse(user2.confidentiality.is_new_employee)
        self.assertEqual(user2.confidentiality.employee_number, data2['employee_number'])

        # different employee number and is_new_employee = false
        data3 = {
            'first_name': 'test',
            'last_name': 'user5050',
            'email': 'test.user5050@example.com',
            'username': 'test.user5050',
            'student_number': '88888886',
            'employee_number': '8888888'
        }
        user3 = userApi.user_exists(data3)
        self.assertEqual(user3.username, data3['username'])
        self.assertEqual(user3.email, data3['email'])
        self.assertEqual(user3.first_name, data3['first_name'])
        self.assertEqual(user3.last_name, data3['last_name'])
        self.assertIsNotNone(user3.profile)
        self.assertEqual(user3.profile.student_number, data3['student_number'])
        roles = userApi.get_user_roles(user3)
        self.assertEqual(roles, ['Student'])
        self.assertIsNotNone(user3.confidentiality)
        self.assertEqual(user3.confidentiality.employee_number, data3['employee_number'])
        self.assertFalse(user3.confidentiality.is_new_employee)

        data4 = {
            'user': user.id,
            'first_name': 'test',
            'last_name': 'user5050',
            'email': 'test.user5050@example.com',
            'username': 'test.user5050',
            'student_number': '88888886',
            'employee_number': '8888888',
            'roles': ['4'],
            'is_new_employee': True,
            'next': reverse('administrators:all_users') + '?page=2'
        }
        response = self.client.post(reverse('administrators:edit_user', args=[ data4['username'] ]) + ALL_USER, data=urlencode(data4, True), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:all_users') + '?page=2')
        self.assertRedirects(response, response.url)

        user4 = userApi.get_user(data4['username'], 'username')
        roles = userApi.get_user_roles(user4)
        self.assertEqual(roles, ['Instructor'])
        self.assertTrue(user4.confidentiality.is_new_employee)

        # different employee number and is_new_employee = true
        data5 = {
            'first_name': 'test',
            'last_name': 'user5050',
            'email': 'test.user5050@example.com',
            'username': 'test.user5050',
            'student_number': '88888886',
            'employee_number': '8888881'
        }
        user5 = userApi.user_exists(data5)
        self.assertEqual(user5.username, data5['username'])
        self.assertEqual(user5.email, data5['email'])
        self.assertEqual(user5.first_name, data5['first_name'])
        self.assertEqual(user5.last_name, data5['last_name'])
        self.assertIsNotNone(user5.profile)
        self.assertEqual(user5.profile.student_number, data5['student_number'])
        roles = userApi.get_user_roles(user5)
        self.assertEqual(roles, ['Instructor'])
        self.assertIsNotNone(user5.confidentiality)
        self.assertEqual(user5.confidentiality.employee_number, data5['employee_number'])
        self.assertFalse(user5.confidentiality.is_new_employee)

        # same as above
        data6 = {
            'first_name': 'test',
            'last_name': 'user5050',
            'email': 'test.user5050@example.com',
            'username': 'test.user5050',
            'student_number': '88888886',
            'employee_number': '8888881'
        }
        user6 = userApi.user_exists(data6)
        self.assertEqual(user6.username, data6['username'])
        self.assertEqual(user6.email, data6['email'])
        self.assertEqual(user6.first_name, data6['first_name'])
        self.assertEqual(user6.last_name, data6['last_name'])
        self.assertIsNotNone(user6.profile)
        self.assertEqual(user6.profile.student_number, data6['student_number'])
        roles = userApi.get_user_roles(user6)
        self.assertEqual(roles, ['Instructor'])
        self.assertIsNotNone(user6.confidentiality)
        self.assertEqual(user6.confidentiality.employee_number, data6['employee_number'])
        self.assertFalse(user6.confidentiality.is_new_employee)

    def test_roles(self):
        print('\n- Test: Display all roles and create a role')
        self.login()

        response = self.client.get( reverse('administrators:roles') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['roles']), 5 )
        self.assertFalse(response.context['form'].is_bound)

        data = { 'name': 'new role' }
        response = self.client.post( reverse('administrators:roles'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:roles') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['roles']), 6 )
        self.assertEqual(response.context['roles'].last().name, data['name'])

    def test_edit_role(self):
        print('\n- Test: edit role details')
        self.login()

        slug = 'student'

        data = { 'name': 'updated student' }
        response = self.client.post( reverse('administrators:edit_role', args=[slug]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:roles') )
        self.assertEqual(response.status_code, 200)
        roles = response.context['roles']

        found = 0
        for role in roles:
            if role.slug == 'updated-student':
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_role(self):
        print('\n- Test: delete a role')
        self.login()

        total_roles = len(userApi.get_roles())

        role_id = 1
        response = self.client.post( reverse('administrators:delete_role'), data=urlencode({ 'role': role_id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:roles'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['roles']), total_roles - 1)

        found = False
        for role in response.context['roles']:
            if role.id == role_id: found = True
        self.assertFalse(found)


class CourseTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        print('\nCourse testing has started ==>')
        cls.user = userApi.get_user(USERS[0], 'username')

    def login(self, username=None, password=None):
        if username and password:
            self.client.post(LOGIN_URL, data={'username': username, 'password': password})
        else:
            self.client.post(LOGIN_URL, data={'username': self.user.username, 'password': PASSWORD})

    def messages(self, res):
        return [m.message for m in get_messages(res.wsgi_request)]

    def test_view_url_exists_at_desired_location(self):
        print('\n- Test: view url exists at desired location')
        self.login()

        response = self.client.get( reverse('administrators:all_courses') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:create_course') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:edit_course', args=[COURSE]) + '?next=' + reverse('administrators:all_users') + '?page=2' )
        self.assertEqual(response.status_code, 200)


    def test_all_courses(self):
        print('\n- Test: Display all courses and edit/delete a course')
        self.login()

        response = self.client.get(reverse('administrators:all_courses'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['courses']), settings.PAGE_SIZE )
        self.assertEqual( len(adminApi.get_courses()), 709 )

    def test_create_course(self):
        print('\n- Test: Create a course')
        self.login()

        total_courses = len(adminApi.get_courses())

        data = {
            'code': '2',
            'number': '1',
            'section': '1',
            'name': 'new course',
            'term': '2',
            'overview': 'overview',
            'job_description': 'description',
            'job_note': 'note'
        }
        response = self.client.post( reverse('administrators:create_course'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)
        self.assertEqual(response.url, reverse('administrators:all_courses'))

        response = self.client.get(reverse('administrators:all_courses'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['courses']), settings.PAGE_SIZE )
        self.assertEqual( len(adminApi.get_courses()), total_courses + 1 )

        # create the same data for checking duplicated data
        response = self.client.post( reverse('administrators:create_course'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)
        self.assertEqual(response.url, reverse('administrators:create_course'))

    def test_edit_course(self):
        print('\n- Test: Edit a course')
        self.login()

        FULL_PATH = reverse('administrators:all_users') + '?page=2'
        NEXT = '?next=' + FULL_PATH

        response = self.client.get(reverse('administrators:edit_course', args=[COURSE]) + NEXT)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual(response.context['course'].slug, COURSE)
        self.assertFalse(response.context['form'].is_bound)

        course = response.context['course']



        data1 = {
            'name': 'edit course',
            'overview': 'new overview',
            'job_description': 'new job description',
            'job_note': 'new job note',
            'next': '/administrators/hr/user/all/?page=2'
        }
        response = self.client.post( reverse('administrators:edit_course', args=[COURSE]) + NEXT, data=urlencode(data1), content_type=ContentType )
        self.assertEqual(response.status_code, 404)

        data2 = {
            'name': 'edit course',
            'overview': 'new overview',
            'job_description': 'new job description',
            'job_note': 'new job note',
            'next': FULL_PATH
        }
        response = self.client.post( reverse('administrators:edit_course', args=[COURSE]) + NEXT, data=urlencode(data2), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        new_course = adminApi.get_course(course.id)

        self.assertEqual(new_course.id, course.id)
        self.assertEqual(new_course.code.id, course.code.id)
        self.assertEqual(new_course.number.id, course.number.id)
        self.assertEqual(new_course.section.id, course.section.id)
        self.assertEqual(new_course.term.id, course.term.id)
        self.assertEqual(new_course.name, data2['name'])
        self.assertEqual(new_course.job_description, data2['job_description'])
        self.assertEqual(new_course.job_note, data2['job_note'])

    def test_delete_course(self):
        print('\n- Test: delete a course')
        self.login()

        total_courses = len(adminApi.get_courses())

        course_id = 61

        FULL_PATH = reverse('administrators:all_courses') + '?page=2'
        NEXT = '?next=' + FULL_PATH
        data1 = {
            'course': course_id,
            'next': '/administrators/courses/al/?page=2'
        }
        response = self.client.post( reverse('administrators:delete_course'), data=urlencode(data1), content_type=ContentType )
        self.assertEqual(response.status_code, 404)

        data2 = {
            'course': course_id,
            'next': FULL_PATH
        }
        response = self.client.post( reverse('administrators:delete_course'), data=urlencode(data2), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, FULL_PATH)
        self.assertRedirects(response, response.url)

        #self.assertIsNone(adminApi.get_course(course_id))
        self.assertEqual( len(adminApi.get_courses()), total_courses - 1 )

    def test_delete_not_existing_course(self):
        print('\n- Test: delete a not existing course')
        self.login()

        response = self.client.post( reverse('administrators:delete_course'), data=urlencode({ 'course': 1000 }), content_type=ContentType )
        self.assertEqual(response.status_code, 404)

    def test_create_new_course_with_zero_base(self):
        print('\n- Test: create a new course with zero base')
        self.login()

        response = self.client.post( reverse('administrators:course_codes'), data=urlencode({ 'name': 'ABC' }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.post( reverse('administrators:course_numbers'), data=urlencode({ 'name': '111' }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.post( reverse('administrators:course_sections'), data=urlencode({ 'name': '501' }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.post( reverse('administrators:terms'), data=urlencode({ 'code': 'N', 'name': 'New Term', 'by_month': 4, 'max_hours': 192 }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        course_code = adminApi.get_course_code_by_name('ABC')
        course_number = adminApi.get_course_number_by_name('111')
        course_section = adminApi.get_course_section_by_name('501')
        term = adminApi.get_term_by_code('N')

        data = {
            'code': course_code.id,
            'number': course_number.id,
            'section': course_section.id,
            'name': 'New Course',
            'term': term.id
        }
        response = self.client.post( reverse('administrators:create_course'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)


class PreparationTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        print('\nPreparation testing has started ==>')
        cls.user = userApi.get_user(USERS[0], 'username')

    def login(self, username=None, password=None):
        if username and password:
            self.client.post(LOGIN_URL, data={'username': username, 'password': password})
        else:
            self.client.post(LOGIN_URL, data={'username': self.user.username, 'password': PASSWORD})

    def messages(self, res):
        return [m.message for m in get_messages(res.wsgi_request)]

    def test_view_url_exists_at_desired_location(self):
        print('\n- Test: view url exists at desired location')
        self.login()

        response = self.client.get( reverse('administrators:terms') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:degrees') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:programs') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:trainings') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:statuses') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:course_codes') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:course_numbers') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:course_sections') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:classifications') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:admin_emails') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:landing_pages') )
        self.assertEqual(response.status_code, 200)


    def test_terms(self):
        print('\n- Test: Display all terms and create a term')
        self.login()

        response = self.client.get( reverse('administrators:terms') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['terms']), 11 )
        self.assertFalse(response.context['form'].is_bound)

        data = {
            'code': 'WG',
            'name': 'Winter G',
            'by_month': 4,
            'max_hours': 192
        }
        response = self.client.post( reverse('administrators:terms'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:terms') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['terms']), 12 )
        self.assertEqual(response.context['terms'].last().code, data['code'])
        self.assertEqual(response.context['terms'].last().name, data['name'])
        self.assertEqual(response.context['terms'].last().by_month, data['by_month'])
        self.assertEqual(response.context['terms'].last().max_hours, data['max_hours'])

    def test_edit_term(self):
        print('\n- Test: edit term details')
        self.login()

        term_id = 1

        data = {
            'code': 'WG',
            'name': 'Winter G',
            'by_month': 4,
            'max_hours': 192
        }
        response = self.client.post( reverse('administrators:edit_term', args=[term_id]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:terms') )
        self.assertEqual(response.status_code, 200)
        terms = response.context['terms']

        found = 0
        for term in terms:
            if term.id == term_id:
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_term(self):
        print('\n- Test: delete a term')
        self.login()

        total_terms = len(adminApi.get_terms())

        data = {
            'code': 'WG',
            'name': 'Winter G',
            'by_month': 4,
            'max_hours': 192
        }
        response = self.client.post( reverse('administrators:terms'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:terms') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['terms']), total_terms + 1 )

        term_id = total_terms + 1
        response = self.client.post( reverse('administrators:delete_term'), data=urlencode({ 'term': term_id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:terms'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['terms']), total_terms)

        found = False
        for term in response.context['terms']:
            if term.id == term_id: found = True
        self.assertFalse(found)


    def test_degrees(self):
        print('\n- Test: Display all degrees and create a degree')
        self.login()

        response = self.client.get( reverse('administrators:degrees') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['degrees']), 11 )
        self.assertFalse(response.context['form'].is_bound)

        data = { 'name': 'Diploma' }
        response = self.client.post( reverse('administrators:degrees'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:degrees') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['degrees']), 12 )
        self.assertEqual(response.context['degrees'].last().name, data['name'])

    def test_edit_degree(self):
        print('\n- Test: edit degree details')
        self.login()

        slug = 'bachelor-of-arts'

        data = { 'name': 'updated degree' }
        response = self.client.post( reverse('administrators:edit_degree', args=[slug]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:degrees') )
        self.assertEqual(response.status_code, 200)
        degrees = response.context['degrees']

        found = 0
        for degree in degrees:
            if degree.slug == 'updated-degree':
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_degree(self):
        print('\n- Test: delete a degree')
        self.login()

        total_degrees = len(userApi.get_degrees())

        degree_id = 1
        response = self.client.post( reverse('administrators:delete_degree'), data=urlencode({ 'degree': degree_id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:degrees'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['degrees']), total_degrees - 1)

        found = False
        for degree in response.context['degrees']:
            if degree.id == degree_id: found = True
        self.assertFalse(found)

    def test_programs(self):
        print('\n- Test: Display all programs and create a program')
        self.login()

        response = self.client.get( reverse('administrators:programs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['programs']), 16 )
        self.assertFalse(response.context['form'].is_bound)

        data = { 'name': 'Master of Science in Animal' }
        response = self.client.post( reverse('administrators:programs'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:programs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['programs']), 17 )
        self.assertEqual(response.context['programs'].last().name, data['name'])

    def test_edit_program(self):
        print('\n- Test: edit program details')
        self.login()

        slug = 'master-of-science-in-applied-animal-biology-msc'

        data = { 'name': 'updated program' }
        response = self.client.post( reverse('administrators:edit_program', args=[slug]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:programs') )
        self.assertEqual(response.status_code, 200)
        programs = response.context['programs']

        found = 0
        for program in programs:
            if program.slug == 'updated-program':
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_program(self):
        print('\n- Test: delete a program')
        self.login()

        total_programs = len(userApi.get_programs())

        program_id = 1
        response = self.client.post( reverse('administrators:delete_program'), data=urlencode({ 'program': program_id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:programs'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['programs']), total_programs - 1)

        found = False
        for program in response.context['programs']:
            if program.id == program_id: found = True
        self.assertFalse(found)

    def test_trainings(self):
        print('\n- Test: Display all trainings and create a training')
        self.login()

        response = self.client.get( reverse('administrators:trainings') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['trainings']), 4 )
        self.assertFalse(response.context['form'].is_bound)

        data = { 'name': 'new training' }
        response = self.client.post( reverse('administrators:trainings'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:trainings') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['trainings']), 5 )
        self.assertEqual(response.context['trainings'].last().name, data['name'])

    def test_edit_training(self):
        print('\n- Test: edit training details')
        self.login()

        slug = 'workplace-violence-prevention-training'

        data = { 'name': 'updated training' }
        response = self.client.post( reverse('administrators:edit_training', args=[slug]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:trainings') )
        self.assertEqual(response.status_code, 200)
        trainings = response.context['trainings']

        found = 0
        for training in trainings:
            if training.slug == 'updated-training':
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_training(self):
        print('\n- Test: delete a training')
        self.login()

        total_trainings = len(userApi.get_trainings())

        training_id = 1
        response = self.client.post( reverse('administrators:delete_training'), data=urlencode({ 'training': training_id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:trainings'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['trainings']), total_trainings - 1)

        found = False
        for training in response.context['trainings']:
            if training.id == training_id: found = True
        self.assertFalse(found)

    def test_statuses(self):
        print('\n- Test: Display all statuss and create a status')
        self.login()

        response = self.client.get( reverse('administrators:statuses') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['statuses']), 9 )
        self.assertFalse(response.context['form'].is_bound)

        data = { 'name': 'Full Professor' }
        response = self.client.post( reverse('administrators:statuses'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:statuses') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['statuses']), 10 )
        self.assertEqual(response.context['statuses'].last().name, data['name'])

    def test_edit_status(self):
        print('\n- Test: edit status details')
        self.login()

        slug = 'undergraduate-student'

        data = { 'name': 'updated status' }
        response = self.client.post( reverse('administrators:edit_status', args=[slug]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:statuses') )
        self.assertEqual(response.status_code, 200)
        statuss = response.context['statuses']

        found = 0
        for status in statuss:
            if status.slug == 'updated-status':
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_status(self):
        print('\n- Test: delete a status')
        self.login()

        total_statuses = len(userApi.get_statuses())

        status_id = 1
        response = self.client.post( reverse('administrators:delete_status'), data=urlencode({ 'status': status_id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:statuses'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['statuses']), total_statuses - 1)

        found = False
        for status in response.context['statuses']:
            if status.id == status_id: found = True
        self.assertFalse(found)

    def test_course_codes(self):
        print('\n- Test: Display all course_codes and create a course_code')
        self.login()

        response = self.client.get( reverse('administrators:course_codes') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['course_codes']), 6 )
        self.assertFalse(response.context['form'].is_bound)

        data = { 'name': 'ZBC' }
        response = self.client.post( reverse('administrators:course_codes'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:course_codes') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['course_codes']), 7 )
        self.assertEqual(response.context['course_codes'].last().name, data['name'])

    def test_edit_course_code(self):
        print('\n- Test: edit course_code details')
        self.login()

        course_code_id = 1

        data = { 'name': 'CSC' }
        response = self.client.post( reverse('administrators:edit_course_code', args=[course_code_id]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:course_codes') )
        self.assertEqual(response.status_code, 200)
        course_codes = response.context['course_codes']

        found = 0
        for course_code in course_codes:
            if course_code.name == 'CSC':
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_course_code(self):
        print('\n- Test: delete a course_code')
        self.login()

        data = { 'name': 'ZBC' }
        response = self.client.post( reverse('administrators:course_codes'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        course_code = adminApi.get_course_code_by_name(data['name'])
        response = self.client.post( reverse('administrators:delete_course_code'), data=urlencode({ 'course_code': course_code.id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:course_codes'))
        self.assertEqual(response.status_code, 200)

        found = False
        for c in response.context['course_codes']:
            if c.id == course_code.id: found = True
        self.assertFalse(found)

    def test_course_numbers(self):
        print('\n- Test: Display all course_numbers and create a course_number')
        self.login()

        response = self.client.get( reverse('administrators:course_numbers') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['course_numbers']), 74 )
        self.assertFalse(response.context['form'].is_bound)

        data = { 'name': '530' }
        response = self.client.post( reverse('administrators:course_numbers'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:course_numbers') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['course_numbers']), 75 )
        self.assertEqual(response.context['course_numbers'].last().name, data['name'])

    def test_edit_course_number(self):
        print('\n- Test: edit course_number details')
        self.login()

        course_number_id = 1

        data = { 'name': '111' }
        response = self.client.post( reverse('administrators:edit_course_number', args=[course_number_id]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:course_numbers') )
        self.assertEqual(response.status_code, 200)
        course_numbers = response.context['course_numbers']

        found = 0
        for course_number in course_numbers:
            if course_number.name == '111':
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_course_number(self):
        print('\n- Test: delete a course_number')
        self.login()


        data = { 'name': '530' }
        response = self.client.post( reverse('administrators:course_numbers'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        course_number = adminApi.get_course_number_by_name(data['name'])

        response = self.client.post( reverse('administrators:delete_course_number'), data=urlencode({ 'course_number': course_number.id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:course_numbers'))
        self.assertEqual(response.status_code, 200)

        found = False
        for c in response.context['course_numbers']:
            if c.id == course_number.id: found = True
        self.assertFalse(found)

    def test_course_sections(self):
        print('\n- Test: Display all course_sections and create a course_section')
        self.login()

        response = self.client.get( reverse('administrators:course_sections') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['course_sections']), 22 )
        self.assertFalse(response.context['form'].is_bound)

        data = { 'name': '99Z' }
        response = self.client.post( reverse('administrators:course_sections'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:course_sections') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['course_sections']), 23 )
        self.assertEqual(response.context['course_sections'].last().name, data['name'])

    def test_edit_course_section(self):
        print('\n- Test: edit course_section details')
        self.login()

        course_section_id = 1

        data = { 'name': '115' }
        response = self.client.post( reverse('administrators:edit_course_section', args=[course_section_id]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:course_sections') )
        self.assertEqual(response.status_code, 200)
        course_sections = response.context['course_sections']

        found = 0
        for course_section in course_sections:
            if course_section.name == '115':
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_course_section(self):
        print('\n- Test: delete a course_section')
        self.login()

        data = { 'name': '99Z' }
        response = self.client.post( reverse('administrators:course_sections'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        course_section = adminApi.get_course_section_by_name(data['name'])

        response = self.client.post( reverse('administrators:delete_course_section'), data=urlencode({ 'course_section': course_section.id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:course_sections'))
        self.assertEqual(response.status_code, 200)

        found = False
        for c in response.context['course_sections']:
            if c.id == course_section.id: found = True
        self.assertFalse(found)

    def test_classifications(self):
        print('\n- Test: Display all classifications and create a classification')
        self.login()

        response = self.client.get( reverse('administrators:classifications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['classifications']), 6 )
        self.assertFalse(response.context['form'].is_bound)

        data = {
            'year': '2020',
            'name': 'Marker 2',
            'wage': '16.05',
            'is_active': True
        }
        response = self.client.post( reverse('administrators:classifications'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:classifications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['classifications']), 7 )
        self.assertEqual(response.context['classifications'].latest('pk').name, data['name'])


    def test_edit_classification(self):
        print('\n- Test: edit classification details')
        self.login()

        slug = '2019-marker'

        data = {
            'year': '2020',
            'name': 'Marker 2',
            'wage': '16.05',
            'is_active': False
        }
        response = self.client.post( reverse('administrators:edit_classification', args=[slug]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:classifications') )
        self.assertEqual(response.status_code, 200)
        classifications = response.context['classifications']

        found = 0
        for classification in classifications:
            if classification.slug == '2020-marker-2':
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_classification(self):
        print('\n- Test: delete a classification')
        self.login()

        data = {
            'year': '2020',
            'name': 'Marker 2',
            'wage': '16.05',
            'is_active': True
        }
        response = self.client.post( reverse('administrators:classifications'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        classification = adminApi.get_classification_by_slug('2020-marker-2')

        response = self.client.post( reverse('administrators:delete_classification'), data=urlencode({ 'classification': classification.id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:classifications'))
        self.assertEqual(response.status_code, 200)

        found = False
        for c in response.context['classifications']:
            if c.id == classification.id: found = True
        self.assertFalse(found)


    def test_admin_emails(self):
        print('\n- Test: Display all admin emails and create an admin email')
        self.login()

        response = self.client.get( reverse('administrators:admin_emails') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['admin_emails']), 3 )
        self.assertFalse(response.context['form'].is_bound)

        data = {
            'title': 'Congratulations',
            'message': 'Hello',
            'type': 'offer'
        }
        response = self.client.post( reverse('administrators:admin_emails'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:admin_emails') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['admin_emails']), 4 )
        self.assertEqual(response.context['admin_emails'].latest('pk').title, data['title'])
        self.assertEqual(response.context['admin_emails'].latest('pk').message, data['message'])
        self.assertEqual(response.context['admin_emails'].latest('pk').type, data['type'])


    def test_edit_admin_email(self):
        print('\n- Test: edit admin email details')
        self.login()

        slug = 'type-1'
        data = {
            'title': 'Congratulations',
            'message': 'Hello',
            'type': 'Type 111'
        }
        response = self.client.post( reverse('administrators:edit_admin_email', args=[slug]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:admin_emails') )
        self.assertEqual(response.status_code, 200)
        admin_emails = response.context['admin_emails']

        found = 0
        for email in admin_emails:
            if email.slug == 'type-111':
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_admin_email(self):
        print('\n- Test: delete a admin email')
        self.login()

        data = {
            'title': 'Congratulations',
            'message': 'Hello',
            'type': 'Offer 2'
        }
        response = self.client.post( reverse('administrators:admin_emails'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        admin_email = adminApi.get_admin_email_by_slug('offer-2')

        response = self.client.post( reverse('administrators:delete_admin_email'), data=urlencode({ 'admin_email': admin_email.id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:admin_emails'))
        self.assertEqual(response.status_code, 200)

        found = False
        for e in response.context['admin_emails']:
            if e.id == admin_email.id: found = True
        self.assertFalse(found)


    def test_landing_pages(self):
        print('\n- Test: Display all landin page contents and create a landing page content')
        self.login()

        response = self.client.get( reverse('administrators:landing_pages') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['landing_pages']), 1 )
        self.assertFalse(response.context['form'].is_bound)

        data = {
            'title': 'Title',
            'message': 'Message',
            'notice': 'Notice',
            'is_visible': False
        }
        response = self.client.post( reverse('administrators:landing_pages'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:landing_pages') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual( len(response.context['landing_pages']), 2 )
        self.assertEqual(response.context['landing_pages'].latest('pk').title, data['title'])
        self.assertEqual(response.context['landing_pages'].latest('pk').message, data['message'])
        self.assertEqual(response.context['landing_pages'].latest('pk').notice, data['notice'])
        self.assertFalse(response.context['landing_pages'].latest('pk').is_visible)


    def test_edit_landing_page(self):
        print('\n- Test: edit landing page details')
        self.login()

        landing_page_id = 1
        data = {
            'title': 'Title 2',
            'message': 'Message 2',
            'notice': 'Notice 2',
            'is_visible': False
        }
        response = self.client.post( reverse('administrators:edit_landing_page', args=[landing_page_id]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('administrators:landing_pages') )
        self.assertEqual(response.status_code, 200)
        admin_emails = response.context['landing_pages']

        found = 0
        for email in admin_emails:
            if email.id == landing_page_id:
                found = 1
                break
        self.assertEqual(found, 1)


    def test_delete_landing_page(self):
        print('\n- Test: delete a landing page')
        self.login()

        data = {
            'title': 'Title 2',
            'message': 'Message 2',
            'notice': 'Notice 2',
            'is_visible': False
        }
        response = self.client.post( reverse('administrators:landing_pages'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        landing_page = adminApi.get_landing_page(2)

        response = self.client.post( reverse('administrators:delete_landing_page'), data=urlencode({ 'landing_page': landing_page.id }), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:landing_pages'))
        self.assertEqual(response.status_code, 200)

        found = False
        for l in response.context['landing_pages']:
            if l.id == landing_page.id: found = True
        self.assertFalse(found)


class AdminHRTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        print('\nAdmin HR testing has started ==>')
        cls.user = userApi.get_user(USERS[0], 'username')

    def login(self, username=None, password=None):
        if username and password:
            self.client.post(LOGIN_URL, data={'username': username, 'password': password})
        else:
            self.client.post(LOGIN_URL, data={'username': self.user.username, 'password': PASSWORD})

    def messages(self, res):
        return [m.message for m in get_messages(res.wsgi_request)]

    def test_view_url_exists_at_desired_location(self):
        self.login('user3.admin', 'password')

        response = self.client.get( reverse('administrators:index') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:accepted_applications') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:create_session') )
        self.assertEqual(response.status_code, 403)

        self.login(USERS[1], 'password')

        response = self.client.get( reverse('administrators:index') )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('administrators:accepted_applications') )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('administrators:create_session') )
        self.assertEqual(response.status_code, 403)

        self.login(USERS[2], 'password')

        response = self.client.get( reverse('administrators:index') )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('administrators:accepted_applications') )
        self.assertEqual(response.status_code, 403)

        response = self.client.get( reverse('administrators:create_session') )
        self.assertEqual(response.status_code, 403)

        self.login()

        response = self.client.get( reverse('administrators:index') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:accepted_applications') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('administrators:create_session') )
        self.assertEqual(response.status_code, 200)

    def test_index(self):
        print('\n- Test: index')
        self.login('user3.admin', 'password')

        response = self.client.get( reverse('administrators:index') )
        self.assertEqual(response.status_code, 200)
        self.assertFalse('archived_sessions' in response.context.keys())
        self.assertTrue('accepted_apps' in response.context.keys())
        self.assertEqual(response.context['accepted_apps'].count(), 6)

    def test_accepted_applications(self):
        print('\n- Test: Display applications accepted by students')
        self.login('user3.admin', 'password')

        response = self.client.get( reverse('administrators:accepted_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'user3.admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['HR'])
        self.assertEqual( len(response.context['apps']), 5)

    def test_admin_docs(self):
        print('\n- Test: Admin or HR can have update admin docs')
        self.login('user3.admin', 'password')
        app_id = 1

        data1 = {
            'application': app_id,
            'pin': '1237',
            'tasm': True,
            'eform': 'af3343',
            'speed_chart': 'adsf',
            'processing_note': 'this is a processing note',
            'next': '/administrators/applications/Accepted/?page=2'
        }
        response = self.client.post(reverse('administrators:accepted_applications') + '?page=2', data=urlencode(data1), content_type=ContentType)
        self.assertEqual(response.status_code, 404)

        # pin is an error
        data2 = {
            'application': app_id,
            'pin': '12377',
            'tasm': True,
            'eform': 'af3343',
            'speed_chart': 'adsf',
            'processing_note': 'this is a processing note',
            'next': reverse('administrators:accepted_applications') + '?page=2'
        }
        response = self.client.post(reverse('administrators:accepted_applications') + '?page=2', data=urlencode(data2), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('An error occurred' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:accepted_applications') + '?page=2')
        self.assertRedirects(response, response.url)

        data3 = {
            'application': app_id,
            'pin': '1237',
            'tasm': True,
            'eform': 'af3343',
            'speed_chart': 'adsf',
            'processing_note': 'this is a processing note',
            'next': reverse('administrators:accepted_applications') + '?page=2'
        }
        response = self.client.post(reverse('administrators:accepted_applications') + '?page=2', data=urlencode(data3), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:accepted_applications') + '?page=2')
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:accepted_applications') + '?page=2')
        self.assertEqual(response.status_code, 200)
        accepted_applications = response.context['apps']

        app = None
        for appl in accepted_applications:
            if appl.id == app_id:
                app = appl

        self.assertTrue(app.id, app_id)
        self.assertTrue(app.admindocuments.pin, data3['pin'])
        self.assertTrue(app.admindocuments.tasm, data3['tasm'])
        self.assertTrue(app.admindocuments.eform, data3['eform'])
        self.assertTrue(app.admindocuments.speed_chart, data3['speed_chart'])
        self.assertEqual( len(app.admindocuments.admindocumentsuser_set.all()), 1 )

        admin_user = app.admindocuments.admindocumentsuser_set.first()
        self.assertEqual(admin_user.user, 'User3 Admin')
        self.assertEqual(admin_user.document.application.id, app_id)
        self.assertEqual(admin_user.created_at.strftime('%Y-%m-%d'), datetime.now().strftime('%Y-%m-%d'))

    def test_admin_docs_update_history(self):
        print('\n- Test: Admin or HR can have update admin docs with history')
        self.login('user3.admin', 'password')
        app_id = 1
        data1 = {
            'application': app_id,
            'pin': '1237',
            'tasm': True,
            'eform': '',
            'speed_chart': 'adsf',
            'processing_note': '',
            'next': reverse('administrators:accepted_applications') + '?page=2'
        }
        response = self.client.post(reverse('administrators:accepted_applications') + '?page=2', data=urlencode(data1), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:accepted_applications') + '?page=2')
        self.assertRedirects(response, response.url)

        data2 = {
            'application': app_id,
            'pin': '1237',
            'tasm': True,
            'eform': 'af3343',
            'speed_chart': 'adsf',
            'processing_note': 'this is a processing note',
            'next': reverse('administrators:accepted_applications') + '?page=2'
        }
        response = self.client.post(reverse('administrators:accepted_applications') + '?page=2', data=urlencode(data2), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:accepted_applications') + '?page=2')
        self.assertRedirects(response, response.url)

        self.login('user2.admin', 'password')

        data3 = {
            'application': app_id,
            'pin': '1255',
            'tasm': False,
            'eform': 'af3343',
            'speed_chart': 'adsf',
            'processing_note': 'this is a processing note',
            'next': reverse('administrators:accepted_applications') + '?page=2'
        }
        response = self.client.post(reverse('administrators:accepted_applications') + '?page=2', data=urlencode(data3), content_type=ContentType)
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('administrators:accepted_applications') + '?page=2')
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('administrators:accepted_applications') + '?page=2')
        self.assertEqual(response.status_code, 200)
        accepted_applications = response.context['apps']

        app = None
        for appl in accepted_applications:
            if appl.id == app_id:
                app = appl

        self.assertTrue(app.id, app_id)
        self.assertTrue(app.admindocuments.pin, data3['pin'])
        self.assertFalse(app.admindocuments.tasm, data3['tasm'])
        self.assertTrue(app.admindocuments.eform, data3['eform'])
        self.assertTrue(app.admindocuments.speed_chart, data3['speed_chart'])
        self.assertEqual( len(app.admindocuments.admindocumentsuser_set.all()), 3 )

        admin_users = []
        for admin_user in app.admindocuments.admindocumentsuser_set.all():
            admin_users.append(admin_user.user)
            self.assertEqual(admin_user.created_at.strftime('%Y-%m-%d'), datetime.now().strftime('%Y-%m-%d'))

        self.assertEqual(admin_users, ['User2 Admin', 'User3 Admin', 'User3 Admin'])
