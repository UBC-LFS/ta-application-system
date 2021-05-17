from django.conf import settings
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from administrators import api as adminApi
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime


def send(apps, option):
    items = ''
    for app_status in apps:
        li = '<li>'+ adminApi.get_session_term_full_name(app_status.application) + ': ' + app_status.application.applicant.get_full_name()
        if option == 'accepted':
            li += ' (App ID: ' + str(app_status.application.id) + ', assigned ' + str(app_status.assigned_hours) + ' hours)</li>'
        elif option == 'terminated':
            li += ' (App ID: ' + str(app_status.application.id) + ')</li>'

        items += li

    title = 'LFS TA App Notification: {0} application(s)'.format(option)

    message = '''\
    <html>
      <head></head>
      <body>
        <p>Hi LFS HR,</p>
        <p>We have {1} {4} application(s) on {0}. Please check applications below.</p>
        <ul>{2}</ul>
        <p>Go to <a href={3}>TA Application System</a></p>
        <p>Best regards,</p>
        <p>LFS TA Application System</p>
      </body>
    </html>
    '''.format(datetime.today().strftime("%m/%d/%Y"), len(apps), items, settings.TA_APP_URL, option)

    valid_email = False
    try:
        validate_email(settings.EMAIL_RECEIVER)
        valid_email = True
    except ValidationError as e:
        print(e)

    if valid_email:
        send_mail(title, message, settings.EMAIL_FROM, [ settings.EMAIL_RECEIVER ], fail_silently=False, html_message=message)
        print('The notification has been sent successfully')

def send_accepted_apps():
    apps = adminApi.get_today_accepted_apps()

    if apps != None:
        send(apps, 'accepted')

def send_terminated_apps():
    apps = adminApi.get_today_terminated_apps()

    if apps != None:
        send(apps, 'terminated')


def run():
    print('Scheduling tasks running...')
    scheduler = BackgroundScheduler()

    scheduler.add_job(send_accepted_apps, 'cron', day_of_week='mon-fri', hour='9-17')
    scheduler.add_job(send_terminated_apps, 'cron', day_of_week='mon-fri', hour='9-17', minute=5)

    scheduler.start()
