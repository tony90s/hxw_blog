# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-15 06:15
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('article', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommentReply',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reply_at', models.DateTimeField(auto_now_add=True, verbose_name='回复时间')),
                ('content', models.CharField(default='', max_length=140, verbose_name='回复内容')),
            ],
            options={
                'verbose_name': 'comment_reply',
                'verbose_name_plural': 'comment_replies',
            },
        ),
        migrations.CreateModel(
            name='Praise',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('praise_type', models.IntegerField(choices=[(1, '博文'), (2, '评论'), (3, '评论回复')], default=1, verbose_name='点赞类型')),
                ('parent_id', models.IntegerField(verbose_name='点赞对象id')),
                ('praise_at', models.DateTimeField(auto_now_add=True, verbose_name='点赞时间')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='点赞人')),
            ],
            options={
                'verbose_name': 'praise',
                'verbose_name_plural': 'praises',
            },
        ),
        migrations.RemoveField(
            model_name='comment',
            name='parent',
        ),
        migrations.AddField(
            model_name='commentreply',
            name='comment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='article.Comment', verbose_name='所属评论'),
        ),
        migrations.AddField(
            model_name='commentreply',
            name='receiver',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comment_reply_receiver', to=settings.AUTH_USER_MODEL, verbose_name='接受者'),
        ),
        migrations.AddField(
            model_name='commentreply',
            name='replier',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comment_reply_replier', to=settings.AUTH_USER_MODEL, verbose_name='回复人'),
        ),
    ]
