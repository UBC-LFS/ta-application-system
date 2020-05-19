import unittest
import subprocess

from ta_app_db import TaAppDatabase
from send_email_settings import *


class NotificationTest(unittest.TestCase):
    def test_accepted_applications(self):
        print('\nTest accepted applications')
        db = TaAppDatabase(USER, PASSWORD, HOST, PORT, DATABASE)
        self.assertEqual(len( db.statuses), 2)

if __name__ == "__main__":
    """
    How to run tests:
    1) On Command Prompt go to ta-application-system directory
    2) Edit created_at to yesterday in fixtures/test_applicationstatus.json
    3) run python email_notification/test.py
    """
    
    print('Target day is', YESTERDAY)
    print('Load application status')
    subprocess.run('python manage.py loaddata email_notification/fixtures/test_applicationstatus.json')
    unittest.main()
