from rest_framework import serializers
from account.models import OauthLogin


class UnbindingSocialLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = OauthLogin
        fields = ('auth_type', 'user_id')
