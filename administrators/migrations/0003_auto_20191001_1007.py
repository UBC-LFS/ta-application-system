# Generated by Django 2.2 on 2019-10-01 17:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrators', '0002_auto_20191001_1002'),
    ]

    operations = [
        migrations.AlterField(
            model_name='classification',
            name='slug',
            field=models.SlugField(max_length=256),
        ),
    ]
