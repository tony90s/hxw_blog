import re

from django.contrib.auth.models import User

from rest_framework import serializers
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


class UpdatePasswordSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=6, max_length=32)
    new_password = serializers.CharField(min_length=6, max_length=32)
    confirm_password = serializers.CharField(min_length=6, max_length=32)

    def validate_password(self, value):
        password = self.context['request'].data.get('password')
        if not password:
            raise serializers.ValidationError("原密码不能空。")
        if not self.instance.check_password(password):
            raise serializers.ValidationError('原密码错误，请重新输入。')
        return password

    def validate_new_password(self, value):
        new_password = self.context['request'].data.get('new_password')
        confirm_password = self.context['request'].data.get('confirm_password')
        if not new_password:
            raise serializers.ValidationError("新密码不能为空。")

        if not reg_password.match(new_password):
            raise serializers.ValidationError("新密码格式有误，请重新输入。")
        if new_password != confirm_password:
            raise serializers.ValidationError("密码不一致，请重新输入。")
        return new_password

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
        verification_code = self.context['request'].data.get('verification_code')
        if not verification_code:
            raise serializers.ValidationError('请输入验证码。')
        if not reg_verification_code.match(verification_code):
            raise serializers.ValidationError('验证码为6位数字，请重新输入。')

        verification_code_in_session = self.context['request'].session.get('verification_code', '')
        if not verification_code_in_session:
            raise serializers.ValidationError('验证码已过期，请重新获取。')
        if verification_code != verification_code_in_session:
            raise serializers.ValidationError('验证码错误，请重新输入。')
        return verification_code

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
        password = self.context['request'].data.get('password')
        if not password:
            raise serializers.ValidationError("密码不能为空。")
        if not reg_password.match(password):
            raise serializers.ValidationError("密码格式有误，请重新输入。")
        return password

    def validate_verification_code(self, value):
        verification_code = self.context['request'].data.get('verification_code')
        if not verification_code:
            raise serializers.ValidationError('请输入验证码。')
        if not reg_verification_code.match(verification_code):
            raise serializers.ValidationError('验证码为6位数字，请重新输入。')

        verification_code_in_session = self.context['request'].session.get('verification_code', '')
        if not verification_code_in_session:
            raise serializers.ValidationError('验证码已过期，请重新获取。')
        if verification_code != verification_code_in_session:
            raise serializers.ValidationError('验证码错误，请重新输入。')
        return verification_code

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
