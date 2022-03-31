# Generated by Django 2.2.27 on 2022-03-28 22:34

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0006_confidentiality_date_of_birth'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='student_year',
            field=models.CharField(blank=True, choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'), ('11', '11'), ('12', '12')], max_length=2, null=True),
        ),
        migrations.CreateModel(
            name='Alert',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('has_read', models.BooleanField(default=False)),
                ('created_at', models.DateField(auto_now_add=True)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='AlertEmail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.CharField(max_length=4)),
                ('term', models.CharField(max_length=20)),
                ('job_code', models.CharField(max_length=5)),
                ('job_number', models.CharField(max_length=5)),
                ('job_section', models.CharField(max_length=12)),
                ('sender', models.CharField(max_length=256)),
                ('receiver_name', models.CharField(max_length=256)),
                ('receiver_email', models.CharField(max_length=256)),
                ('title', models.CharField(max_length=256)),
                ('message', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('instructor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-pk'],
                'unique_together': {('year', 'term', 'job_code', 'job_number', 'job_section', 'instructor', 'receiver_email')},
            },
        ),
    ]
