from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import datetime as dt


class Term(models.Model):
    """ Create a Term model """
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=256)
    by_month = models.IntegerField(
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    max_hours = models.IntegerField(
        default=192,
        validators=[MinValueValidator(0), MaxValueValidator(4000)]
    )
    class Meta:
        ordering = ['pk']

    def __str__(self):
        return self.code


class CourseCode(models.Model):
    """ Create a CourseCode model """
    name = models.CharField(max_length=5, unique=True)
    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class CourseNumber(models.Model):
    """ Create a CourseNumber model """
    name = models.CharField(max_length=5, unique=True)
    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class CourseSection(models.Model):
    """ Create a CourseSection model """
    name = models.CharField(max_length=5, unique=True)
    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Course(models.Model):
    ''' Create a Course model '''
    code = models.ForeignKey(CourseCode, on_delete=models.DO_NOTHING)
    number = models.ForeignKey(CourseNumber, on_delete=models.DO_NOTHING)
    section = models.ForeignKey(CourseSection, on_delete=models.DO_NOTHING)
    term = models.ForeignKey(Term, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=256, null=True)
    overview = models.TextField(null=True, blank=True)
    job_description = models.TextField(null=True, blank=True)
    job_note = models.TextField(null=True, blank=True)
    slug = models.SlugField(max_length=256, unique=True)

    class Meta:
        unique_together = ['code', 'number', 'section', 'term']
        ordering = ['code', 'number', 'term', 'section']

    def __str__(self):
        return '{0} {1} {2}'.format(self.code, self.number, self.section, self.term.code)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.code.name  + ' ' + self.number.name + ' ' + self.section.name + ' ' + self.name + ' ' + self.term.code)
        super(Course, self).save(*args, **kwargs)


class Session(models.Model):
    """ Create a Session model """

    year = models.CharField(max_length=4)
    term = models.ForeignKey(Term, on_delete=models.DO_NOTHING)
    title = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    is_visible = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)

    created_at = models.DateField(default=dt.date.today)
    updated_at = models.DateField(default=dt.date.today)
    slug = models.SlugField(max_length=256, unique=True)

    class Meta:
        unique_together = ['year', 'term']
        ordering = ['-year', 'term']

    def __str__(self):
        return '{0} {1} {2}'.format(self.year, self.term.code, self.title)

    def save(self, *args, **kwargs):
        """ Make a slug """
        self.slug = slugify(self.year + ' ' + self.term.code)
        super(Session, self).save(*args, **kwargs)


class Job(models.Model):
    course_overview = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    instructors = models.ManyToManyField(User)

    # Admins can assign TA hours
    assigned_ta_hours = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(4000)]
    )

    # Add up all student's TA hours
    accumulated_ta_hours = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(4000)]
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateField(default=dt.date.today)
    updated_at = models.DateField(default=dt.date.today)

    def __str__(self):
        return '{0} {1} {2} {3} {4}'.format(self.session.year, self.session.term.code, self.course.code.name, self.course.number.name, self.course.section.name)
    class Meta:
        ordering = ['session', 'course']


class Classification(models.Model):
    year = models.CharField(max_length=10)
    name = models.CharField(max_length=10)
    wage = models.FloatField()
    is_active = models.BooleanField(default=True)
    slug = models.SlugField(max_length=256, unique=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.year + ' ' + self.name)
        super(Classification, self).save(*args, **kwargs)

    class Meta:
        unique_together = ['year', 'name']
        ordering = ['-year', '-wage']

