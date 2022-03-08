# Upgrade

### History

_2022-03-08_
* Modified a summary of applicants on the Instructor's side.
- A **No offers** search option has been added, and CV information and resume has been placed in the data table.

_2021-10-05_

##### New features
* Added a **Summary Report** for supervisors to each session. This report contains the information of courses and TAs.

The following commands are required to run this application properly.
```
$ python manage.py collectstatic --noinput
```

_2021-08-26_

##### New features
* Reset function: a new class **ApplicationReset** in models has been added to reset SELECTED, DECLINED and TERMINATED applications

The following commands are required to run this application properly.
```
$ python manage.py collectstatic --noinput
$ python manage.py migrate
```
