# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-04 04:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0003_auto_20171119_2125'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='type',
            field=models.IntegerField(choices=[(1, 'Python'), (2, 'Linux'), (3, 'Django'), (4, '前端技术'), (5, '杂记')], default=1, verbose_name='类别'),
        ),
    ]
