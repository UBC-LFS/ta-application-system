# Generated by Django 2.2.10 on 2020-06-08 22:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_avatar'),
    ]

    operations = [
        migrations.AddField(
            model_name='confidentiality',
            name='is_new_employee',
            field=models.BooleanField(default=True),
        ),
    ]
