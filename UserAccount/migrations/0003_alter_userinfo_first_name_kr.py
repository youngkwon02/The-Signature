# Generated by Django 3.2.2 on 2021-06-04 15:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('UserAccount', '0002_auto_20210328_1027'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userinfo',
            name='first_name_kr',
            field=models.CharField(max_length=16, verbose_name='first_name_kr'),
        ),
    ]
