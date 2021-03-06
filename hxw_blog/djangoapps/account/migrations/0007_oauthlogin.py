# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-02-27 01:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0006_auto_20180125_1657'),
    ]

    operations = [
        migrations.CreateModel(
            name='OauthLogin',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('auth_type', models.IntegerField(choices=[(1, 'weibo')], default=1, verbose_name='授权类别')),
                ('user_id', models.IntegerField(db_index=True, verbose_name='用户id')),
                ('oauth_id', models.CharField(default='', max_length=128)),
                ('oauth_access_token', models.CharField(default='', max_length=128)),
                ('oauth_expires', models.IntegerField(default=0, verbose_name='token有效期')),
            ],
            options={
                'db_table': 'auth_oauth_login',
            },
        ),
    ]
