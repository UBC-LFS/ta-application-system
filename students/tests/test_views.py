from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from urllib.parse import urlencode

from administrators.models import *
from users.models import *
from administrators import api as adminApi
from users import api as userApi

from administrators.tests.test_views import DATA, ContentType
from django.core.files.uploadedfile import SimpleUploadedFile

from django.utils.crypto import get_random_string



class JobTest(TestCase):
    fixtures = DATA

    @classmethod
    def setUpTestData(cls):
        print('\nJob testing has started ==>')

    def login(self, username, password):
        self.client.post('/accounts/local_login/', data={'username': username, 'password': password})

    def messages(self, res):
        return [m.message for m in get_messages(res.wsgi_request)]

    def test_view_url_exists_at_desired_location(self):
        print('\n- Test: view url exists at desired location')
        self.login('test.user10', '12')

        session_slug = '2019-w1'

        response = self.client.get( reverse('students:index') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:show_profile') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:edit_profile') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:show_confidentiality') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:submit_confidentiality') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:edit_confidentiality') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:explore_jobs') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:available_jobs', args=[session_slug]) )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:apply_job', args=[session_slug, 'lfs-252-001-land-food-and-community-quantitative-data-analysis-w1']) )
        self.assertEqual(response.status_code, 200)

        """response = self.client.get( reverse('students:applied_jobs') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:offered_jobs') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:accepted_jobs') )
        self.assertEqual(response.status_code, 200)

        response = self.client.get( reverse('students:declined_jobs') )
        self.assertEqual(response.status_code, 200)"""

        response = self.client.get( reverse('students:accept_decline_job', args=[session_slug, 'lfs-150-001-scholarly-writing-and-argumentation-in-land-and-food-systems-w1']) )
        self.assertEqual(response.status_code, 200)

    def test_show_profile(self):
        print('\n- Test: Display all lists of session terms')
        self.login('test.user10', '12')

        response = self.client.get( reverse('students:show_profile') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'test.user10')
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual(response.context['user'].username, 'test.user10')
        self.assertFalse(response.context['form'].is_bound)

    def test_edit_profile(self):
        print('\n- Test: Edit user profile')
        self.login('test.user10', '12')

        data = {
            'preferred_name': 'preferred name',
            'qualifications': 'qualifications',
            'prior_employment': 'prior employment',
            'special_considerations': 'special considerations',
            'status': '3',
            'program': '5',
            'program_others': 'program others',
            'graduation_date': '2020-05-20',
            'degrees': ['2', '5'],
            'trainings': ['2', '3'],
            'training_details': 'training details',
            'lfs_ta_training': '1',
            'lfs_ta_training_details': 'Lfs ta training details',
            'ta_experience': '2',
            'ta_experience_details': 'Ta experience details'
        }

        response = self.client.post( reverse('students:edit_profile'), data=urlencode(data, True), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:show_profile') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'test.user10')
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        user = response.context['user']
        self.assertEqual(user.username, 'test.user10')

        self.assertEqual(user.profile.preferred_name, data['preferred_name'])
        self.assertEqual(user.profile.qualifications, data['qualifications'])
        self.assertEqual(user.profile.prior_employment, data['prior_employment'])
        self.assertEqual(user.profile.special_considerations, data['special_considerations'])
        self.assertEqual(user.profile.status.id, int(data['status']))
        self.assertEqual(user.profile.program.id, int(data['program']))
        self.assertEqual(user.profile.program_others, data['program_others'])
        self.assertEqual(user.profile.graduation_date.year, 2020)
        self.assertEqual(user.profile.graduation_date.month, 5)
        self.assertEqual(user.profile.graduation_date.day, 20)
        self.assertEqual( len(user.profile.degrees.all()), len(data['degrees']) )
        self.assertEqual( len(user.profile.trainings.all()), len(data['trainings']) )
        self.assertEqual(user.profile.training_details, data['training_details'])
        self.assertEqual(user.profile.lfs_ta_training, data['lfs_ta_training'])
        self.assertEqual(user.profile.lfs_ta_training_details, data['lfs_ta_training_details'])
        self.assertEqual(user.profile.ta_experience, data['ta_experience'])
        self.assertEqual(user.profile.ta_experience_details, data['ta_experience_details'])

    def test_upload_user_resume(self):
        print('\n- Test: upload user resume')
        self.login('test.user10', '12')

        username = 'test.user10'
        resume_name = 'resume.pdf'
        data = {
            'user': '10',
            'resume': SimpleUploadedFile(resume_name, b'file_content', content_type='application/pdf')
        }
        response = self.client.post( reverse('students:upload_resume'), data=data, format='multipart')
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('students:show_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, username)
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertIsNotNone(response.context['user'].resume)

    def test_replace_user_resume(self):
        print('\n- Test: replace user resume')
        self.login('test.user10', '12')

        user_id = '10'
        username = 'test.user10'
        resume_name = 'resume.pdf'
        data = {
            'user': user_id,
            'resume': SimpleUploadedFile(resume_name, b'file_content', content_type='application/pdf')
        }
        response = self.client.post( reverse('students:upload_resume'), data=data, format='multipart')
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('students:show_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, username)
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertIsNotNone(response.context['user'].resume)

        updated_resume_name = 'updated_resume.pdf'
        updated_data = {
            'user': user_id,
            'resume': SimpleUploadedFile(updated_resume_name, b'file_content', content_type='application/pdf')
        }
        response = self.client.post( reverse('students:upload_resume'), data=updated_data, format='multipart')
        messages = self.messages(response)
        """print(messages)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('students:show_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, username)
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertIsNotNone(response.context['user'].resume)"""

    def test_delete_user_resume(self):
        print('\n- Test: delete user resume')
        self.login('test.user10', '12')

        username = 'test.user10'
        resume_name = 'resume.pdf'
        data = {
            'user': '10',
            'resume': SimpleUploadedFile(resume_name, b'file_content', content_type='application/pdf')
        }
        response = self.client.post( reverse('students:upload_resume'), data=data, format='multipart' )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('students:show_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, username)
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertIsNotNone(response.context['user'].resume)

        response = self.client.post( reverse('students:delete_resume'), data=urlencode({ 'user': username }), content_type=ContentType )
        messages = self.messages(response)
        """print(messages)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get(reverse('students:show_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, username)
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertIsNone(response.context['user'].resume)"""

    def test_show_confidentiality(self):
        print('\n- Test: Display user confidentiality')
        self.login('test.user10', '12')

        response = self.client.get( reverse('students:show_confidentiality') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'test.user10')
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        self.assertEqual(response.context['user'].username, 'test.user10')

    def test_check_confidentiality(self):
        print('\n- Test: Check whether an international student or not')
        self.login('test.user10', '12')

        user_id = '10'
        data = {
            'user': user_id,
            'is_international': True
        }

        response = self.client.post( reverse('students:check_confidentiality'), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Please submit your information' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        data = {
            'user': user_id,
            'employee_number': '12345678',
            'sin': SimpleUploadedFile('sin.jpg', b'file_content', content_type='image/jpeg'),
            'sin_expiry_date': '2020-01-01',
            'study_permit': SimpleUploadedFile('study_permit.png', b'file_content', content_type='image/png'),
            'study_permit': '2020-05-05'
        }

        """response = self.client.post( reverse('students:submit_confidentiality'), data=data, format='multipart' )
        messages = self.messages(response)
        print(messages)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)"""






    def test_explore_jobs(self):
        print('\n- Test: Display all lists of session terms')
        self.login('test.user10', '12')

        response = self.client.get( reverse('students:explore_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'test.user10')
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        self.assertEqual( len(response.context['visible_current_sessions']), 3 )
        self.assertEqual( len(response.context['applied_jobs']), 9 )

    def test_available_jobs(self):
        print('\n- Test: Display jobs available to apply')
        self.login('test.user10', '12')

        session_slug = '2019-w1'

        response = self.client.get( reverse('students:available_jobs', args=[session_slug]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'test.user10')
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual(response.context['session'].slug, session_slug)
        self.assertEqual( len(response.context['jobs']), 4 )

    def test_apply_jobs(self):
        print('\n- Test: Students can apply for each job')
        self.login('test.user10', '12')

        session_slug = '2019-w1'
        job_slug = 'lfs-252-001-land-food-and-community-quantitative-data-analysis-w1'
        response = self.client.get( reverse('students:apply_job', args=[session_slug, job_slug]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'test.user10')
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual(response.context['job'].course.slug, job_slug)
        self.assertFalse(response.context['has_applied_job'])
        self.assertFalse(response.context['form'].is_bound)

        data = {
            'applicant': response.context['loggedin_user'].id,
            'job': response.context['job'].id,
            'supervisor_approval': True,
            'how_qualified': '4',
            'how_interested': '3',
            'availability': True,
            'availability_note': 'nothing'
        }

        response = self.client.post( reverse('students:apply_job', args=[session_slug, job_slug]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:apply_job', args=[session_slug, job_slug]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'test.user10')
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual(response.context['job'].course.slug, job_slug)
        self.assertTrue(response.context['has_applied_job'])
        self.assertFalse(response.context['form'].is_bound)



    def test_accept_decline_job(self):
        print('\n- Test: Display a job to select accept or decline a job offer')
        self.login('test.user20', '20')

        session_slug = '2019-w1'
        job_slug = 'lfs-100-001-introduction-to-land-food-and-community-w1'

        response = self.client.get( reverse('students:accept_decline_job', args=[session_slug, job_slug]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'test.user20')
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual(response.context['app'].job.session.slug, session_slug)
        self.assertEqual(response.context['app'].job.course.slug, job_slug)
        self.assertEqual(response.context['app'].applicant.username, 'test.user20')
        self.assertEqual(response.context['app'].offered.get_assigned_display(), 'Offered')
        self.assertEqual(response.context['app'].offered.assigned_hours, 10.0)
        self.assertFalse(response.context['app'].accepted)
        self.assertFalse( response.context['app'].declined )

    def test_accept_offer(self):
        print('\n- Test: Students accept a job offer')
        self.login('test.user20', '20')

        session_slug = '2019-w1'
        job_slug = 'lfs-100-001-introduction-to-land-food-and-community-w1'

        response = self.client.get( reverse('students:accept_decline_job', args=[session_slug, job_slug]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'test.user20')
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual(response.context['app'].job.course.slug, job_slug)
        self.assertEqual(response.context['app'].applicant.username, 'test.user20')

        data = {
            'application': response.context['app'].id,
            'assigned_hours': response.context['app'].offered.assigned_hours
        }

        response = self.client.post( reverse('students:accept_offer', args=[session_slug, job_slug]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:status_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'test.user20')
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        apps = response.context['apps']
        total_assigned_hours = response.context['total_accepted_assigned_hours']
        self.assertEqual( len(apps), 2 )
        self.assertEqual(apps[0].job.session.slug, session_slug)
        self.assertEqual(apps[0].job.course.slug, job_slug)
        self.assertEqual(apps[0].accepted.get_assigned_display(), 'Accepted')
        self.assertEqual(apps[0].accepted.assigned_hours, data['assigned_hours'])
        self.assertEqual(total_assigned_hours[session_slug.upper()], data['assigned_hours'])

    def test_decline_offer(self):
        print('\n- Test: Students decline job offers')
        self.login('test.user20', '20')

        session_slug = '2019-w1'
        job_slug = 'lfs-100-001-introduction-to-land-food-and-community-w1'

        response = self.client.get( reverse('students:accept_decline_job', args=[session_slug, job_slug]) )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'test.user20')
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual(response.context['app'].job.session.slug, session_slug)
        self.assertEqual(response.context['app'].job.course.slug, job_slug)
        self.assertEqual(response.context['app'].applicant.username, 'test.user20')

        data = {
            'application': response.context['app'].id,
            'assigned_hours': response.context['app'].offered.assigned_hours
        }

        response = self.client.post( reverse('students:decline_offer', args=[session_slug, job_slug]), data=urlencode(data), content_type=ContentType )
        messages = self.messages(response)
        self.assertTrue('Success' in messages[0])
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        response = self.client.get( reverse('students:status_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'test.user20')
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])

        apps = response.context['apps']
        self.assertEqual( len(apps), 2 )
        self.assertEqual(apps[0].job.session.slug, session_slug)
        self.assertEqual(apps[0].job.course.slug, job_slug)
        self.assertEqual(apps[0].declined.get_assigned_display(), 'Declined')
        self.assertEqual(apps[0].declined.assigned_hours, 0.0)


    """def test_applied_jobs(self):
        print('\n- Test: Display jobs applied by a student')
        self.login('test.user10', '12')

        response = self.client.get( reverse('students:applied_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'test.user10')
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual( len(response.context['apps']), 9 )

    def test_offered_jobs(self):
        print('\n- Test: Display jobs offered from admins')
        self.login('test.user10', '12')

        response = self.client.get( reverse('students:offered_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'test.user10')
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual( len(response.context['apps']), 5 )
        self.assertEqual( len(response.context['total_assigned_hours']), 2 )

    def test_accepted_jobs(self):
        print('\n- Test: Display jobs accepted by a student')
        self.login('test.user10', '12')

        response = self.client.get( reverse('students:accepted_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'test.user10')
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual( len(response.context['apps']), 3 )
        self.assertEqual( len(response.context['total_assigned_hours']), 2 )

    def test_declined_jobs(self):
        print('\n- Test: Display jobs declined by a student')
        self.login('test.user10', '12')

        response = self.client.get( reverse('students:declined_jobs') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'test.user10')
        self.assertEqual(response.context['loggedin_user'].roles, ['Student'])
        self.assertEqual( len(response.context['apps']), 2 )"""
