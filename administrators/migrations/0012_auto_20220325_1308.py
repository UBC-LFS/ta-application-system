# Generated by Django 2.2.27 on 2022-03-25 20:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrators', '0011_applicationreset'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coursesection',
            name='name',
            field=models.CharField(max_length=12, unique=True),
        ),
    ]
