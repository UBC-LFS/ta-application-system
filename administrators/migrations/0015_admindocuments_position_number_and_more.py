# Generated by Django 4.2.13 on 2024-08-01 17:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrators', '0014_application_sta_confirmation'),
    ]

    operations = [
        migrations.AddField(
            model_name='admindocuments',
            name='position_number',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='admindocuments',
            name='worktag',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
