import re

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

from account.models import UserProfile, OauthLogin

reg_username = re.compile('^[\w_\u4e00-\u9fa5]{2,32}$')
reg_password = re.compile('^[\.\w@_-]{6,32}$')
reg_verification_code = re.compile('^\d{6}$')


class LoginForm(forms.Form):
    account = forms.EmailField(required=True)
    password = forms.CharField(required=True, min_length=6, max_length=32)

    def clean(self):
        account = self.cleaned_data.get('account')
        password = self.cleaned_data.get('password')

        users = User.objects.using('read').filter(email=account)
        if not users.exists():
            raise forms.ValidationError('该邮箱尚未注册')
        user = authenticate(username=users[0].get_username(), password=password)
        if user is None:
            raise forms.ValidationError('密码错误，请重新输入')
        return self.cleaned_data


class ResetPasswordForm(forms.Form):
    email = forms.EmailField(required=True)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        users = User.objects.using('read').filter(email=email)
        if not users.exists():
            raise forms.ValidationError('该邮箱尚未注册。')
        self.instance = users[0]
        return self.cleaned_data['email']


class GeneralEmailForm(forms.Form):
    email = forms.EmailField(required=True)


class EmailToResetPasswordForm(GeneralEmailForm):
    def clean_email(self):
        email = self.cleaned_data.get('email')
        users = User.objects.using('read').filter(email=email)
        if not users.exists():
            raise forms.ValidationError('该邮箱尚未注册。')
        return self.cleaned_data['email']


class CheckEmailIsBindForm(GeneralEmailForm):
    def clean_email(self):
        email = self.cleaned_data.get('email')
        users = User.objects.using('read').filter(email=email)
        if users.exists():
            raise forms.ValidationError('该邮箱已被绑定，换一个试试。')
        return self.cleaned_data['email']


class UnbindingSocialLoginForm(forms.Form):
    auth_type = forms.IntegerField(required=True)
    user_id = forms.IntegerField(required=True)

    def clean_auth_type(self):
        auth_type = self.cleaned_data.get('auth_type')
        if auth_type not in [value for value, display in OauthLogin.TYPE_CHOICES]:
            raise forms.ValidationError("'auth_type' must be 1,2,3,4.")
        return self.cleaned_data['auth_type']
