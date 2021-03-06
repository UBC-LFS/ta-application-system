# Generated by Django 2.2.9 on 2020-03-27 18:01

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrators', '0003_auto_20200213_0843'),
    ]

    operations = [
        migrations.CreateModel(
            name='LandingPage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=256, null=True)),
                ('message', models.TextField(blank=True, null=True)),
                ('notice', models.TextField(blank=True, null=True)),
                ('is_visible', models.BooleanField(default=False)),
                ('created_at', models.DateField(default=datetime.date.today)),
                ('updated_at', models.DateField(default=datetime.date.today)),
            ],
            options={
                'ordering': ['pk'],
            },
        ),
    ]
