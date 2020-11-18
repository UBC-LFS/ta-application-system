import os
from datetime import datetime, timedelta

# Global variables
DATABASE = os.environ['TA_APP_DB_NAME']
USER = os.environ['TA_APP_DB_USER']
PASSWORD = os.environ['TA_APP_DB_PASSWORD']
HOST = os.environ['TA_APP_DB_HOST']
PORT = os.environ['TA_APP_DB_PORT']

SMTP_SERVER = os.environ['TA_APP_EMAIL_HOST']
SENDER = os.environ['TA_APP_EMAIL_FROM']
RECEIVER = os.environ['TA_APP_EMAIL_RECEIVER']

TA_APP_URL = os.environ['TA_APP_URL']
YESTERDAY = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
TODAY = datetime.today().strftime('%Y-%m-%d')
ACCEPTED_ID = '3'

"""
How to use cron jobs
# List jobs
$ crontab -l

# Open a crontab
$ crontab -e

# Add jobs
00 09 * * * /usr/bin/python3 /home/username/ta-application-system/email_notification/send_email.py
"""
