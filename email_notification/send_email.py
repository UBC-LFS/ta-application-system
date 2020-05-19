from ta_app_db import TaAppDatabase
from send_email_settings import *

import smtplib, ssl
from email.mime.text import MIMEText


def send(statuses):
    """Send an email with a receiver and a message """
    lis = ''
    for status in statuses:
        lis += '<li>Application ID: ' + str(status[0]) + ' (assigned ' + str(status[1]) + ' hours)</li>'

    message = '''\
    <html>
      <head></head>
      <body>
        <p>Hi LFS HR,</p>
        <p>We have {1} accepted application(s) on {0}. Please check applications below.</p>
        <ul>{2}</ul>
        <p>Go to <a href={3}>TA Application System</a></p><br />
        <p>Best regards,</p>
        <p>LFS TA Application System</p>
      </body>
    </html>
    '''.format(YESTERDAY, len(statuses), lis, URL)

    msg = MIMEText(message, 'html')
    msg['Subject'] = 'Notification: TA Application System'
    msg['From'] = SENDER
    msg['To'] = RECEIVER

    try:
    	server = smtplib.SMTP(SMTP_SERVER)
    	server.sendmail(SENDER, RECEIVER, msg.as_string())
    except Exception as e:
    	print(e)
    finally:
    	server.quit()


if __name__ == "__main__":
    db = TaAppDatabase(USER, PASSWORD, HOST, PORT, DATABASE)
    statuses = db.statuses
    if len(statuses)> 0:
        print('Sent it to HR users. Target day was {0}'.format(YESTERDAY))
        send(statuses)
