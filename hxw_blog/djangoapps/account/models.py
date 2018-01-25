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
    user = models.OneToOneField(User, unique=True, db_index=True, related_name='profile')
    gender = models.CharField(blank=True, max_length=6, choices=GENDER_CHOICES, default=GENDER.MALE)
    #nick_name = models.CharField(blank=True, max_length=32, default='')
    bio = models.CharField(blank=True, max_length=120, default='')
    mobile = models.CharField(blank=True, max_length=16, default='')
    avatar = models.ImageField(upload_to='avatar', blank=True, default="/avatar/default_avatar.jpg")

    class Meta:
        db_table = "auth_userprofile"
