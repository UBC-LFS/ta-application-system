from django.test import TestCase
from django.urls import reverse
from django.contrib.messages import get_messages
from urllib.parse import urlencode

from administrators.models import *
from administrators import api
from users import api as userApi

ContentType='application/x-www-form-urlencoded'

DATA = [
    'administrators/fixtures/application_status.json',
    'administrators/fixtures/applications.json',
    'administrators/fixtures/applicationstatus.json',
    'administrators/fixtures/course_codes.json',
    'administrators/fixtures/course_numbers.json',
    'administrators/fixtures/course_sections.json',
    'administrators/fixtures/courses.json',
    'administrators/fixtures/job_instructors.json',
    'administrators/fixtures/jobs.json',
    'administrators/fixtures/sessions.json',
    'administrators/fixtures/terms.json',
    'users/fixtures/confidentialities.json',
    'users/fixtures/degrees.json',
    'users/fixtures/profile_roles.json',
    'users/fixtures/profiles.json',
    'users/fixtures/programs.json',
    'users/fixtures/resumes.json',
    'users/fixtures/roles.json',
    'users/fixtures/statuses.json',
    'users/fixtures/trainings.json',
    'users/fixtures/users.json'
]


class SessionTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        print('\nSession testing has started ==>')

    def login(self, username, password):
        self.client.post('/accounts/local_login/', data={'username': username, 'password': password})

    def test_view_url_exists_at_desired_location(self):
        self.login('admin', '12')
        response = self.client.get( reverse('administrators:sessions') )
        self.assertEqual(response.status_code, 200)

    def test_create_session(self):
        """ Test: create a session"""
        self.login('admin', '12')
        data = {
            'year': '2020',
            'term': '2',
            'title': 'New TA Application',
            'description': 'new description',
            'note': 'new note',
            'is_active': 'False'
        }
        sessions = api.get_sessions_by_year(data['year'])
        self.assertEqual( sessions.count(), 0 ) # no session yet

        response = self.client.post(reverse('administrators:sessions'), data=urlencode(data), content_type=ContentType)
        self.assertEqual(response.status_code, 302) # Redirect to create_session_confirmation
        self.assertRedirects(response, response.url)

        response = self.client.get(response.url)
        session = self.client.session
        self.assertEqual(session['session_form_data'], data)
        self.assertEqual(response.context['courses'].count(), 6)

        data['courses'] = [ str(course.id) for course in response.context['courses'] ]
        response = self.client.post(reverse('administrators:create_session_confirmation'), data=urlencode(data, True), content_type=ContentType)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue('Success' in messages[0]) # Check a success message
        self.assertEqual(response.status_code, 302) # Redirect to users index
        self.assertRedirects(response, response.url)

        sessions = api.get_sessions_by_year(data['year'])
        self.assertEqual( sessions.count(), 1 ) # 1 session created
        self.assertEqual(sessions[0].year, data['year'])
        self.assertEqual(sessions[0].term.name, 'Winter Term 1')
        self.assertEqual(sessions[0].title, data['title'])
        self.assertEqual(sessions[0].description, data['description'])
        self.assertEqual(sessions[0].is_active, eval(data['is_active']))
        self.assertEqual(sessions[0].job_set.count(), 6)


    def test_delte_session(self):
        """ Test: delete a session """
        self.login('admin', '12')
        session_id = '6'
        data = { 'session': session_id }
        response = self.client.post(reverse('administrators:delete_session'), data=urlencode(data), content_type=ContentType)

        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue('Success' in messages[0]) # Check a success message
        self.assertEqual(response.status_code, 302) # Redirect to sessions page
        self.assertRedirects(response, response.url)
        self.assertFalse( api.session_exists(session_id) ) # session does not exist

    def test_edit_session(self):
        self.login('admin', '12')
        session_id = '6'
        session = api.get_session(session_id)
        courses = api.get_courses_by_term('6')
        data = {
            'session': session_id,
            'year': '2019',
            'term': '6',
            'title': 'Edited TA Application',
            'description': 'Edited description',
            'note': 'Edited note',
            'is_active': 'True',
            'courses': [ str(courses[0].id), str(courses[1].id) ]
        }

        response = self.client.post(reverse('administrators:edit_session', args=[session.slug]), data=urlencode(data, True), content_type=ContentType)
        self.assertEqual(response.status_code, 302) # Redirect to session details
        self.assertRedirects(response, response.url)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue('Success' in messages[0]) # Check a success message

        updated_session = api.get_session(session_id)
        self.assertEqual( updated_session.id, int(data['session']) )
        self.assertEqual( updated_session.year, data['year'] )
        self.assertEqual( updated_session.title, data['title'] )
        self.assertEqual( updated_session.description, data['description'] )
        self.assertEqual( updated_session.note, data['note'] )
        self.assertEqual( updated_session.is_active, eval(data['is_active']) )
        self.assertEqual( updated_session.job_set.count(), len(data['courses']) )



class JobTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        print('\nJob testing has started ==>')

    def login(self, username, password):
        self.client.post('/accounts/local_login/', data={'username': username, 'password': password})

    def apply_jobs(self, user, active_sessions):
        """ Students apply jobs """
        num_applications = 0
        num = 0
        for session in active_sessions:
            for job in session.job_set.all():
                if num % 2 == 0:
                    data = {
                        'applicant': user.id,
                        'job': str(job.id),
                        'supervisor_approval': 'True',
                        'how_qualified': '4',
                        'how_interested': '4',
                        'availability': 'True',
                        'availability_note': 'good'
                    }
                    response = self.client.post(reverse('home:show_job', args=[session.slug, job.course.slug]), data=urlencode(data, True), content_type=ContentType)
                    self.assertEqual(response.status_code, 302) # Redirect to session details
                    #self.assertRedirects(response, response.url)
                    messages = [m.message for m in get_messages(response.wsgi_request)]
                    self.assertTrue('Success' in messages[num_applications]) # Check a success message
                    num_applications += 1
                num += 1
        return num_applications

    def offer_jobs(self, applications):
        """ Admins send a job offer """

        num = 0
        num_offers = 0
        for app in applications:
            if num % 2 == 1:
                data = {
                    'applicant': str(app.applicant.id),
                    'assigned': ApplicationStatus.OFFERED,
                    'assigned_hours': '30.0'
                }
                response = self.client.post(reverse('administrators:offer_job', args=[app.job.session.slug, app.job.course.slug]), data=urlencode(data), content_type=ContentType)
                self.assertEqual(response.status_code, 302)
                #self.assertRedirects(response, response.url)
                messages = [m.message for m in get_messages(response.wsgi_request)]
                self.assertTrue('Success' in messages[num_offers]) # Check a success message

                # Check status of the application
                for st in app.status.all():
                    if st.assigned == ApplicationStatus.OFFERED:
                        self.assertEqual(st.assigned, data['assigned'])
                        self.assertEqual(st.assigned_hours, float(data['assigned_hours']))
                num_offers += 1
            num += 1
        return num_offers

    def test_view_url_exists_at_desired_location(self):
        self.login('admin', '12')
        response = self.client.get( reverse('administrators:jobs') )
        self.assertEqual(response.status_code, 200)

    def test_jobs(self):
        """ Test: display all jobs """
        self.login('admin', '12')
        response = self.client.get( reverse('administrators:jobs') )
        self.assertEqual(response.status_code, 200) # check jobs page
        self.assertEqual(response.context['loggedin_user']['username'], 'admin')
        self.assertEqual( len(response.context['jobs']), 21 )

    def test_edit_job(self):
        """ Test: edit a job """
        self.login('admin', '12')
        session_slug = '2018-w1'
        job_slug = 'lfs-100-001-introduction-to-land-food-and-community-w1'

        job = api.get_session_job_by_slug(session_slug, job_slug)
        job_id = '1'
        data = {
            'job': job_id,
            'title': 'Updated title',
            'description': 'Updated description',
            'qualification': 'Updated qualification',
            'note': 'Updated note',
            'instructors': ['8'],
            'is_active': 'False'
        }
        response = self.client.post(reverse('administrators:edit_job', args=[session_slug, job_slug]), data=urlencode(data, True), content_type=ContentType)

        self.assertEqual(response.status_code, 302) # Redirect to job details
        self.assertRedirects(response, response.url)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue('Success' in messages[0]) # Check a success message

        job = api.get_session_job_by_slug(session_slug, job_slug)
        self.assertEqual(job.id, int(data['job']))
        self.assertEqual(job.title, data['title'])
        self.assertEqual(job.description, data['description'])
        self.assertEqual(job.qualification, data['qualification'])
        self.assertEqual(job.note, data['note'])
        self.assertEqual(job.instructors.count(), len(data['instructors']) )
        self.assertEqual( [instructor.username for instructor in job.instructors.all()], ['test.user8'] )
        self.assertEqual(job.is_active, eval(data['is_active']))


    def test_create_applications(self):
        """ Test: applicants can apply to each job """
        user_id = '15'
        user = userApi.get_user(user_id)
        self.login(user.username, '12')
        response = self.client.get( reverse('home:index') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user']['username'], user.username)
        active_sessions = response.context['active_sessions']
        num_applications = self.apply_jobs(user, active_sessions) # Apply
        applications = api.get_applications_applied_by_student(user)
        self.assertEquals( len(applications),  num_applications )



    def test_offer_job(self):
        """ Test: offer a job to each applicant """

        # Login with a student
        user_id = '15'
        user = userApi.get_user(user_id)
        self.login(user.username, '12')
        response = self.client.get( reverse('home:index') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user']['username'], user.username)
        active_sessions = response.context['active_sessions']

        num_applications = self.apply_jobs(user, active_sessions) # a student has applied
        applications = api.get_applications_applied_by_student(user)
        self.assertEquals( len(applications),  num_applications )

        # Login with an admin
        self.login('admin', '12')
        user_applications = api.get_applications_applied_by_student(user)

        # send job offers
        num_offers = self.offer_jobs(user_applications) # an admin has offered
        offers = api.get_offered_applications_by_student(user)
        self.assertEquals( len(offers),  num_offers )


    def test_accept_jobs(self):
        """ Test: accept job offers """

        # Login with a student
        user_id = '15'
        user = userApi.get_user(user_id)
        self.login(user.username, '12')
        response = self.client.get( reverse('home:index') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user']['username'], user.username)
        active_sessions = response.context['active_sessions']

        num_applications = self.apply_jobs(user, active_sessions) # a student has applied
        applications = api.get_applications_applied_by_student(user)
        self.assertEquals( len(applications),  num_applications )

        # Login with an admin
        self.login('admin', '12')
        user_applications = api.get_applications_applied_by_student(user)

        # send job offers
        num_offers = self.offer_jobs(user_applications) # an admin has offered
        offers = api.get_offered_applications_by_student(user)
        self.assertEquals( len(offers),  num_offers )

        # Login with a student again
        self.login(user.username, '12')

        # accept job offers
        for offer in offers:
            session_slug = offer.job.session.slug
            job_slug = offer.job.course.slug
            response = self.client.get( reverse('users:show_student_job', args=[user.username, session_slug, job_slug]) )
            get_offered = response.context['get_offered']
            get_accepted = response.context['get_accepted']
            get_declined  = response.context['get_declined']

            self.assertEquals( get_offered.assigned, ApplicationStatus.OFFERED)
            self.assertEquals( get_offered.assigned_hours, 30.0)
            self.assertFalse(get_accepted)
            self.assertFalse(get_declined)

            data = {
                'application': offer.id,
                'assigned_hours': get_offered.assigned_hours
            }
            response = self.client.post( reverse('users:accept_offer', args=[user.username, session_slug, job_slug]), data=urlencode(data), content_type=ContentType )
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, response.url)

            response = self.client.get( reverse('users:show_student_job', args=[user.username, session_slug, job_slug]) )
            application = response.context['application']
            get_accepted = response.context['get_accepted']
            get_declined  = response.context['get_declined']

            self.assertEqual(get_accepted.assigned, ApplicationStatus.ACCEPTED)
            self.assertEqual(get_accepted.assigned_hours, 30.0)
            self.assertEqual(application.job.accumulated_ta_hours, 30.0)
            self.assertFalse(get_declined)



    def test_decline_jobs(self):
        """ Test: decline job offers """

        # Login with a student
        user_id = '15'
        user = userApi.get_user(user_id)
        self.login(user.username, '12')
        response = self.client.get( reverse('home:index') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user']['username'], user.username)
        active_sessions = response.context['active_sessions']

        num_applications = self.apply_jobs(user, active_sessions) # a student has applied
        applications = api.get_applications_applied_by_student(user)
        self.assertEquals( len(applications),  num_applications )

        # Login with an admin
        self.login('admin', '12')
        user_applications = api.get_applications_applied_by_student(user)

        # send job offers
        num_offers = self.offer_jobs(user_applications) # an admin has offered
        offers = api.get_offered_applications_by_student(user)
        self.assertEquals( len(offers),  num_offers )

        # Login with a student again
        self.login(user.username, '12')

        # accept job offers
        for offer in offers:
            session_slug = offer.job.session.slug
            job_slug = offer.job.course.slug
            response = self.client.get( reverse('users:show_student_job', args=[user.username, session_slug, job_slug]) )
            get_offered = response.context['get_offered']
            get_accepted = response.context['get_accepted']
            get_declined  = response.context['get_declined']

            self.assertEquals( get_offered.assigned, ApplicationStatus.OFFERED)
            self.assertEquals( get_offered.assigned_hours, 30.0)
            self.assertFalse(get_accepted)
            self.assertFalse(get_declined)

            data = {
                'application': offer.id,
                'assigned_hours': get_offered.assigned_hours
            }
            response = self.client.post( reverse('users:decline_offer', args=[user.username, session_slug, job_slug]), data=urlencode(data), content_type=ContentType )
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, response.url)

            response = self.client.get( reverse('users:show_student_job', args=[user.username, session_slug, job_slug]) )
            application = response.context['application']
            get_accepted = response.context['get_accepted']
            get_declined  = response.context['get_declined']

            self.assertFalse(get_accepted)
            self.assertEqual(application.job.accumulated_ta_hours, 0.0)

            self.assertEqual(get_declined.assigned, ApplicationStatus.DECLINED)
            self.assertEqual(get_declined.assigned_hours, 0.0)



    def test_show_instructor_details(self):
        """ Test: display instructor's details """
        user_id = '5'
        user = userApi.get_user(user_id)
        self.login(user.username, '12')

        job = None
        for j in user.job_set.all():
            job = j
            break

        response = self.client.get( reverse('users:show_instructor_jobs', args=[user.username, job.session.slug, job.course.slug]) )
        self.assertEqual(response.status_code, 200)

        loggedin_user = response.context['loggedin_user']
        res_user = response.context['user']
        session = response.context['session']
        res_job = response.context['job']
        self.assertEqual(loggedin_user['username'], user.username)
        self.assertEqual(res_user.id, user.id)
        self.assertEqual(session.id, job.session.id)
        self.assertEqual(res_job.id, job.id)


    def test_edit_job_description(self):
        """ Test: edit a job description by an instructor """
        user_id = '5'
        user = userApi.get_user(user_id)
        self.login(user.username, '12')

        job = None
        for j in user.job_set.all():
            job = j
            break

        data = {
            'title': 'updated title',
            'description': 'updated description',
            'qualification': 'updatd qualification',
            'note': 'updated note'
        }

        response = self.client.post( reverse('users:edit_instructor_jobs', args=[user.username, job.session.slug, job.course.slug]), data=urlencode(data), content_type=ContentType )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue('Success' in messages[0]) # Check a success message

        response = self.client.get( reverse('users:show_instructor_jobs', args=[user.username, job.session.slug, job.course.slug]) )
        self.assertEqual(response.status_code, 200)
        res_job = response.context['job']
        self.assertEqual(res_job.title, data['title'])
        self.assertEqual(res_job.description, data['description'])
        self.assertEqual(res_job.qualification, data['qualification'])
        self.assertEqual(res_job.note, data['note'])
