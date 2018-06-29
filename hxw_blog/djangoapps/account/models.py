from django.conf import settings
from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    class GENDER:
        MALE = 'm'
        FEMALE = 'f'

    GENDER_CHOICES = (
        (GENDER.MALE, '男'),
        (GENDER.FEMALE, '女')
    )
    user = models.OneToOneField(User, unique=True, db_index=True, related_name='profile')
    gender = models.CharField(blank=True, max_length=6, choices=GENDER_CHOICES, default=GENDER.MALE)
    bio = models.CharField(blank=True, max_length=64, default='')
    mobile = models.CharField(blank=True, max_length=16, default='')
    avatar = models.ImageField(upload_to='avatar', blank=True, default="/avatar/default_avatar.jpg")

    class Meta:
        db_table = "auth_userprofile"


def render_user_info(user):
    return {
        'user_id': user.id,
        'username': user.username,
        'avatar': settings.HOST + user.profile.avatar.url,
        'gender': user.profile.get_gender_display(),
        'bio': user.profile.bio
    }


class OauthLogin(models.Model):
    class TYPE:
        WEIBO = 1
        WECHAT = 2
        QQ = 3
        ALIPAY = 4

    TYPE_CHOICES = (
        (TYPE.WEIBO, 'weibo'),
        (TYPE.WECHAT, 'wechat'),
        (TYPE.QQ, 'qq'),
        (TYPE.ALIPAY, '支付宝')
    )
    auth_type = models.IntegerField(choices=TYPE_CHOICES, default=TYPE.WEIBO, verbose_name='授权类别')
    user_id = models.IntegerField(db_index=True, verbose_name='用户id')
    oauth_id = models.CharField(max_length=128, default='')
    oauth_access_token = models.CharField(max_length=128, default='')
    oauth_expires = models.IntegerField(default=0, verbose_name='token有效期')

    class Meta:
        db_table = "auth_oauth_login"
