# Generated by Django 2.2 on 2020-01-29 01:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrators', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='how_interested',
            field=models.CharField(choices=[('0', 'Select'), ('1', 'Not at all'), ('2', 'Marginally'), ('3', 'Somewhat'), ('4', 'Very'), ('5', 'Most')], max_length=1),
        ),
        migrations.AlterField(
            model_name='application',
            name='how_qualified',
            field=models.CharField(choices=[('0', 'Select'), ('1', 'Not at all'), ('2', 'Marginally'), ('3', 'Somewhat'), ('4', 'Very'), ('5', 'Most')], max_length=1),
        ),
    ]