class Application(models.Model):
    """ This is a model for applications of students """

    PREFERENCE_CHOICES = [
        ('0', 'Select'),
        ('1', 'Not at all'),
        ('2', 'Marginally'),
        ('3', 'Somewhat'),
        ('4', 'Very'),
        ('5', 'Most')
    ]

    NONE = '0'
    NO_PREFERENCE = '1'
    ACCEPTABLE = '2'
    REQUESTED = '3'
    CRITICAL_REQUESTED = '4'

    INSTRUCTOR_PREFERENCE_CHOICES = [
        (NONE, 'None'),
        (NO_PREFERENCE, 'No Preference'),
        (ACCEPTABLE, 'Acceptable'),
        (REQUESTED, 'Requested'),
        (CRITICAL_REQUESTED, 'Critical Requested')
    ]

    applicant = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)

    supervisor_approval = models.BooleanField()
    how_qualified = models.CharField(max_length=1, choices=PREFERENCE_CHOICES)
    how_interested = models.CharField(max_length=1, choices=PREFERENCE_CHOICES)
    availability = models.BooleanField()
    availability_note = models.TextField(null=True, blank=True)

    classification = models.ForeignKey(Classification, on_delete=models.DO_NOTHING, null=True, blank=True)
    note = models.TextField(null=True, blank=True)

    instructor_preference = models.CharField(max_length=1, choices=INSTRUCTOR_PREFERENCE_CHOICES, default=NONE)
    is_declined_reassigned = models.BooleanField(default=False)
    is_terminated = models.BooleanField(default=False)

    created_at = models.DateField(default=dt.date.today)
    updated_at = models.DateField(default=dt.date.today)
    slug = models.SlugField(max_length=256, unique=True)

    class Meta:
        ordering = ['job', 'applicant']

    def save(self, *args, **kwargs):
        self.slug = slugify(self.job.session.slug + ' ' + self.job.course.slug + ' application by ' + self.applicant.username)
        super(Application, self).save(*args, **kwargs)


class ApplicationStatus(models.Model):
    ''' Application Status '''
    NONE = '0'
    SELECTED = '1'
    OFFERED = '2'
    ACCEPTED = '3'
    DECLINED = '4'
    CANCELLED = '5'
    ASSSIGNED_CHOICES = [(NONE, 'None'), (SELECTED, 'Selected'), (OFFERED, 'Offered'), (ACCEPTED, 'Accepted'), (DECLINED, 'Declined'), (CANCELLED, 'Cancelled')]

    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    assigned = models.CharField(max_length=1, choices=ASSSIGNED_CHOICES, default=NONE)
    assigned_hours = models.FloatField(
        default=0.0,
        validators=[MaxValueValidator(4000)]
    )
    parent_id = models.CharField(max_length=256, null=True, blank=True)
    created_at = models.DateField(default=dt.date.today)

    class Meta:
        ordering = ['pk']

class AdminDocuments(models.Model):
    ''' Admin Documents '''
    application = models.OneToOneField(Application, on_delete=models.CASCADE, primary_key=True)

    pin = models.CharField(max_length=4, null=True, blank=True)
    tasm = models.BooleanField(default=False)
    eform = models.CharField(max_length=6, unique=True, null=True, blank=True)
    speed_chart = models.CharField(max_length=4, null=True, blank=True)
    processing_note = models.TextField(null=True, blank=True)

    created_at = models.DateField(default=dt.date.today)
    updated_at = models.DateField(default=dt.date.today)


class Favourite(models.Model):
    ''' Favourite Job '''
    applicant = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    is_selected = models.BooleanField(default=False)
    created_at = models.DateField(default=dt.date.today)


class Email(models.Model):
    ''' Send an email to applicants '''
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    sender = models.CharField(max_length=256)
    receiver = models.CharField(max_length=256)
    title = models.CharField(max_length=256)
    message = models.TextField()
    type = models.CharField(max_length=256)
    created_at = models.DateField(default=dt.date.today)

    class Meta:
        ordering = ['-pk']


class AdminEmail(models.Model):
    ''' Admins can save an email message and title '''
    title = models.CharField(max_length=256)
    message = models.TextField()
    type = models.CharField(max_length=256, unique=True)
    created_at = models.DateField(default=dt.date.today)
    updated_at = models.DateField(default=dt.date.today)
    slug = models.SlugField(max_length=256, unique=True)

    class Meta:
        ordering = ['pk']

    def save(self, *args, **kwargs):
        self.slug = slugify(self.type)
        super(AdminEmail, self).save(*args, **kwargs)


class LandingPage(models.Model):
    ''' Landing Page contents '''
    title = models.CharField(max_length=256, null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    notice = models.TextField(null=True, blank=True)
    is_visible = models.BooleanField(default=False)
    created_at = models.DateField(default=dt.date.today)
    updated_at = models.DateField(default=dt.date.today)

    class Meta:
        ordering = ['pk']

    def __str__(self):
        return str(self.id)
