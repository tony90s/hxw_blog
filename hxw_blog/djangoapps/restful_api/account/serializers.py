import re

from django.conf import settings
from django.contrib.auth.models import User

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from utils.file_handling import get_thumbnail
from account.models import UserProfile, OauthLogin
from article.models import Article, get_user_article_count, get_user_praises_count
from restful_api.account.validators import RegMatchValidator

reg_verification_code = re.compile('^\d{6}$')


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(
        required=True,
        min_length=2,
        max_length=32,
        validators=[
            UniqueValidator(queryset=User.objects.using('read').all(), message='昵称已被使用，请重新输入。'),
            RegMatchValidator(pattern=r'^[\w.@_\u4e00-\u9fa5]{2,32}$', message='昵称格式有误，请重新输入。')
        ]
    )
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.using('read').all(), message='Email已注册，请登录。')]
    )
    password = serializers.CharField(
        required=True,
        min_length=6,
        max_length=32,
        validators=[RegMatchValidator(pattern=r'^[\w!@#$%^&*?,.;_]{6,32}$', message='密码格式有误，请重新输入。')]
    )
    confirm_password = serializers.CharField(required=True, min_length=6, max_length=32)

    def validate_confirm_password(self, value):
        password = self.context['request'].data.get('password')
        if password != value:
            raise serializers.ValidationError('密码输入不一致')
        return value

    def create(self, validated_data):
        username = validated_data.get('username')
        email = validated_data.get('email')
        password = validated_data.get('password')

        user = User.objects.create_user(username, email, password)
        user_profile = UserProfile()
        user_profile.user = user
        user_profile.save(using='write')
        return user

    def update(self, instance, validated_data):
        return None


class UserListSerializer(serializers.ModelSerializer):
    user_id = serializers.SerializerMethodField()
    avatar = serializers.ImageField(source='profile.avatar')
    bio = serializers.CharField(source='profile.bio')
    article_count = serializers.SerializerMethodField()
    gender = serializers.CharField(source='profile.gender')
    praises_count = serializers.SerializerMethodField()

    def get_user_id(self, user):
        return user.id

    def get_article_count(self, user):
        return get_user_article_count(user.id)

    def get_praises_count(self, user):
        return  get_user_praises_count(user.id)

    class Meta:
        model = User
        fields = ('user_id', 'username', 'avatar', 'gender', 'bio', 'article_count', 'praises_count')


class UserInfoSerializer(serializers.ModelSerializer):
    gender = serializers.CharField(source='profile.gender')
    bio = serializers.CharField(required=False, max_length=48, default='')

    class Meta:
        model = User
        fields = ('username', 'gender', 'bio')

    def update(self, instance, validated_data):
        profile = instance.profile
        instance.username = validated_data.get('username', instance.username)
        profile.gender = validated_data.get('profile').get('gender', profile.gender)
        profile.bio = validated_data.get('bio', profile.bio)
        instance.save(using='write')
        profile.save(using='write')
        return instance


class UpdateUserAvatarSerializer(serializers.Serializer):

    def validate(self, attrs):
        avatar = self.context['request'].FILES.get('avatar')
        if not avatar:
            raise serializers.ValidationError('请先选择图片。')
        if re.match(r'image', avatar.content_type) is None:
            raise serializers.ValidationError('请选择正确的图片!')
        img_max_size = 1024 * 5
        if avatar.size / 1024 > img_max_size:
            raise serializers.ValidationError('图片过大，请重新选择!')
        attrs.update({'avatar': avatar})
        return attrs

    def create(self, validated_data):
        return None

    def update(self, instance, validated_data):
        thumbnail, error = get_thumbnail(validated_data.get('avatar'))
        if thumbnail is None:
            raise serializers.ValidationError('头像上传失败，请稍后重试。')
        instance.avatar = thumbnail
        instance.save(using='write')
        return instance


