import re

from django.contrib.auth.models import User

from rest_framework import serializers

from utils.file_handling import get_thumbnail
from account.models import OauthLogin

reg_password = re.compile('^[\.\w@_-]{6,32}$')
reg_verification_code = re.compile('^\d{6}$')


class UserInfoSerializer(serializers.ModelSerializer):
    gender = serializers.CharField(source='profile.gender')
    bio = serializers.CharField(source='profile.bio')

    class Meta:
        model = User
        fields = ('username', 'gender', 'bio')

    def update(self, instance, validated_data):
        profile = instance.profile
        instance.username = validated_data.get('username', instance.username)
        profile.gender = validated_data.get('profile').get('gender', profile.gender)
        profile.bio = validated_data.get('profile').get('bio', profile.bio)
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
    password = serializers.CharField(min_length=6, max_length=32)
    new_password = serializers.CharField(min_length=6, max_length=32)
    confirm_password = serializers.CharField(min_length=6, max_length=32)

    def validate_password(self, value):
        if not value:
            raise serializers.ValidationError("原密码不能空。")
        if not self.instance.check_password(value):
            raise serializers.ValidationError('原密码错误，请重新输入。')
        return value

    def validate_new_password(self, value):
        confirm_password = self.context['request'].data.get('confirm_password')
        if not value:
            raise serializers.ValidationError("新密码不能为空。")
        if not reg_password.match(value):
            raise serializers.ValidationError("新密码格式有误，请重新输入。")
        if value != confirm_password:
            raise serializers.ValidationError("密码不一致，请重新输入。")
        return value

    def create(self, validated_data):
        return None

    def update(self, instance, validated_data):
        instance.set_password(validated_data.get('new_password'))
        instance.save(using='write')
        return instance


class ChangeEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    verification_code = serializers.CharField(max_length=6)

    def validate_verification_code(self, value):
        if not value:
            raise serializers.ValidationError('请输入验证码。')
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
    email = serializers.EmailField()
    verification_code = serializers.CharField(max_length=6)
    password = serializers.CharField(min_length=6, max_length=32)

    def validate_password(self, value):
        if not value:
            raise serializers.ValidationError("密码不能为空。")
        if not reg_password.match(value):
            raise serializers.ValidationError("密码格式有误，请重新输入。")
        return value

    def validate_verification_code(self, value):
        if not value:
            raise serializers.ValidationError('请输入验证码。')
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


class UnbindingSocialLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = OauthLogin
        fields = ('auth_type', 'user_id')
