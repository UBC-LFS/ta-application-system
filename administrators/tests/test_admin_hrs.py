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

from administrators.tests.test_sessions import LOGIN_URL, ContentType, DATA, PASSWORD, USERS

from datetime import datetime

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

    def json_messages(self, res):
        return json.loads( res.content.decode('utf-8') )

    def build_csv_file(self, apps, options, id_included=False):
        ''' Build a csv file '''
        csv_file = 'ID,Year,Term,Job,Applicant,Student Number,Employee Number,Classification,Monthly Salary (CAD),P/T (%),PIN,TASM,eForm,Worktag,Processing Note,Accepted at\n'
        objs = []
        c = 1
        for app in apps:
            if hasattr(app, 'admindocuments'):
                csv_file += '"' + str(app.id) + '","2019","W2","APBI 260 001","Michael Jordan (user100.test)","45345555","1111112","2019 STA ($35.42)","$442.75","26.04",'
                pin = app.admindocuments.pin
                tasm = app.admindocuments.tasm
                eform = app.admindocuments.eform
                worktag = app.admindocuments.worktag
                processing_note = app.admindocuments.processing_note

                if 'pin' in options: pin = '998'+ str(c)
                if 'tasm' in options:
                    tasm = False if tasm else True
                if 'eform' in options: eform = 'LLGG6' + str(c)
                if 'worktag' in options: worktag = 'xyzlmno' + str(c)
                if 'processing_note' in options: processing_note = 'Very good. Updated ' + str(c)

                objs.append({ 'id': app.id, 'pin': pin, 'tasm': tasm, 'eform': eform, 'worktag': worktag, 'processing_note': processing_note })

                csv_file += '"' + str(pin) + '",' if pin != None else '"",'
                csv_file += '"' + "YES" + '",' if tasm else '"",'
                csv_file += '"' + str(eform) + '",' if eform != None else '"",'
                csv_file += '"' + str(worktag) + '",' if worktag != None else '"",'
                csv_file += '"' + str(processing_note) + '",' if processing_note != None else '"",'
                csv_file += '"Sept. 20, 2019 (50.0 hours)"\n'
            else:
                if id_included:
                    pin = '9977'
                    tasm = 'YES'
                    eform = 'vASE12'
                    worktag = 'ABCDEFG9'
                    processing_note = 'Yay good'
                    csv_file += '"' + str(app.id) + '","2019","W2","APBI 260 001","Michael Jordan (user100.test)","45345555","1111112","2019 STA ($35.42)","$442.75","26.04","{0}",{1},"{2}","{3}","{4}","Sept. 20, 2019 (50.0 hours)"\n'.format(pin, tasm, eform, worktag, processing_note)
                    objs.append({ 'id': app.id, 'pin': pin, 'tasm': tasm, 'eform': eform, 'worktag': worktag, 'processing_note': processing_note })
            c += 1

        return csv_file, objs

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
        print('- Test: index')
        self.login('user3.admin', 'password')

        response = self.client.get( reverse('administrators:index') )
        self.assertEqual(response.status_code, 200)
        self.assertFalse('archived_sessions' in response.context.keys())
        self.assertTrue('accepted_apps' in response.context.keys())
        self.assertEqual(response.context['accepted_apps'].count(), 6)

    def test_accepted_applications(self):
        print('- Test: Display applications accepted by students')
        self.login('user3.admin', 'password')

        response = self.client.get( reverse('administrators:accepted_applications') )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['loggedin_user'].username, 'user3.admin')
        self.assertEqual(response.context['loggedin_user'].roles, ['HR'])
        self.assertEqual( len(response.context['apps']), 5 )

    def test_admin_docs_failure1(self):
        print('- Test: Admin or HR can update admin docs - app id missing')
        self.login('user3.admin', 'password')

        data1 = {
            'pin': '1237',
            'tasm': 'true',
            'eform': 'af3343',
            'worktag': 'ABCDEFG9',
            'processing_note': 'this is a processing note'
        }
        response = self.client.post(reverse('administrators:update_admin_docs'), data=urlencode(data1), content_type=ContentType)
        messages = self.json_messages(response)
        self.assertEqual(messages['status'], 'error')
        self.assertEqual(messages['message'], 'An error occurred. Form is invalid. APPLICATION: This field is required.')
        self.assertEqual(response.status_code, 400)


    def test_admin_docs_failure2(self):
        print('- Test: Admin or HR can update admin docs - pin is an error')
        self.login('user3.admin', 'password')
        app_id = 1

        data2 = {
            'application': app_id,
            'pin': '12377',
            'tasm': 'true',
            'eform': 'af3343',
            'worktag': 'ABCDEFG9',
            'processing_note': 'this is a processing note'
        }
        response = self.client.post(reverse('administrators:update_admin_docs'), data=urlencode(data2), content_type=ContentType)
        messages = self.json_messages(response)
        self.assertEqual(messages['status'], 'error')
        self.assertEqual(messages['message'], 'An error occurred. Form is invalid. PIN: Ensure this value has at most 4 characters (it has 5).')
        self.assertEqual(response.status_code, 400)


    def test_admin_docs_success(self):
        print('- Test: Admin or HR can update admin docs - success')
        self.login('user3.admin', 'password')
        app_id = 1

        data3 = {
            'application': app_id,
            'pin': '1237',
            'tasm': 'true',
            'eform': 'af3343',
            'worktag': 'ABCDEFG9',
            'processing_note': 'this is a processing note',
        }
        response = self.client.post(reverse('administrators:update_admin_docs'), data=urlencode(data3), content_type=ContentType)
        messages = self.json_messages(response)
        self.assertTrue(messages['status'], 'success')
        self.assertTrue(messages['message'], 'Success! Admin Documents of User100 Test updated (Application ID: 1).')
        self.assertEqual(response.status_code, 200)

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
        self.assertTrue(app.admindocuments.worktag, data3['worktag'])
        self.assertEqual( len(app.admindocuments.admindocumentsuser_set.all()), 1 )

        admin_user = app.admindocuments.admindocumentsuser_set.first()
        self.assertEqual(admin_user.user, 'User3 Admin')
        self.assertEqual(admin_user.document.application.id, app_id)
        self.assertEqual(admin_user.created_at.strftime('%Y-%m-%d'), datetime.now().strftime('%Y-%m-%d'))

    def test_admin_docs_update_history(self):
        print('- Test: Admin or HR can have update admin docs with history')
        self.login('user3.admin', 'password')
        app_id = 1
        data1 = {
            'application': app_id,
            'pin': '1237',
            'tasm': 'true',
            'eform': '',
            'worktag': 'ABCDEFG9',
            'processing_note': ''
        }
        response = self.client.post(reverse('administrators:update_admin_docs'), data=urlencode(data1), content_type=ContentType)
        messages = self.json_messages(response)
        self.assertEqual(messages['status'], 'success')
        self.assertEqual(messages['message'], 'Success! Admin Documents of User100 Test updated (Application ID: 1).')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('administrators:accepted_applications') + '?page=2')
        self.assertEqual(response.status_code, 200)
        accepted_applications = response.context['apps']

        app1 = None
        for appl in accepted_applications:
            if appl.id == app_id:
                app1 = appl

        self.assertEqual(app1.id, app_id)
        self.assertEqual(app1.admindocuments.pin, data1['pin'])
        self.assertTrue(app1.admindocuments.tasm)
        self.assertIsNone(app1.admindocuments.eform)
        self.assertEqual(app1.admindocuments.worktag, data1['worktag'])
        self.assertEqual( len(app1.admindocuments.admindocumentsuser_set.all()), 1 )


        data2 = {
            'application': app_id,
            'pin': '1237',
            'tasm': 'true',
            'eform': 'af3343',
            'worktag': 'ABCDEFG9',
            'processing_note': 'this is a processing note',
        }
        response = self.client.post(reverse('administrators:update_admin_docs'), data=urlencode(data2), content_type=ContentType)
        messages = self.json_messages(response)
        self.assertEqual(messages['status'], 'success')
        self.assertEqual(messages['message'], 'Success! Admin Documents of User100 Test updated (Application ID: 1).')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('administrators:accepted_applications') + '?page=2')
        self.assertEqual(response.status_code, 200)
        accepted_applications = response.context['apps']

        app2 = None
        for appl in accepted_applications:
            if appl.id == app_id:
                app2 = appl

        self.assertEqual(app2.id, app_id)
        self.assertEqual(app2.admindocuments.pin, data2['pin'])
        self.assertTrue(app2.admindocuments.tasm)
        self.assertEqual(app2.admindocuments.eform, data2['eform'])
        self.assertEqual(app2.admindocuments.worktag, data2['worktag'])
        self.assertEqual( len(app2.admindocuments.admindocumentsuser_set.all()), 2 )


        self.login('user2.admin', 'password')

        data3 = {
            'application': app_id,
            'pin': '1255',
            'tasm': 'false',
            'eform': 'af3343',
            'worktag': 'ABCDEFG8',
            'processing_note': 'this is a processing note'
        }
        response = self.client.post(reverse('administrators:update_admin_docs'), data=urlencode(data3), content_type=ContentType)
        messages = self.json_messages(response)
        self.assertEqual(messages['status'], 'success')
        self.assertEqual(messages['message'], 'Success! Admin Documents of User100 Test updated (Application ID: 1).')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('administrators:accepted_applications') + '?page=2')
        self.assertEqual(response.status_code, 200)
        accepted_applications = response.context['apps']

        app3 = None
        for appl in accepted_applications:
            if appl.id == app_id:
                app3 = appl

        self.assertEqual(app3.id, app_id)
        self.assertEqual(app3.admindocuments.pin, data3['pin'])
        self.assertFalse(app3.admindocuments.tasm, data3['tasm'])
        self.assertEqual(app3.admindocuments.eform, data3['eform'])
        self.assertEqual(app3.admindocuments.worktag, data3['worktag'])
        self.assertEqual( len(app3.admindocuments.admindocumentsuser_set.all()), 3 )

        admin_users = []
        for admin_user in app3.admindocuments.admindocumentsuser_set.all():
            admin_users.append(admin_user.user)
            self.assertEqual(admin_user.created_at.strftime('%Y-%m-%d'), datetime.now().strftime('%Y-%m-%d'))

        self.assertEqual(admin_users, ['User2 Admin', 'User3 Admin', 'User3 Admin'])


    def test_admin_docs_update_via_csv_empty(self):
        print('- Test: Admin or HR can have update admin docs via CSV - empty data')
        self.login()

        data = {
            'file': SimpleUploadedFile('ta_app.csv', ''.encode(), content_type='text/csv'),
            'next': reverse('administrators:accepted_applications')
        }
        response = self.client.post(reverse('administrators:import_accepted_apps'), data=data, format='multipart')
        messages = self.messages(response)
        self.assertEqual(messages[0], 'An error occurred while iterating table rows. Please check your data. Note that 1st row is a header.')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

    def test_admin_docs_update_via_csv_no_header(self):
        print('- Test: Admin or HR can have update admin docs via CSV - no header')
        self.login()

        csv = '"24","2019","W2","APBI 260 001","Michael Jordan (user100.test)","45345555","1111112","2019 STA ($35.42)","$442.75","26.04","2222","","444444","5555","6666","Sept. 20, 2019 (50.0 hours)"'
        data = {
            'file': SimpleUploadedFile('ta_app.csv', csv.encode(), content_type='text/csv'),
            'next': reverse('administrators:accepted_applications')
        }
        response = self.client.post(reverse('administrators:import_accepted_apps'), data=data, format='multipart')
        messages = self.messages(response)
        self.assertEqual(messages[0], 'An error occurred while iterating table rows. Please check your header or data fields. Note that 1st row is a header.')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)


    def test_admin_docs_update_via_csv_no_data(self):
        print('- Test: Admin or HR can have update admin docs via CSV - no data fields')
        self.login()

        csv = 'ID,Year,Term,Job,Applicant,Student Number,Employee Number,Classification,Monthly Salary (CAD),P/T (%),PIN,TASM,eForm,Worktag,Processing Note,Accepted at\n'
        data = {
            'file': SimpleUploadedFile('ta_app.csv', csv.encode(), content_type='text/csv'),
            'next': reverse('administrators:accepted_applications')
        }
        response = self.client.post(reverse('administrators:import_accepted_apps'), data=data, format='multipart')
        messages = self.messages(response)
        self.assertEqual(messages[0], 'An error occurred while iterating table rows. Please check your header or data fields. Note that 1st row is a header.')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)


    def test_admin_docs_update_via_csv_columns_missing(self):
        print('- Test: Admin or HR can have update admin docs via CSV - some columns are missing')
        self.login()

        csv3 = 'ID,Year,Term,Job,Applicant,Student Number,Employee Number,Classification,Monthly Salary (CAD),P/T (%),PIN,TASM,eForm,Worktag,Processing Note,Accepted at\n"24","2019","W2","APBI 260 001","Michael Jordan (user100.test)","45345555","1111112","2019 STA ($35.42)","$442.75","26.04","2222","","444444","5555","6666"\n'
        data3 = {
            'file': SimpleUploadedFile('ta_app.csv', csv3.encode(), content_type='text/csv'),
            'next': reverse('administrators:accepted_applications')
        }
        response = self.client.post(reverse('administrators:import_accepted_apps'), data=data3, format='multipart')
        messages = self.messages(response)
        self.assertEqual(messages[0], 'An error occurred while reading table rows. Some columns are missing.')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)


    def test_admin_docs_update_via_csv_wrong_file_type(self):
        print('- Test: Admin or HR can have update admin docs via CSV - wrong file type')
        self.login()

        response = self.client.get(reverse('administrators:accepted_applications'))
        self.assertEqual(response.status_code, 200)
        apps = response.context['apps']

        csv, objs = self.build_csv_file(apps, [])
        data = {
            'file': SimpleUploadedFile('ta_app.xls', csv.encode(), content_type='application/vnd.ms-excel'),
            'next': reverse('administrators:accepted_applications')
        }
        response = self.client.post(reverse('administrators:import_accepted_apps'), data=data, format='multipart')
        messages = self.messages(response)
        self.assertEqual(messages[0], 'An error occurred. Only CSV files are allowed to update. Please check your file.')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

    def test_admin_docs_update_via_csv_same(self):
        print('- Test: Admin or HR can have update admin docs via CSV - same file')
        self.login()

        response = self.client.get(reverse('administrators:accepted_applications'))
        self.assertEqual(response.status_code, 200)
        apps = response.context['apps']

        csv, objs = self.build_csv_file(apps, [])
        data = {
            'file': SimpleUploadedFile('ta_app.csv', csv.encode(), content_type='text/csv'),
            'next': reverse('administrators:accepted_applications')
        }
        response = self.client.post(reverse('administrators:import_accepted_apps'), data=data, format='multipart')
        messages = self.messages(response)
        self.assertEqual(messages[0], 'Warning! No data was updated in the database. Please check your data inputs.')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

    def test_admin_docs_update_via_csv_update(self):
        print('- Test: Admin or HR can have update admin docs via CSV - update file')
        self.login()

        response = self.client.get(reverse('administrators:accepted_applications'))
        self.assertEqual(response.status_code, 200)
        apps = response.context['apps']

        csv, objs = self.build_csv_file(apps, ['pin', 'tasm', 'eform', 'worktag', 'processing_note'])
        data = {
            'file': SimpleUploadedFile('ta_app.csv', csv.encode(), content_type='text/csv'),
            'next': reverse('administrators:accepted_applications')
        }
        response = self.client.post(reverse('administrators:import_accepted_apps'), data=data, format='multipart')
        messages = self.messages(response)
        self.assertEqual(messages[0], 'Success! Updated the following fields in Admin Docs through CSV. <ul><li><strong>ID: 24 (CWL: user100.test)</strong> - PIN,TASM,eForm,Worktag,Processing Note</li><li><strong>ID: 11 (CWL: user70.test)</strong> - PIN,TASM,eForm,Worktag,Processing Note</li><li><strong>ID: 8 (CWL: user66.test)</strong> - PIN,TASM,eForm,Worktag,Processing Note</li><li><strong>ID: 7 (CWL: user66.test)</strong> - PIN,TASM,eForm,Worktag,Processing Note</li></ul>')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

    def test_admin_docs_update_via_csv_create_id(self):
        print('- Test: Admin or HR can have update admin docs via CSV - create id')
        self.login()

        response = self.client.get(reverse('administrators:accepted_applications'))
        self.assertEqual(response.status_code, 200)
        apps = response.context['apps']

        csv, objs = self.build_csv_file(apps, ['pin', 'tasm', 'eform', 'worktag', 'processing_note'], True)
        data = {
            'file': SimpleUploadedFile('ta_app.csv', csv.encode(), content_type='text/csv'),
            'next': reverse('administrators:accepted_applications')
        }
        response = self.client.post(reverse('administrators:import_accepted_apps'), data=data, format='multipart')
        messages = self.messages(response)
        self.assertEqual(messages[0], 'Success! Updated the following fields in Admin Docs through CSV. <ul><li><strong>ID: 24 (CWL: user100.test)</strong> - PIN,TASM,eForm,Worktag,Processing Note</li><li><strong>ID: 11 (CWL: user70.test)</strong> - PIN,TASM,eForm,Worktag,Processing Note</li><li><strong>ID: 8 (CWL: user66.test)</strong> - PIN,TASM,eForm,Worktag,Processing Note</li><li><strong>ID: 7 (CWL: user66.test)</strong> - PIN,TASM,eForm,Worktag,Processing Note</li><li><strong>ID: 1 (CWL: user100.test)</strong> - PIN,TASM,eForm,Worktag,Processing Note</li></ul>')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

        app = adminApi.get_application('1')
        found = {}
        for obj in objs:
            if obj['id'] == app.id:
                found = obj

        found['tasm'] = True if found['tasm'].lower() == 'yes' else False

        self.assertTrue(hasattr(app, 'admindocuments'))
        self.assertEqual(app.admindocuments.pin, found['pin'])
        self.assertEqual(app.admindocuments.tasm, found['tasm'])
        self.assertEqual(app.admindocuments.eform, found['eform'])
        self.assertEqual(app.admindocuments.worktag, found['worktag'])
        self.assertEqual(app.admindocuments.processing_note, found['processing_note'])

    def test_admin_docs_update_via_csv_no_id_found(self):
        print('- Test: Admin or HR can have update admin docs via CSV - no id found')
        self.login()

        response = self.client.get(reverse('administrators:accepted_applications'))
        self.assertEqual(response.status_code, 200)
        apps = response.context['apps']

        csv, objs = self.build_csv_file(apps, ['pin', 'tasm', 'eform', 'worktag', 'processing_note'], True)
        csv += '"111111","2019","W2","APBI 260 001","Michael Jordan (user100.test)","45345555","1111112","2019 STA ($35.42)","$442.75","26.04","1277","YES","JJSVV1","jj1b","Extra","Sept. 20, 2019 (50.0 hours)"\n'
        data = {
            'file': SimpleUploadedFile('ta_app.csv', csv.encode(), content_type='text/csv'),
            'next': reverse('administrators:accepted_applications')
        }
        response = self.client.post(reverse('administrators:import_accepted_apps'), data=data, format='multipart')
        messages = self.messages(response)
        self.assertEqual(messages[0], 'An error occurred while reading table rows. No application ID: 111111 found in Accepted Applications.')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

    def test_admin_docs_update_via_csv_not_in_accepted_apps(self):
        print('- Test: Admin or HR can have update admin docs via CSV - not in accepted apps')
        self.login()

        response = self.client.get(reverse('administrators:accepted_applications'))
        self.assertEqual(response.status_code, 200)
        apps = response.context['apps']

        csv, objs = self.build_csv_file(apps, ['pin', 'tasm', 'eform', 'worktag', 'processing_note'], True)
        csv += '"25","2019","W2","APBI 260 001","Michael Jordan (user100.test)","45345555","1111112","2019 STA ($35.42)","$442.75","26.04","1277","YES","JJSVV1","jj2b","Extra","Sept. 20, 2019 (50.0 hours)"\n'
        data = {
            'file': SimpleUploadedFile('ta_app.csv', csv.encode(), content_type='text/csv'),
            'next': reverse('administrators:accepted_applications')
        }
        response = self.client.post(reverse('administrators:import_accepted_apps'), data=data, format='multipart')
        messages = self.messages(response)
        self.assertEqual(messages[0], 'An error occurred while reading table rows. No application ID: 25 found in Accepted Applications.')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

    def test_admin_docs_update_via_csv_empty_row(self):
        print('- Test: Admin or HR can have update admin docs via CSV - empty row')
        self.login()

        response = self.client.get(reverse('administrators:accepted_applications'))
        self.assertEqual(response.status_code, 200)
        apps = response.context['apps']

        csv, objs = self.build_csv_file(apps, ['pin', 'tasm', 'eform', 'worktag', 'processing_note'])
        csv += ',,,,,,,,,,,,,,,\n'
        data = {
            'file': SimpleUploadedFile('ta_app.csv', csv.encode(), content_type='text/csv'),
            'next': reverse('administrators:accepted_applications')
        }
        response = self.client.post(reverse('administrators:import_accepted_apps'), data=data, format='multipart')
        messages = self.messages(response)
        self.assertEqual(messages[0], 'Success! Updated the following fields in Admin Docs through CSV. <ul><li><strong>ID: 24 (CWL: user100.test)</strong> - PIN,TASM,eForm,Worktag,Processing Note</li><li><strong>ID: 11 (CWL: user70.test)</strong> - PIN,TASM,eForm,Worktag,Processing Note</li><li><strong>ID: 8 (CWL: user66.test)</strong> - PIN,TASM,eForm,Worktag,Processing Note</li><li><strong>ID: 7 (CWL: user66.test)</strong> - PIN,TASM,eForm,Worktag,Processing Note</li></ul>')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)

    def test_admin_docs_update_via_csv_empty_id(self):
        print('- Test: Admin or HR can have update admin docs via CSV - empty id')
        self.login()

        response = self.client.get(reverse('administrators:accepted_applications'))
        self.assertEqual(response.status_code, 200)
        apps = response.context['apps']

        csv, objs = self.build_csv_file(apps, ['pin', 'tasm', 'eform', 'worktag', 'processing_note'])
        csv_modified = csv.replace('"8"', '""')
        data = {
            'file': SimpleUploadedFile('ta_app.csv', csv_modified.encode(), content_type='text/csv'),
            'next': reverse('administrators:accepted_applications')
        }
        response = self.client.post(reverse('administrators:import_accepted_apps'), data=data, format='multipart')
        messages = self.messages(response)
        self.assertEqual(messages[0], 'An error occurred while reading table rows. Something went wrong in the 3rd row. (e.g., ID is empty)')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, response.url)
