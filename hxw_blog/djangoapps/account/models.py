from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    class GENDER:
        MALE = 'm'
        FEMALE = 'f'

    GENDER_CHOICES = (
        (GENDER.MALE, 'male'),
        (GENDER.FEMALE, 'female')
    )

    class UerType:
        OFFICIAL = 0
        WEIBO = 1
        WECHAT = 2
        QQ = 3

    USER_TYPE_CHOICES = (
        (UerType.OFFICIAL, '官方帐号'),
        (UerType.WEIBO, '微博'),
        (UerType.WECHAT, '微信'),
        (UerType.QQ, 'QQ')
    )
    user_type = models.IntegerField(choices=USER_TYPE_CHOICES, default=UerType.OFFICIAL, verbose_name='用户类型')
    user = models.OneToOneField(User, unique=True, db_index=True, related_name='profile')
    gender = models.CharField(blank=True, max_length=6, choices=GENDER_CHOICES, default=GENDER.MALE)
    #nick_name = models.CharField(blank=True, max_length=32, default='')
    bio = models.CharField(blank=True, max_length=120, default='')
    mobile = models.CharField(blank=True, max_length=16, default='')
    avatar = models.ImageField(upload_to='avatar', blank=True, default="/avatar/default_avatar.jpg")

    class Meta:
        db_table = "auth_userprofile"


class OauthLogin(models.Model):
    class TYPE:
        WEIBO = 1

    TYPE_CHOICES = (
        (TYPE.WEIBO, 'weibo'),
    )
    auth_type = models.IntegerField(choices=TYPE_CHOICES, default=TYPE.WEIBO, verbose_name='授权类别')
    user_id = models.IntegerField(db_index=True, verbose_name='用户id')
    oauth_id = models.CharField(max_length=128, default='')
    oauth_access_token = models.CharField(max_length=128, default='')
    oauth_expires = models.IntegerField(default=0, verbose_name='token有效期')

    class Meta:
        db_table = "auth_oauth_login"
