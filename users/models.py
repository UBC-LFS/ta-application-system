import os
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.validators import FileExtensionValidator, MinLengthValidator, MaxLengthValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.files.storage import default_storage

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.base import ContentFile
import sys
import base64
from io import BytesIO
from PIL import Image as PILImage
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from administrators.models import Session, Course

import datetime as dt


class Role(models.Model):
    SUPERADMIN = 'Superadmin'
    ADMIN = 'Admin'
    HR = 'HR'
    INSTRUCTOR = 'Instructor'
    STUDENT = 'Student'
    OBSERVER = 'Observer'

    name = models.CharField(max_length=256, unique=True)
    slug = models.SlugField(max_length=256, unique=True)

    class Meta: ordering = ['pk']
    def __str__(self): return self.name
    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Role, self).save(*args, **kwargs)


class Status(models.Model):
    name = models.CharField(max_length=256, unique=True)
    slug = models.SlugField(max_length=256, unique=True)

    class Meta: ordering = ['pk']
    def __str__(self): return self.name
    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Status, self).save(*args, **kwargs)

class Program(models.Model):
    name = models.CharField(max_length=256, unique=True)
    slug = models.SlugField(max_length=256, unique=True)

    class Meta: ordering = ['pk']
    def __str__(self): return self.name
    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Program, self).save(*args, **kwargs)

class Degree(models.Model):
    name = models.CharField(max_length=256, unique=True)
    slug = models.SlugField(max_length=256, unique=True)

    class Meta: ordering = ['pk']
    def __str__(self): return self.name
    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Degree, self).save(*args, **kwargs)

class Training(models.Model):
    name = models.CharField(max_length=256, unique=True)
    is_active = models.BooleanField(default=True)
    slug = models.SlugField(max_length=256, unique=True)

    class Meta: ordering = ['pk']
    def __str__(self): return self.name
    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Training, self).save(*args, **kwargs)

def create_sin_path(instance, filename):
    return os.path.join('users', str(instance.user.username), 'sin', filename)

def create_study_permit_path(instance, filename):
    return os.path.join('users', str(instance.user.username), 'study_permit', filename)

def create_personal_data_form_path(instance, filename):
    return os.path.join('users', str(instance.user.username), 'personal_data_form', filename)

