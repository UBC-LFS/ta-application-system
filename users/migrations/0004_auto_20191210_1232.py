# Generated by Django 2.2 on 2019-12-10 20:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20191210_1224'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='degree_details',
            field=models.TextField(blank=True, help_text='Please indicate your degree details: most recent completed or conferred or multiple same type degrees (ex. BSc - Biochemistry - U of T, November 24, 2014).', null=True),
        ),
    ]
