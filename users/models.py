import os
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.validators import FileExtensionValidator

from administrators.models import Course
import shutil
import datetime as dt

ROLES = [
    { 'name': 'Student' },
    { 'name': 'Instructor' },
    { 'name': 'HR' },
    { 'name': 'Admin' },
    { 'name': 'Superadmin' }
]

STATUSES = [
    { 'name': 'Undergraduate student' },
    { 'name': 'Master student' },
    { 'name': 'Ph.D student' },
    { 'name': 'Instructor' },
    { 'name': 'Assistance Professor' },
    { 'name': 'Professor' },
    { 'name': 'Other' }
]


class Program(models.Model):
    name = models.CharField(max_length=256, unique=True)
    slug = models.SlugField(max_length=256, unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """ Make a slug """
        self.slug = slugify(self.name)
        super(Program, self).save(*args, **kwargs)

class Degree(models.Model):
    name = models.CharField(max_length=256)
    slug = models.SlugField(max_length=256, unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """ Make a slug """
        self.slug = slugify(self.name)
        super(Degree, self).save(*args, **kwargs)

class Training(models.Model):
    name = models.CharField(max_length=256, unique=True)
    slug = models.SlugField(max_length=256, unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """ Make a slug """
        self.slug = slugify(self.name)
        super(Training, self).save(*args, **kwargs)


class Role(models.Model):
    name = models.CharField(max_length=256, unique=True)
    slug = models.SlugField(max_length=256, unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """ Make a slug """
        self.slug = slugify(self.name)
        super(Role, self).save(*args, **kwargs)


class Status(models.Model):
    name = models.CharField(max_length=256, unique=True)
    slug = models.SlugField(max_length=256, unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """ Make a slug """
        self.slug = slugify(self.name)
        super(Status, self).save(*args, **kwargs)


def create_study_permit_path(instance, filename):
    return os.path.join('users', str(instance.user.username), 'study_permit', filename)

def create_work_permit_path(instance, filename):
    return os.path.join('users', str(instance.user.username), 'work_permit', filename)


class Confidentiality(models.Model):
    VISA_CHOICES = [
        ('0', 'None'),
        ('1', 'Type 1'),
        ('2', 'Type 2'),
        ('3', 'Type 3')
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    sin = models.CharField(max_length=256, unique=True, null=True, blank=True)
    employee_number = models.CharField(max_length=256, unique=True, null=True, blank=True)
    study_permit = models.FileField(
        upload_to=create_study_permit_path,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx'])],
        null=True,
        blank=True
    )
    study_permit_expiry_date = models.DateField(null=True, blank=True)
    work_permit = models.FileField(
        upload_to=create_work_permit_path,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx'])],
        null=True,
        blank=True
    )

    created_at = models.DateField(default=dt.date.today)
    updated_at = models.DateField(default=dt.date.today)

    """
    def delete_existing_study_permit_file(self, *args, **kwargs):
        ''' Remove existing files '''
        dir_path = os.path.join(settings.MEDIA_ROOT, 'users', str(self.user.username), 'study_permit')
        for root, dirs, files in os.walk(dir_path):
            for filename in files:
                os.remove(os.path.join(dir_path, filename))
        super(Confidentiality, self).delete(*args, **kwargs)

    def delete_existing_work_permit_file(self, *args, **kwargs):
        ''' Remove existing files '''
        dir_path = os.path.join(settings.MEDIA_ROOT, 'users', str(self.user.username), 'work_permit')
        for root, dirs, files in os.walk(dir_path):
            for filename in files:
                os.remove(os.path.join(dir_path, filename))
        super(Confidentiality, self).delete(*args, **kwargs)
    """



def create_resume_path(instance, filename):
    return os.path.join('users', str(instance.user.username), 'resume', filename)

class Resume(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    file = models.FileField(
        upload_to=create_resume_path,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx'])],
        null=True,
        blank=True
    )
    created_at = models.DateField(null=True, blank=True)

    """
    def delete_existing_file(self, *args, **kwargs):
        ''' Remove existing files '''
        dir_path = os.path.join(settings.MEDIA_ROOT, 'users', str(self.user.username), 'resume')
        for root, dirs, files in os.walk(dir_path):
            for filename in files:
                os.remove(os.path.join(dir_path, filename))
        super(Resume, self).delete(*args, **kwargs)
    """


#checked
class Profile(models.Model):
    """ This is a model for a user profile """

    LFS_TA_TRAINING_CHOICES = [
        ('0', 'N/A'),
        ('1', 'Yes'),
        ('2', 'No')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    ubc_number = models.CharField(max_length=256, unique=True)
    preferred_name = models.CharField(max_length=256, null=True, blank=True)
    roles = models.ManyToManyField(Role)

    qualifications = models.TextField(null=True, blank=True)
    prior_employment = models.TextField(null=True, blank=True)
    special_considerations = models.TextField(null=True, blank=True)

    status = models.ForeignKey(Status, on_delete=models.DO_NOTHING, null=True, blank=True)
    program = models.ForeignKey(Program, on_delete=models.DO_NOTHING, null=True, blank=True)
    graduation_date = models.DateField(null=True, blank=True)

    degrees = models.ManyToManyField(Degree)
    trainings = models.ManyToManyField(Training)

    lfs_ta_training = models.CharField(max_length=1, choices=LFS_TA_TRAINING_CHOICES, null=True, blank=True)
    lfs_ta_training_details = models.TextField(null=True, blank=True)

    ta_experience = models.CharField(max_length=1, choices=LFS_TA_TRAINING_CHOICES, null=True, blank=True)
    ta_experience_details = models.TextField(null=True, blank=True)

    created_at = models.DateField(default=dt.date.today)
    updated_at = models.DateField(default=dt.date.today)

    def __str__(self):
        return self.user.username
