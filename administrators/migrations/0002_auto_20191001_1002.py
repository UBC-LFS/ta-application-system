# Generated by Django 2.2 on 2019-10-01 17:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('administrators', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='classification',
            unique_together={('year', 'name')},
        ),
    ]
