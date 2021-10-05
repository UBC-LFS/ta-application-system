# Upgrade

### History

_2021-08-26_

##### New features
* Reset function: a new class **ApplicationReset** in models has been added to reset SELECTED, DECLINED and TERMINATED applications

The following commands are required to run this application properly.
```
$ python manage.py collectstatic --noinput
$ python manage.py migrate
```

_2021-10-05_

##### New features
* Added a **Summary Report** for supervisors to each session. This report contains the information of courses and TAs.

The following commands are required to run this application properly.
```
$ python manage.py collectstatic --noinput
```
