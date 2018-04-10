from django.contrib.auth.models import User

from rest_framework import serializers
from account.models import OauthLogin


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


class UnbindingSocialLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = OauthLogin
        fields = ('auth_type', 'user_id')
