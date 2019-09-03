# Generated by Django 2.2 on 2019-09-03 17:50

import datetime
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import users.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='Confidentiality',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('is_international', models.BooleanField(blank=True, null=True)),
                ('employee_number', models.CharField(blank=True, max_length=256, null=True, unique=True)),
                ('sin', models.FileField(blank=True, null=True, upload_to=users.models.create_sin_path, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx'])])),
                ('sin_expiry_date', models.DateField(blank=True, null=True)),
                ('study_permit', models.FileField(blank=True, null=True, upload_to=users.models.create_study_permit_path, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx'])])),
                ('study_permit_expiry_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateField(blank=True, null=True)),
                ('updated_at', models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Degree',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('slug', models.SlugField(max_length=256, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Program',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256, unique=True)),
                ('slug', models.SlugField(max_length=256, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Resume',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('file', models.FileField(blank=True, null=True, upload_to=users.models.create_resume_path, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx'])])),
                ('created_at', models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256, unique=True)),
                ('slug', models.SlugField(max_length=256, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256, unique=True)),
                ('slug', models.SlugField(max_length=256, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Training',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256, unique=True)),
                ('slug', models.SlugField(max_length=256, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('ubc_number', models.CharField(max_length=256, unique=True)),
                ('preferred_name', models.CharField(blank=True, max_length=256, null=True)),
                ('qualifications', models.TextField(blank=True, null=True)),
                ('prior_employment', models.TextField(blank=True, null=True)),
                ('special_considerations', models.TextField(blank=True, null=True)),
                ('program_others', models.TextField(blank=True, null=True)),
                ('graduation_date', models.DateField(blank=True, null=True)),
                ('training_details', models.TextField(blank=True, null=True)),
                ('lfs_ta_training', models.CharField(blank=True, choices=[('0', 'N/A'), ('1', 'Yes'), ('2', 'No')], max_length=1, null=True)),
                ('lfs_ta_training_details', models.TextField(blank=True, null=True)),
                ('ta_experience', models.CharField(blank=True, choices=[('0', 'N/A'), ('1', 'Yes'), ('2', 'No')], max_length=1, null=True)),
                ('ta_experience_details', models.TextField(blank=True, null=True)),
                ('created_at', models.DateField(default=datetime.date.today)),
                ('updated_at', models.DateField(default=datetime.date.today)),
                ('degrees', models.ManyToManyField(to='users.Degree')),
                ('program', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='users.Program')),
                ('roles', models.ManyToManyField(to='users.Role')),
                ('status', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='users.Status')),
                ('trainings', models.ManyToManyField(to='users.Training')),
            ],
        ),
    ]
