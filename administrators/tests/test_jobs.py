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

from administrators.tests.test_sessions import LOGIN_URL, ContentType, DATA, PASSWORD, USERS,  SESSION, JOB

PREPARE_JOB = '?next=' + reverse('administrators:prepare_jobs') + '?page=2&p=Prepare%20Jobs'
INSTRUCTOR_JOB = '?next=' + reverse('administrators:instructor_jobs') + '?page=2&p=Jobs%20by%20Instructor'
STUDENT_JOB = '?next=' + reverse('administrators:student_jobs') + '?page=2&p=Jobs%20by%20Student&t=all'

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
        print('- Test: view url exists at desired location')
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
        print('- Test: display a job')
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
        print('- Test: display all prepare jobs')
        self.login()

        response = self.client.get( reverse('administrators:prepare_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, self.user.username)
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['jobs']), settings.PAGE_SIZE )
        self.assertEqual( len(adminApi.get_jobs()), 450 )

    def test_edit_job(self):
        print('- Test: edit a job')
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
        print('- Test: add instructors')
        self.login()

        job = adminApi.get_job_by_session_slug_job_slug(SESSION, JOB)
        self.assertEqual( len(job.instructors.all()), 2 )

        data1 = {
            'instructors': ['15']
        }
        response = self.client.post( reverse('administrators:add_job_instructors', args=[SESSION, JOB]), data=urlencode(data1, True), content_type=ContentType )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(content['status'], 'success')
        self.assertTrue('Success' in content['message'])

        job = adminApi.get_job_by_session_slug_job_slug(SESSION, JOB)
        self.assertEqual( len(job.instructors.all()), 3 )

        data2 = {
            'instructors': ['11']
        }
        response = self.client.post( reverse('administrators:add_job_instructors', args=[SESSION, JOB]), data=urlencode(data2, True), content_type=ContentType )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(content['status'], 'success')
        self.assertTrue('Success' in content['message'])

        job = adminApi.get_job_by_session_slug_job_slug(SESSION, JOB)
        self.assertEqual( len(job.instructors.all()), 4 )

        data3 = {
            'instructors': ['11']
        }
        response = self.client.post( reverse('administrators:add_job_instructors', args=[SESSION, JOB]), data=urlencode(data3, True), content_type=ContentType )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(content['status'], 'error')
        self.assertTrue('An error occurred' in content['message'])

        job = adminApi.get_job_by_session_slug_job_slug(SESSION, JOB)
        self.assertEqual( len(job.instructors.all()), 4 )


    def test_delete_instructors(self):
        print('- Test: delete instructors')
        self.login()
        job = adminApi.get_job_by_session_slug_job_slug(SESSION, JOB)
        self.assertEqual( len(job.instructors.all()), 2 )

        data1 = {
            'instructors': ['15']
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
        self.assertEqual( len(job.instructors.all()), 1 )

        data3 = {
            'instructors': ['56']
        }
        response = self.client.post( reverse('administrators:delete_job_instructors', args=[SESSION, JOB]), data=urlencode(data3, True), content_type=ContentType )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(content['status'], 'error')
        self.assertTrue('An error occurred' in content['message'])

    def test_edit_not_existing_job(self):
        print('- Test: display all progress jobs')
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
        print('- Test: display all progress jobs')
        self.login()

        response = self.client.get( reverse('administrators:progress_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, self.user.username)
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['jobs']), settings.PAGE_SIZE )
        self.assertEqual( len(adminApi.get_jobs()), 450 )

    def test_instructor_jobs(self):
        print('- Test: display all instructor jobs')
        self.login()

        response = self.client.get( reverse('administrators:instructor_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, self.user.username)
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['users']), 50 )
        self.assertEqual( len(userApi.get_users_by_role('Instructor')), 57 )


    def test_student_jobs(self):
        print('- Test: display all student jobs')
        self.login()

        response = self.client.get( reverse('administrators:student_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, self.user.username)
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual( len(response.context['users']), settings.PAGE_SIZE )
        self.assertEqual( len(userApi.get_users_by_role('Student')), 99 )

    def test_show_job_applications(self):
        print('- Test: display a job applications')
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
        print('- Test: display jobs that an instructor has')
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

    def test_student_jobs_details1(self):
        print('- Test: display jobs that a student has - user100.test')
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

        offered_app_ids = [1, 22, 24, 25]
        self.assertEqual(len(response.context['offered_apps']), 4)

        c1 = 0
        for app in response.context['offered_apps']:
            self.assertEqual(app.id, offered_app_ids[c1])
            c1 += 1

        accepted_app_ids = [1, 24]
        self.assertEqual(len(response.context['accepted_apps']), 2)

        c2 = 0
        for app in response.context['accepted_apps']:
            self.assertEqual(app.id, accepted_app_ids[c2])
            c2 += 1

        self.assertEqual(response.context['tab_urls']['all'], '/administrators/students/user100.test/jobs/?next=/administrators/jobs/student/?page=2&p=Jobs by Student&t=all')
        self.assertEqual(response.context['tab_urls']['offered'], '/administrators/students/user100.test/jobs/?next=/administrators/jobs/student/?page=2&p=Jobs by Student&t=offered')
        self.assertEqual(response.context['tab_urls']['accepted'], '/administrators/students/user100.test/jobs/?next=/administrators/jobs/student/?page=2&p=Jobs by Student&t=accepted')
        self.assertEqual(response.context['current_tab'], 'all')
        self.assertEqual(response.context['app_status'], {'none': '0', 'applied': '0', 'selected': '1', 'offered': '2', 'accepted': '3', 'declined': '4', 'cancelled': '5'})
        self.assertEqual(response.context['next'], '/administrators/jobs/student/?page=2')

        apps = response.context['apps']
        num_offered = 0
        num_accepted = 0
        for app in apps:
            if app.offered is not None: num_offered += 1
            if app.accepted is not None: num_accepted += 1

        total_assigned_hours = response.context['total_assigned_hours']
        self.assertEqual( total_assigned_hours['offered'], {'2019-W1': 100.0, '2019-W2': 20.0, '2019-S': 40.0} )
        self.assertEqual( total_assigned_hours['accepted'], {'2019-W1': 30.0, '2019-W2': 50.0} )
        self.assertEqual(len(apps), 7)
        self.assertEqual(num_offered, 4)
        self.assertEqual(num_accepted, 3)


    def test_student_jobs_details2(self):
        print('- Test: display jobs that a student has - user66.test')
        self.login()

        user = userApi.get_user('user66.test', 'username')

        response = self.client.get( reverse('administrators:student_jobs_details', args=[ user.username ]) + STUDENT_JOB )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, USERS[0])
        self.assertEqual(response.context['loggedin_user'].roles, ['Admin'])
        self.assertEqual(response.context['user'].username, user.username)

        offered_app_ids = [7, 8]
        self.assertEqual(len(response.context['offered_apps']), 2)

        c1 = 0
        for app in response.context['offered_apps']:
            self.assertEqual(app.id, offered_app_ids[c1])
            c1 += 1

        accepted_app_ids = [7, 8]
        self.assertEqual(len(response.context['accepted_apps']), 2)

        c2 = 0
        for app in response.context['accepted_apps']:
            self.assertEqual(app.id, accepted_app_ids[c2])
            c2 += 1

        self.assertEqual(response.context['tab_urls']['all'], '/administrators/students/user66.test/jobs/?next=/administrators/jobs/student/?page=2&p=Jobs by Student&t=all')
        self.assertEqual(response.context['tab_urls']['offered'], '/administrators/students/user66.test/jobs/?next=/administrators/jobs/student/?page=2&p=Jobs by Student&t=offered')
        self.assertEqual(response.context['tab_urls']['accepted'], '/administrators/students/user66.test/jobs/?next=/administrators/jobs/student/?page=2&p=Jobs by Student&t=accepted')
        self.assertEqual(response.context['current_tab'], 'all')
        self.assertEqual(response.context['app_status'], {'none': '0', 'applied': '0', 'selected': '1', 'offered': '2', 'accepted': '3', 'declined': '4', 'cancelled': '5'})
        self.assertEqual(response.context['next'], '/administrators/jobs/student/?page=2')

        apps = response.context['apps']
        num_offered = 0
        num_accepted = 0
        for app in apps:
            if app.offered is not None: num_offered += 1
            if app.accepted is not None: num_accepted += 1

        total_assigned_hours = response.context['total_assigned_hours']
        self.assertEqual( total_assigned_hours['offered'], {'2019-W1': 45.0, '2019-W2': 30.0} )
        self.assertEqual( total_assigned_hours['accepted'], {'2019-W1': 45.0, '2019-W2': 30.0} )
        self.assertEqual(len(apps), 5)
        self.assertEqual(num_offered, 2)
        self.assertEqual(num_accepted, 2)
