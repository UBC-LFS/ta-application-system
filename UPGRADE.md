# Upgrade

### History

_2021-08-26_

##### New feature
* Reset function: a new class **ApplicationReset** in models has been added to reset SELECTED, DECLINED and TERMINATED applications

The following commands are required to run this application properly.
```
$ python manage.py collectstatic --noinput
$ python manage.py migrate
```
