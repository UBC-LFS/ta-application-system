# Generated by Django 2.2 on 2019-09-06 18:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('administrators', '0007_auto_20190906_1115'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='coursecode',
            options={'ordering': ['pk']},
        ),
        migrations.AlterModelOptions(
            name='coursenumber',
            options={'ordering': ['pk']},
        ),
        migrations.AlterModelOptions(
            name='coursesection',
            options={'ordering': ['pk']},
        ),
        migrations.AlterModelOptions(
            name='term',
            options={'ordering': ['pk']},
        ),
    ]
