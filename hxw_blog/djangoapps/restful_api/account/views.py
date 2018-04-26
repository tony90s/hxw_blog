from copy import deepcopy
import logging
import os
import re

from django.conf import settings
from django.http import Http404, QueryDict
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.contrib.auth import logout, authenticate, login

from rest_framework.views import APIView
from rest_framework import serializers, generics, permissions
from rest_framework.response import Response

from restful_api.account.serializers import (
    UserInfoSerializer,
    UpdateUserAvatarSerializer,
    UpdatePasswordSerializer,
    ResetPasswordSerializer,
    ChangeEmailSerializer,
    BindEmailSerializer
)
from restful_api.account.forms import (
    RegisterForm,
    LoginForm,
    ResetPasswordForm,
    GeneralEmailForm,
    EmailToResetPasswordForm,
    CheckEmailIsBindForm,
    UnbindingSocialLoginForm
)
from account.cookies import set_logged_in_cookies
from account.models import UserProfile, OauthLogin
from utils.file_handling import get_thumbnail
from utils import generate_verification_code
from utils.html_email_utils import send_html_mail
from utils.rest_framework.authentication import (
    OAuth2AuthenticationAllowInactiveUser,
    SessionAuthenticationAllowInactiveUser
)

reg_username = re.compile('^[\w_\u4e00-\u9fa5]{2,32}$')
reg_password = re.compile('^[\.\w@_-]{6,32}$')
reg_email = re.compile('^[\w-]+(\.[\w-]+)*@[\w-]+(\.[\w-]+)+$')

logger = logging.getLogger('api.account')


class RegisterView(APIView):
    def post(self, request, *args, **kwargs):
        form = RegisterForm(request.data)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        user = form.create()
        login(request, user)

        # send email to notice users when register successfully
        redirect_url = request.data.get('redirect_url', '').replace('#', '')
        if redirect_url == '':
            redirect_url = reverse('index')
        response = Response({
            'code': 200,
            'msg': '注册成功',
            'redirect_url': redirect_url
        })
        response = set_logged_in_cookies(request, response, user)
        return response


class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        form = LoginForm(request.data)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        email = form.cleaned_data.get('account')
        user = User.objects.using('read').get(email=email)
        login(request, user)

        if request.data.get('remember') == 'true':
            request.session.set_expiry(604800)
        else:
            request.session.set_expiry(0)

        redirect_url = request.data.get('redirect_url', '').replace('#', '')
        if redirect_url == '':
            redirect_url = reverse('index')

        response = Response({'code': '200', 'msg': '登录成功', 'redirect_url': redirect_url})
        response = set_logged_in_cookies(request, response, user)
        return response


class UpdateUserInfoView(generics.UpdateAPIView):
    serializer_class = UserInfoSerializer
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser)
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        self.perform_update(serializer)
        return Response({'code': 200, 'msg': '更新成功。'})


class ResetUserPasswordView(generics.UpdateAPIView):
    serializer_class = ResetPasswordSerializer

    def get_object(self):
        form = ResetPasswordForm(self.request.data)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)
        return form.instance

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        self.perform_update(serializer)
        redirect_url = reverse('account:login')
        return Response({
            'code': 200,
            'msg': '密码重置成功，马上登录。',
            'redirect_url': redirect_url
        })


class UpdateUserPasswordView(generics.UpdateAPIView):
    serializer_class = UpdatePasswordSerializer
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser)
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        self.perform_update(serializer)
        return Response({'code': 200, 'msg': '密码更新成功，请重新登录。'})


class UpdateUserAvatarView(generics.UpdateAPIView):
    serializer_class = UpdateUserAvatarSerializer
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser)
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user.profile

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        original_avatar_url = instance.avatar.url
        original_avatar_path = os.path.join(settings.ENV_ROOT, original_avatar_url.lstrip('/'))
        self.perform_update(serializer)

        # delete original avatar
        if original_avatar_path.split('/')[-1] != 'default_avatar.jpg':
            os.remove(original_avatar_path)

        return Response({'code': 200, 'msg': '更新头像成功。', 'src': serializer.instance.avatar.url})


class SendEmailToResetPassword(APIView):
    def post(self, request, *args, **kwargs):
        form = EmailToResetPasswordForm(request.data)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        verification_code = generate_verification_code()
        try:
            context = {
                'verification_code': verification_code
            }
            # composes activation email
            subject = '重置密码'
            template_path = 'emails/forget_password.html'
            default_from_address = settings.DEFAULT_FROM_EMAIL_DISPLAY
            send_html_mail(subject, template_path, context, default_from_address, [form.cleaned_data.get('email')])
        except Exception as ex:
            logger.error(ex)
            return Response(status=500, data={'code': 500, 'msg': '邮件发送失败，请稍后重试。'})

        # save verify code into request session
        request.session['verification_code'] = verification_code
        request.session.set_expiry(5 * 60)
        return Response({'code': 200, 'msg': '验证码已发送至邮箱，注意查收，若邮件未出现在收件箱，请留意垃圾箱。'})


class CheckEmailIsBind(APIView):
    def post(self, request, *args, **kwargs):
        form = CheckEmailIsBindForm(request.data)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        return Response({
            'code': 200,
            'msg': '可以绑定'
        })


class SendEmailToBindOrChangeEmail(APIView):
    def post(self, request, *args, **kwargs):
        form = GeneralEmailForm(request.data)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        verification_code = generate_verification_code()
        try:
            context = {
                'verification_code': verification_code
            }
            subject = '绑定/修改邮箱'
            template_path = 'emails/bind_or_change_email.html'
            default_from_address = settings.DEFAULT_FROM_EMAIL_DISPLAY
            send_html_mail(subject, template_path, context, default_from_address, [form.cleaned_data.get('email')])
        except Exception as ex:
            logger.error(ex)
            return Response(status=500, data={'code': 500, 'msg': '邮件发送失败，请稍后重试。'})

        # save verify code into request session
        request.session['verification_code'] = verification_code
        request.session.set_expiry(5 * 60)

        return Response({'code': 200, 'msg': '验证码已发送至邮箱，注意查收，若邮件未出现在收件箱，请留意垃圾箱。'})


class ChangeEmailView(generics.UpdateAPIView):
    serializer_class = ChangeEmailSerializer
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser)
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        self.perform_update(serializer)
        return Response({
            'code': 200,
            'msg': '邮箱修改成功。'
        })


class BindEmailView(generics.UpdateAPIView):
    serializer_class = BindEmailSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        self.perform_update(serializer)
        return Response({
            'code': 200,
            'msg': '邮箱绑定成功。'
        })


class UnbindingSocialLoginView(generics.DestroyAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        original_request_data = self.request.data.urlencode()
        new_request_data = QueryDict(original_request_data, mutable=True)
        new_request_data['user_id'] = self.request.user.id

        form = UnbindingSocialLoginForm(new_request_data)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        auth_type = form.cleaned_data.get('auth_type')
        user_id = form.cleaned_data.get('user_id')

        oauth_logins = OauthLogin.objects.using('read').filter(auth_type=auth_type, user_id=user_id)
        if not oauth_logins.exists():
            raise Http404
        return oauth_logins[0]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'code': 200,
            'msg': '解绑成功。'
        })
