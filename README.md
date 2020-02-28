# TA Application System

This project is a web-based TA hiring process system.

### Features
- Encrypt/Decrypt images
- Enable Masquerade mode
- Email sending services
- Used 6 different badges to display the status of job applications: **Applied**, **Selected**, **Accepted**, **Offered**, **Declined** and **Terminated**

### Install prerequisites for Alpine
```
RUN apk update && apk add build-base libressl-dev postgresql-dev libffi-dev gcc python3-dev musl-dev libxml2-dev libxslt-dev xmlsec-dev jpeg-dev
```

### Install prerequisites for Ubuntu
```
$ sudo apt-get install python3-pip python3-setuptools python3-dev libxml2-dev libxmlsec1-dev libxmlsec1-openssl
```

## Summary of Deployment
0. Rename *ta_app/settings.py.example* to *ta_app/settings.py*

1. Clone this Github repository
```
$ git clone https://github.com/UBC-LFS/ta-application-system.git
```

2. Install requirement dependencies
```
$ pip install -r requirements.txt
```

3. Set Environment Variables in your machine:
```
SECRET_KEY = os.environ['TA_APP_SECRET_KEY']
DATABASE_ENGINE = os.environ['TA_APP_DB_ENGINE']
DATABASE = os.environ['TA_APP_DB_NAME']
USER = os.environ['TA_APP_DB_USER']
PASSWORD = os.environ['TA_APP_DB_PASSWORD']
HOST = os.environ['TA_APP_DB_HOST']
PORT = os.environ['TA_APP_DB_PORT']
EMAIL_HOST = os.environ['TA_APP_EMAIL_HOST']
EMAIL_FROM = os.environ['TA_APP_EMAIL_FROM']
TA_APP_URL = os.environ['TA_APP_URL']
ENCRYPT_SALT = os.environ['TA_APP_ENCRYPT_SALT']
ENCRYPT_PASSWORD = os.environ['TA_APP_ENCRYPT_PASSWORD']
```

*Note: how to create ENCRYPT_SALT and ENCRYPT_PASSWORD*
```
# Open up a Python Shell by typing *python*
$ python

# In the Python Shell
>>> from cryptography.fernet import Fernet
>>> key = Fernet.generate_key()
>>> key
long binary string shows up (i.e., b'23fva4-09234ndsfas=sdf0-8973u2rel=')

# You can save only the string part for ENCRYPT_SALT and ENCRYPT_PASSWORD into your system environment variables
So, os.environ['TA_APP_ENCRYPT_SALT'] would be **23fva4-09234ndsfas=sdf0-8973u2rel=**
```

> Reference: [cryptography](https://github.com/pyca/cryptography)


4. Switch *DEBUG* to **False** in a *settings.py* file
```
DEBUG = False
```

5. Add a Media root directory to store certificate files
```
MEDIA_ROOT = 'your_media_root'
```

6. Add your allowed_hosts in *settings.py*
```
ALLOWED_HOSTS = ['YOUR_HOST']
```

7. Create staticfiles in your directory
```
$ python manage.py collectstatic --noinput

# References
# https://docs.djangoproject.com/en/2.2/howto/static-files/
# https://devcenter.heroku.com/articles/django-assets
# https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django/Deployment
```

8. Create a database in Postgresql

9. Create database tables, and migrate
```
$ python manage.py migrate
```

10. Load data
```
$ python manage.py loaddata ta_app/fixtures/*.json
```

11. Update *settings.json* and *advanced_settings.json* files in the **saml** folder

12. See a deployment checklist and change your settings
```
$ python manage.py check --deploy


# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/
# CSRF_COOKIE_SECURE = True
# SESSION_COOKIE_SECURE = True
# SECURE_BROWSER_XSS_FILTER = True
# SECURE_CONTENT_TYPE_NOSNIFF = True
# SECURE_SSL_REDIRECT = True
# X_FRAME_OPTIONS = 'DENY'
```

13. Now, it's good to go. Run this web application in your production!
```
$ python manage.py runserver
```

14. Timezone in settings.py
https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

```
# Choose the timezone where you live
TIME_ZONE = 'America/Vancouver'
```


## Login locally
1. Create a superuser
```
# Reference: https://docs.djangoproject.com/en/2.2/topics/auth/default/
$ python manage.py createsuperuser --username=joe --email=joe@example.com
```

2. Run this app
```
$ python manage.py runserver
```


3. If you would like to log in through the local login, please change **LOCAL_LOGIN** to **True** in settings.py.
```
LOCAL_LOGIN=True
```
Open a new window with an URL ``` http://localhost:8000/accounts/local_login/ ```


Happy coding!
