import re

from django import forms
from django.contrib.auth.models import User

reg_email = re.compile('^[\w-]+(\.[\w-]+)*@[\w-]+(\.[\w-]+)+$')


class GeneralEmailForm(forms.Form):
    email = forms.EmailField(required=True)


class EmailToResetPasswordForm(GeneralEmailForm):
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError('请填入邮箱。')
        if not reg_email.match(email):
            raise forms.ValidationError('邮箱格式有误，请重新输入。')

        users = User.objects.using('read').filter(email=email)
        if not users.exists():
            raise forms.ValidationError('该邮箱尚未注册。')
        return self.cleaned_data['email']


class CheckEmailIsBindForm(GeneralEmailForm):
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError('请填入邮箱。')
        if not reg_email.match(email):
            raise forms.ValidationError('邮箱格式有误，请重新输入。')

        users = User.objects.using('read').filter(email=email)
        if users.exists():
            raise forms.ValidationError('该邮箱已被绑定，换一个试试。')
        return self.cleaned_data['email']