class UpdatePasswordSerializer(serializers.Serializer):
    password = serializers.CharField(required=True, min_length=6, max_length=32)
    new_password = serializers.CharField(
        required=True,
        min_length=6,
        max_length=32,
        validators=[RegMatchValidator(pattern=r'^[\w!@#$%^&*?,.;_]{6,32}$', message='新密码格式有误，请重新输入。')]
    )
    confirm_password = serializers.CharField(required=True, min_length=6, max_length=32)

    def validate_password(self, value):
        if not self.instance.check_password(value):
            raise serializers.ValidationError('原密码错误，请重新输入。')
        return value

    def validate_confirm_password(self, value):
        new_password = self.context['request'].data.get('new_password')
        if value != new_password:
            raise serializers.ValidationError("密码不一致，请重新输入。")
        return value

    def create(self, validated_data):
        return None

    def update(self, instance, validated_data):
        instance.set_password(validated_data.get('new_password'))
        instance.save(using='write')
        return instance


class ResetPasswordSerializer(serializers.Serializer):
    verification_code = serializers.CharField(required=True, max_length=6)
    password = serializers.CharField(
        required=True,
        min_length=6,
        max_length=32,
        validators=[RegMatchValidator(pattern=r'^[\w!@#$%^&*?,.;_]{6,32}$', message='密码格式有误，请重新输入。')]
    )
    confirm_password = serializers.CharField(required=True, min_length=6, max_length=32)

    def validate_verification_code(self, value):
        if not reg_verification_code.match(value):
            raise serializers.ValidationError('验证码为6位数字，请重新输入。')

        verification_code_in_session = self.context['request'].session.get('verification_code', '')
        if not verification_code_in_session:
            raise serializers.ValidationError('验证码已过期，请重新获取。')
        if value != verification_code_in_session:
            raise serializers.ValidationError('验证码错误，请重新输入。')
        return value

    def validate_confirm_password(self, value):
        password = self.context['request'].data.get('password')
        if value != password:
            raise serializers.ValidationError("密码不一致，请重新输入。")
        return value

    def create(self, validated_data):
        return None

    def update(self, instance, validated_data):
        instance.set_password(validated_data.get('password'))
        instance.save(using='write')
        return instance


class ChangeEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.using('read').all(), message='该邮箱已被绑定，换一个试试。')]
    )
    verification_code = serializers.CharField(required=True, max_length=6)

    def validate_verification_code(self, value):
        if not reg_verification_code.match(value):
            raise serializers.ValidationError('验证码为6位数字，请重新输入。')

        verification_code_in_session = self.context['request'].session.get('verification_code', '')
        if not verification_code_in_session:
            raise serializers.ValidationError('验证码已过期，请重新获取。')
        if value != verification_code_in_session:
            raise serializers.ValidationError('验证码错误，请重新输入。')
        return value

    def create(self, validated_data):
        return None

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email')
        instance.save(using='write')
        return instance


class BindEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.using('read').all(), message='该邮箱已被绑定，换一个试试。')]
    )
    verification_code = serializers.CharField(required=True, max_length=6)
    password = serializers.CharField(
        required=True,
        min_length=6,
        max_length=32,
        validators=[RegMatchValidator(pattern=r'^[\w!@#$%^&*?,.;_]{6,32}$', message='密码格式有误，请重新输入。')]
    )

    def validate_email(self, value):
        if self.context['request'].user.email:
            raise serializers.ValidationError('您已绑定邮箱，无需重复绑定。')
        return value

    def validate_verification_code(self, value):
        if not reg_verification_code.match(value):
            raise serializers.ValidationError('验证码为6位数字，请重新输入。')

        verification_code_in_session = self.context['request'].session.get('verification_code', '')
        if not verification_code_in_session:
            raise serializers.ValidationError('验证码已过期，请重新获取。')
        if value != verification_code_in_session:
            raise serializers.ValidationError('验证码错误，请重新输入。')
        return value

    def create(self, validated_data):
        return None

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email')
        instance.set_password(validated_data.get('password'))
        instance.save(using='write')
        return instance
