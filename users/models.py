import os
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.validators import FileExtensionValidator

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.base import ContentFile
import sys
import base64
import requests
from io import BytesIO
from PIL import Image as PILImage
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from administrators.models import Course

import datetime as dt


class Role(models.Model):
    SUPERADMIN = 'Superadmin'
    ADMIN = 'Admin'
    HR = 'HR'
    INSTRUCTOR = 'Instructor'
    STUDENT = 'Student'

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



def create_union_correspondence_path(instance, filename):
    return os.path.join('users', str(instance.user.username), 'union_correspondence', filename)


def create_compression_agreement_path(instance, filename):
    return os.path.join('users', str(instance.user.username), 'compression_agreement', filename)


class Confidentiality(models.Model):
    ''' '''

    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    is_international = models.BooleanField(null=True, blank=True)
    employee_number = models.CharField(max_length=7, unique=True, null=True, blank=True)

    sin = models.ImageField(upload_to=create_sin_path, null=True, blank=True)
    sin_expiry_date = models.DateField(null=True, blank=True)
    study_permit = models.ImageField(upload_to=create_study_permit_path, null=True, blank=True)
    study_permit_expiry_date = models.DateField(null=True, blank=True)

    pin = models.CharField(max_length=4, unique=True, null=True, blank=True)
    tasm = models.BooleanField(default=False)
    eform = models.CharField(max_length=6, unique=True, null=True, blank=True)
    speed_chart = models.CharField(max_length=256, unique=True, null=True, blank=True)

    union_correspondence = models.FileField(
        upload_to=create_union_correspondence_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        null=True,
        blank=True
    )

    compression_agreement = models.FileField(
        upload_to=create_compression_agreement_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        null=True,
        blank=True
    )

    processing_note = models.TextField(null=True, blank=True)

    created_at = models.DateField(null=True, blank=True)
    updated_at = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        #print('save =======')
        #print('sin ', self.sin)
        #print('study_permit ', self.study_permit)
        #print('self', self)
        #print('args', args)
        #print('kwargs', kwargs)

        if 'update_fields' in kwargs:
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
        upload_to=create_resume_path,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx'])],
        null=True,
        blank=True
    )
    created_at = models.DateField(default=dt.date.today)


class Profile(models.Model):
    ''' This is a model for a user profile '''

    LFS_TA_TRAINING_CHOICES = [
        ('0', 'N/A'),
        ('1', 'Yes'),
        ('2', 'No')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    student_number = models.CharField(max_length=8, unique=True, null=True, blank=True)
    preferred_name = models.CharField(max_length=256, null=True, blank=True)
    roles = models.ManyToManyField(Role)

    qualifications = models.TextField(null=True, blank=True)
    prior_employment = models.TextField(null=True, blank=True)
    special_considerations = models.TextField(null=True, blank=True)

    status = models.ForeignKey(Status, on_delete=models.DO_NOTHING, null=True, blank=True)
    program = models.ForeignKey(Program, on_delete=models.DO_NOTHING, null=True, blank=True)
    program_others = models.TextField(null=True, blank=True)
    graduation_date = models.DateField(null=True, blank=True)

    degrees = models.ManyToManyField(Degree)
    degree_details = models.TextField(null=True, blank=True)
    trainings = models.ManyToManyField(Training)
    training_details = models.TextField(null=True, blank=True)

    lfs_ta_training = models.CharField(max_length=1, choices=LFS_TA_TRAINING_CHOICES, null=True, blank=True)
    lfs_ta_training_details = models.TextField(null=True, blank=True)

    ta_experience = models.CharField(max_length=1, choices=LFS_TA_TRAINING_CHOICES, null=True, blank=True)
    ta_experience_details = models.TextField(null=True, blank=True)

    is_trimmed = models.BooleanField(default=False)
    created_at = models.DateField(default=dt.date.today)
    updated_at = models.DateField(default=dt.date.today)

    def __str__(self):
        return self.user.username



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

    img.thumbnail( (width, height), PILImage.ANTIALIAS )
    output = BytesIO()
    img.save(output, format='JPEG', quality=70) # Reduce a quality by 70%
    output.seek(0)

    fernet = encrypt_algorithm()
    encrypted = fernet.encrypt(output.read())
    content = ContentFile(encrypted)

    #img.close()
    #content.close()
    #output.close()

    return InMemoryUploadedFile(content,'ImageField', '{0}.jpg'.format(file_name), 'image/jpeg', sys.getsizeof(content), None)

def decrypt_image(username, obj, type, delete=None):
    filename = os.path.basename(obj.file.name)
    path = settings.TA_APP_URL + '/students/confidentiality/' + username + '/' + type + '/' + filename + '/download/'
    content = requests.get(path, stream=True).raw.read()
    #path = None

    fernet = encrypt_algorithm()
    decrypted = fernet.decrypt(content)
    url = 'data:image/jpg;base64,' + base64.b64encode(decrypted).decode('utf-8')

    imageStream = BytesIO(decrypted)
    img = PILImage.open(imageStream)
    #imageStream.seek(0)
    #imageStream.close()

    width, height = img.size

    #img.seek(0)
    #img.close()

    return {
        'filename': filename,
        'url': url,
        'width': width,
        'height': height
    }
