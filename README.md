# TA Application System

This project is a web-based TA hiring process system, and running on Django and Apache with PostgreSQL.

Wiki: https://github.com/UBC-LFS/ta-application-system/wiki

### Features
- Encrypt/Decrypt images
- Enable Masquerade mode
- Email sending services
- Used 6 different badges to display the status of job applications: **Applied**, **Selected**, **Accepted**, **Offered**, **Declined** and **Terminated**
- Shibboleth login technology

# Installation Guide

### Linux Container's Environment
- Ubuntu 22.04
- Python 3.10.6
- Django 4.2 or greater
- Apache 2.4.52
- Shibboleth: libapache2-mod-shib (3.3.0+dfsg1-1)

### Install prerequisites for Ubuntu

#### 1. Install the latest stable version of Git first if it does not exist

```
# https://git-scm.com/download/linux
$ sudo apt install software-properties-common
$ sudo add-apt-repository ppa:git-core/ppa
$ sudo apt update
$ sudo apt install git
```

#### 2. Clone this repository

```
$ git clone https://github.com/UBC-LFS/ta-application-system.git
```

#### 3. Install the python3 virtual environment and activate it

```
$ sudo apt update
$ sudo apt install python3-venv

$ python3 -m venv venv
$ source venv/bin/activate
```

#### 4. Install pip3

```
$ sudo apt update
$ sudo apt install python3-pip
$ pip3 install --upgrade pip
```

#### 5. Install requirements

```
$ cd ta-application-system
$ pip3 install -r requirements.txt

# errors might occur in some packages, then install the following packages
$ sudo apt-get install python3-setuptools python3-dev libxml2-dev libxmlsec1-dev libxmlsec1-openssl
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
ENCRYPT_SALT = os.environ['TA_APP_ENCRYPT_SALT']
ENCRYPT_PASSWORD = os.environ['TA_APP_ENCRYPT_PASSWORD']
TA_APP_URL = os.environ['TA_APP_URL']
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
LOCAL_LOGIN = False
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

10. Load data for local testing
```
$ python manage.py loaddata ta_app/fixtures/*.json
$ python manage.py loaddata users/fixtures/*.json
$ python manage.py loaddata administrators/fixtures/*.json
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

15. Test
```
$ python manage.py test accounts.tests.shib_login
$ python manage.py test users
$ python manage.py test instructors
$ python manage.py test students
$ python manage.py test observers
$ python manage.py test administrators.tests.test_sessions
$ python manage.py test administrators.tests.test_jobs
$ python manage.py test administrators.tests.test_courses
$ python manage.py test administrators.tests.test_applications
$ python manage.py test administrators.tests.test_preparations
$ python manage.py test administrators.tests.test_hrs
$ python manage.py test administrators.tests.test_admin_hrs
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

For scheduling tasks
$ python manage.py runserver --noreload

```


3. If you would like to log in through the local login, please change **LOCAL_LOGIN** to **True** in settings.py.
```
LOCAL_LOGIN=True
```
Open a new window with an URL ``` http://localhost:8000/accounts/local_login/ ```


**Upgrade Django**
```
pip install --upgrade django==new_version (e.g., 2.2.19)
```

Happy coding!
Thank you.
