# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-07-04 02:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0013_auto_20180614_1824'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='background',
            field=models.ImageField(blank=True, default='/background/default_background.jpg', upload_to='background'),
        ),
    ]