# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-06-24 01:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0011_auto_20180420_1628'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='be_replied_comment_id',
            field=models.IntegerField(db_index=True, default=0, verbose_name='被回复的评论id'),
        ),
        migrations.AddField(
            model_name='comment',
            name='parent_id',
            field=models.IntegerField(db_index=True, default=0, verbose_name='父级评论id'),
        ),
        migrations.AddField(
            model_name='comment',
            name='receiver_id',
            field=models.IntegerField(db_index=True, default=0, verbose_name='接受者'),
        ),
    ]