# Generated by Django 2.2 on 2019-11-07 21:24

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AdminEmail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=256)),
                ('message', models.TextField()),
                ('type', models.CharField(max_length=256, unique=True)),
                ('created_at', models.DateField(default=datetime.date.today)),
                ('updated_at', models.DateField(default=datetime.date.today)),
                ('slug', models.SlugField(max_length=256, unique=True)),
            ],
            options={
                'ordering': ['pk'],
            },
        ),
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('supervisor_approval', models.BooleanField()),
                ('how_qualified', models.CharField(choices=[('1', 'Not at all'), ('2', 'Marginally'), ('3', 'Somewhat'), ('4', 'Very'), ('5', 'Most')], max_length=1)),
                ('how_interested', models.CharField(choices=[('1', 'Not at all'), ('2', 'Marginally'), ('3', 'Somewhat'), ('4', 'Very'), ('5', 'Most')], max_length=1)),
                ('availability', models.BooleanField()),
                ('availability_note', models.TextField(blank=True, null=True)),
                ('note', models.TextField(blank=True, null=True)),
                ('instructor_preference', models.CharField(choices=[('0', 'None'), ('1', 'No Preference'), ('2', 'Acceptable'), ('3', 'Requested'), ('4', 'Critical Requested')], default='0', max_length=1)),
                ('is_terminated', models.BooleanField(default=False)),
                ('created_at', models.DateField(default=datetime.date.today)),
                ('updated_at', models.DateField(default=datetime.date.today)),
                ('slug', models.SlugField(max_length=256, unique=True)),
                ('applicant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['job', 'applicant'],
            },
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256, null=True)),
                ('slug', models.SlugField(max_length=256, unique=True)),
            ],
            options={
                'ordering': ['code', 'number', 'term', 'section'],
            },
        ),
        migrations.CreateModel(
            name='CourseCode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=5, unique=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='CourseNumber',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=5, unique=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='CourseSection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=5, unique=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Term',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=20, unique=True)),
                ('name', models.CharField(max_length=256)),
            ],
            options={
                'ordering': ['pk'],
            },
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.CharField(max_length=4)),
                ('title', models.CharField(max_length=256)),
                ('description', models.TextField(blank=True, null=True)),
                ('note', models.TextField(blank=True, null=True)),
                ('is_visible', models.BooleanField(default=False)),
                ('is_archived', models.BooleanField(default=False)),
                ('created_at', models.DateField(default=datetime.date.today)),
                ('updated_at', models.DateField(default=datetime.date.today)),
                ('slug', models.SlugField(max_length=256, unique=True)),
                ('term', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='administrators.Term')),
            ],
            options={
                'ordering': ['-year', 'term'],
                'unique_together': {('year', 'term')},
            },
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=256, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('qualification', models.TextField(blank=True, null=True)),
                ('note', models.TextField(blank=True, null=True)),
                ('assigned_ta_hours', models.FloatField(default=0.0)),
                ('accumulated_ta_hours', models.FloatField(default=0.0)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateField(default=datetime.date.today)),
                ('updated_at', models.DateField(default=datetime.date.today)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='administrators.Course')),
                ('instructors', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='administrators.Session')),
            ],
            options={
                'ordering': ['session', 'course'],
            },
        ),
        migrations.CreateModel(
            name='Email',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sender', models.CharField(max_length=256)),
                ('receiver', models.CharField(max_length=256)),
                ('title', models.CharField(max_length=256)),
                ('message', models.TextField()),
                ('type', models.CharField(max_length=256)),
                ('created_at', models.DateField(default=datetime.date.today)),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='administrators.Application')),
            ],
            options={
                'ordering': ['-pk'],
            },
        ),
        migrations.AddField(
            model_name='course',
            name='code',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='administrators.CourseCode'),
        ),
        migrations.AddField(
            model_name='course',
            name='number',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='administrators.CourseNumber'),
        ),
        migrations.AddField(
            model_name='course',
            name='section',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='administrators.CourseSection'),
        ),
        migrations.AddField(
            model_name='course',
            name='term',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='administrators.Term'),
        ),
        migrations.CreateModel(
            name='Classification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.CharField(max_length=4)),
                ('name', models.CharField(max_length=10)),
                ('wage', models.FloatField()),
                ('is_active', models.BooleanField(default=True)),
                ('slug', models.SlugField(max_length=256, unique=True)),
            ],
            options={
                'ordering': ['-year', '-wage'],
                'unique_together': {('year', 'name')},
            },
        ),
        migrations.CreateModel(
            name='ApplicationStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assigned', models.CharField(choices=[('0', 'None'), ('1', 'Selected'), ('2', 'Offered'), ('3', 'Accepted'), ('4', 'Declined'), ('5', 'Cancelled')], default='0', max_length=1)),
                ('assigned_hours', models.FloatField(default=0.0)),
                ('parent_id', models.CharField(blank=True, max_length=256, null=True)),
                ('created_at', models.DateField(default=datetime.date.today)),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='administrators.Application')),
            ],
            options={
                'ordering': ['pk'],
            },
        ),
        migrations.AddField(
            model_name='application',
            name='classification',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='administrators.Classification'),
        ),
        migrations.AddField(
            model_name='application',
            name='job',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='administrators.Job'),
        ),
        migrations.AlterUniqueTogether(
            name='course',
            unique_together={('code', 'number', 'section', 'term')},
        ),
    ]
