# TA Application System

This project is a web-based TA hiring process system.

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

3. Open a new window with an URL ``` http://localhost:8000/accounts/admin/login/ ```


## Summary of Deployment

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
```

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
$ python manage.py makemigrations
$ python manage.py migrate
```

10. Add valid certificate information
```
$ python manage.py loaddata certs
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

Happy coding!