def format_bytes(size):
    power = 2**10
    n = 0
    power_labels = {0 : '', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size > power:
        size /= power
        n += 1
    return str( round(size, 2) ) + ' ' + power_labels[n]

def FileSizeValidator(file):
    if int(file.size) > int(settings.MAX_UPLOAD_SIZE):
        raise ValidationError(
            _('The maximum file size that can be uploaded is 1.5 MB. The size of this file (%(name)s) is %(size)s.'), params={'name': file.name, 'size': format_bytes(int(file.size)) }, code='file_size_limit'
        )

def NumericalValueValidator(value):
    if value.isnumeric() == False:
        raise ValidationError(
            _('This field must be numerical value only.'), params={'value': value}, code='numerical_value'
        )


class Confidentiality(models.Model):
    '''
    Confidential Information

    personal_data_form: no longer available
     '''

    NATIONALITY_CHOICES = [
        ('0', 'Domestic Student'),
        ('1', 'International Student')
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    nationality = models.CharField(max_length=1, choices=NATIONALITY_CHOICES, null=True, blank=True)
    is_new_employee = models.BooleanField(default=True)
    employee_number = models.CharField(
        max_length=7,
        unique=True,
        null=True,
        blank=True,
        validators=[
            NumericalValueValidator,
            MinLengthValidator(7),
            MaxLengthValidator(7)
        ]
    )
    sin = models.ImageField(
        max_length=256,
        upload_to=create_sin_path,
        null=True,
        blank=True,
        validators=[FileSizeValidator]
    )
    sin_expiry_date = models.DateField(null=True, blank=True)
    study_permit = models.ImageField(
        max_length=256,
        upload_to=create_study_permit_path,
        null=True,
        blank=True,
        validators=[FileSizeValidator]
    )
    study_permit_expiry_date = models.DateField(null=True, blank=True)

    personal_data_form = models.FileField(
        max_length=256,
        upload_to=create_personal_data_form_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx']),
            FileSizeValidator
        ],
        null=True,
        blank=True
    )

    date_of_birth = models.DateField(null=True, blank=True)

    created_at = models.DateField(null=True, blank=True)
    updated_at = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        if 'update_fields' in kwargs:

            # To check where update fields are coming from
            # Note: administrators/edit_user doesn't need it
            if 'updated_at' in kwargs['update_fields']:
                if 'sin' in kwargs['update_fields']:
                    self.sin = encrypt_image(self.sin)
                if 'study_permit' in kwargs['update_fields']:
                    self.study_permit = encrypt_image(self.study_permit)
        else:
            if bool(self.sin): self.sin = encrypt_image(self.sin)
            if bool(self.study_permit): self.study_permit = encrypt_image(self.study_permit)

        super(Confidentiality, self).save(*args, **kwargs)


def create_resume_path(instance, filename):
    return os.path.join('users', str(instance.user.username), 'resume', filename)

class Resume(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    uploaded = models.FileField(
        max_length=256,
        upload_to=create_resume_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx']),
            FileSizeValidator
        ],
        null=True,
        blank=True
    )
    created_at = models.DateField(default=dt.date.today)

    def save(self, *args, **kwargs):
        super(Resume, self).save(*args, **kwargs)


class Profile(models.Model):
    ''' This is a model for a user profile '''

    LFS_TA_TRAINING_CHOICES = [
        ('0', 'N/A'),
        ('1', 'Yes'),
        ('2', 'No')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    student_number = models.CharField(
        max_length=8,
        unique=True,
        null=True,
        blank=True,
        validators=[
            NumericalValueValidator,
            MinLengthValidator(8),
            MaxLengthValidator(8)
        ]
    )
    preferred_name = models.CharField(
        max_length=256,
        null=True,
        blank=True
    )
    roles = models.ManyToManyField(Role)

    qualifications = models.TextField(
        null=True,
        blank=True
    )
    prior_employment = models.TextField(
        null=True,
        blank=True
    )
    special_considerations = models.TextField(
        null=True,
        blank=True
    )

    status = models.ForeignKey(Status, on_delete=models.DO_NOTHING, null=True, blank=True)
    program = models.ForeignKey(
        Program,
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True
    )

    program_others = models.TextField(
        null=True,
        blank=True
    )

    STUDENT_YEAR_CHOICES = [
        ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'),
        ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'), ('11', '11'), ('12', '12')
    ]
    student_year = models.CharField(max_length=2, choices=STUDENT_YEAR_CHOICES, null=True, blank=True)

    graduation_date = models.DateField(
        null=True,
        blank=True
    )

    degrees = models.ManyToManyField(Degree)

    degree_details = models.TextField(
        null=True,
        blank=True
    )
    trainings = models.ManyToManyField(Training)
    training_details = models.TextField(
        null=True,
        blank=True
    )

    lfs_ta_training = models.CharField(max_length=1, choices=LFS_TA_TRAINING_CHOICES, null=True, blank=True)
    lfs_ta_training_details = models.TextField(
        null=True,
        blank=True
    )

    ta_experience = models.CharField(max_length=1, choices=LFS_TA_TRAINING_CHOICES, null=True, blank=True)
    ta_experience_details = models.TextField(
        null=True,
        blank=True
    )

    is_trimmed = models.BooleanField(default=False)
    created_at = models.DateField(default=dt.date.today)
    updated_at = models.DateField(default=dt.date.today)

    def __str__(self):
        return self.user.username


class Alert(models.Model):
    ''' To check whether students check an alert message between March and April every year '''

    student = models.ForeignKey(User, on_delete=models.CASCADE)
    has_read = models.BooleanField(default=False)
    created_at = models.DateField(auto_now_add=True)


class AlertEmail(models.Model):
    ''' Instructors send an alert email to students '''
    year = models.CharField(max_length=4)
    term = models.CharField(max_length=20)
    job_code = models.CharField(max_length=5)
    job_number = models.CharField(max_length=5)
    job_section = models.CharField(max_length=12)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE)
    sender = models.CharField(max_length=256)
    receiver_name = models.CharField(max_length=256)
    receiver_email = models.CharField(max_length=256)
    title = models.CharField(max_length=256)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['year', 'term', 'job_code', 'job_number', 'job_section', 'instructor', 'receiver_name', 'receiver_email']
        ordering = ['-pk']


def create_avatar_path(instance, filename):
    return os.path.join('users', str(instance.user.username), 'avatar', filename)

class Avatar(models.Model):
    ''' This is a user profile picture '''
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    uploaded = models.ImageField(
        max_length=256,
        upload_to=create_avatar_path,
        validators=[FileSizeValidator],
        null=True,
        blank=True
    )
    created_at = models.DateField(default=dt.date.today)

    def save(self, *args, **kwargs):
        ''' Reduce a size and quality of the image '''
        if 'update_fields' not in kwargs:
            if bool(self.uploaded):
                file_split = os.path.splitext(self.uploaded.name)
                file_name = file_split[0]
                file_extension = file_split[1]

                if self.uploaded and file_extension.lower() in ['.jpg', '.jpeg', '.png']:
                    img = PILImage.open( self.uploaded )
                    if img.mode == 'P':
                        img = img.convert('RGB')

                    if img.mode in ['RGBA']:
                        background = PILImage.new( img.mode[:-1], img.size, (255,255,255) )
                        background.paste(img, img.split()[-1])
                        img = background

                    width, height = compress_image(img)

                    img.thumbnail( (width, height), PILImage.ANTIALIAS )
                    output = BytesIO()
                    img.save(output, format='JPEG', quality=70) # Reduce a quality by 70%
                    output.seek(0)

                    img.close()

                    self.uploaded = InMemoryUploadedFile(output,'ImageField', "%s.jpg" % file_name, 'image/jpeg', sys.getsizeof(output), None)
        super(Avatar, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete actual files
        default_storage.delete(self.uploaded.path)
        super(Avatar, self).delete(*args, **kwargs)


def compress_image(img):
    ''' Compress an image '''
    # Check image's width and height
    width, height = img.size
    if width > 4000 or height > 3000:
        width, height = width/3.0, height/3.0
    elif width > 3000 or height > 2000:
        width, height = width/2.5, height/2.5
    elif width > 2000 or height > 1000:
        width, height = width/2.0, height/2.0
    elif width > 1000 or height > 500:
        width, height = width/1.5, height/1.5

    return width, height

"""
cryptography
https://github.com/pyca/cryptography

The cryptography alogorithm would be used to encrypt and decrypt attachments for SIN and Study Permit files
"""
def encrypt_algorithm():
    return Fernet(base64.urlsafe_b64encode(PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=settings.ENCRYPT_SALT.encode('utf-8'),
        iterations=100000,
        backend=default_backend()
    ).derive(settings.ENCRYPT_PASSWORD.encode('utf-8'))))

def encrypt_image(obj):
    ''' Enrypte an impage '''
    file_split = os.path.splitext(obj.name)
    file_name = file_split[0]
    file_extension = file_split[1]

    img = PILImage.open(obj)
    if img.mode in ['RGBA']:
        background = PILImage.new( img.mode[:-1], img.size, (255,255,255) )
        background.paste(img, img.split()[-1])
        img = background

    width, height = compress_image(img)

    img.thumbnail( (width, height), PILImage.ANTIALIAS )
    output = BytesIO()
    img.save(output, format='JPEG', quality=70) # Reduce a quality by 70%
    output.seek(0)

    fernet = encrypt_algorithm()
    encrypted = fernet.encrypt(output.read())
    content = ContentFile(encrypted)

    img.close()
    content.close()
    output.close()

    return InMemoryUploadedFile(content, 'ImageField', '{0}.jpg'.format(file_name), 'image/jpeg', sys.getsizeof(content), None)

def decrypt_image(obj):
    fernet = encrypt_algorithm()

    content = None
    with obj.open() as f:
        content = f.read()

    decrypted = fernet.decrypt(content)
    url = 'data:image/jpg;base64,' + base64.b64encode(decrypted).decode('utf-8')

    imageStream = BytesIO(decrypted)
    img = PILImage.open(imageStream)
    width, height = img.size

    imageStream.close()
    img.close()

    return {
        'filename': os.path.basename(obj.file.name),
        'url': url,
        'width': width,
        'height': height
    }
