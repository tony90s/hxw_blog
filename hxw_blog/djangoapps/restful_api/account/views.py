from copy import deepcopy
import logging
import os
import re

from django.conf import settings
from django.http import Http404, QueryDict
from django.contrib.auth.models import User

from rest_framework.views import APIView
from rest_framework import generics, permissions
from rest_framework.response import Response

from restful_api.account.serializers import (
    UserInfoSerializer,
    UpdatePasswordSerializer,
    ChangeEmailSerializer,
    BindEmailSerializer,
    UnbindingSocialLoginSerializer,
)
from account.models import OauthLogin
from utils.file_handling import get_thumbnail
from utils import generate_verification_code
from utils.html_email_utils import send_html_mail

reg_username = re.compile('^[\w_\u4e00-\u9fa5]{2,32}$')
reg_password = re.compile('^[\.\w@_-]{6,32}$')
reg_email = re.compile('^[\w-]+(\.[\w-]+)*@[\w-]+(\.[\w-]+)+$')

logger = logging.getLogger('api.account')


class UpdateUserInfoView(generics.UpdateAPIView):
    serializer_class = UserInfoSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data.get('username')
        if username:
            if not reg_username.match(username):
                return Response({'code': 400, 'msg': '昵称格式有误，请重新输入。'})
        self.perform_update(serializer)
        return Response({'code': 200, 'msg': '更新成功。'})


class UpdateUserPasswordView(generics.UpdateAPIView):
    serializer_class = UpdatePasswordSerializer
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


class UpdateUserAvatarView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def clean(self):
        avatar = self.request.FILES.get('avatar')
        if avatar is None:
            return Response({'code': 400, 'msg': '请先选择图片。'})
        if re.match(r'image', avatar.content_type) is None:
            return Response({'code': 400, 'msg': '请选择正确的图片!'})
        img_max_size = 1024 * 5
        if avatar.size / 1024 > img_max_size:
            return Response({'code': 400, 'msg': '图片过大，请重新选择!'})
        self.cleaned_data = {'avatar': avatar}
        return None

    def perform_update(self, user_profile):
        thumbnail, error = get_thumbnail(self.cleaned_data.get('avatar'))
        if thumbnail is None:
            return Response({'code': 500, 'msg': '头像上传失败，请稍后重试。'})
        user_profile.avatar = thumbnail
        user_profile.save(using='write')

    def post(self, request, *args, **kwargs):
        response = self.clean()
        if response is not None:
            return response

        user = request.user
        user_profile = user.profile
        original_avatar_url = user_profile.avatar.url
        original_avatar_path = os.path.join(settings.ENV_ROOT, original_avatar_url.lstrip('/'))

        self.perform_update(user_profile)
        # delete original avatar
        if original_avatar_path.split('/')[-1] != 'default_avatar.jpg':
            os.remove(original_avatar_path)

        return Response({'code': 200, 'msg': '更新头像成功。', 'src': user_profile.avatar.url})


class SendEmailToResetPassword(APIView):
    def clean(self):
        email = self.request.POST.get('email', '')
        if not email:
            return Response({'code': 400, 'msg': '请填入邮箱。'})
        if not reg_email.match(email):
            return Response({'code': 400, 'msg': '邮箱格式有误，请重新输入。'})

        users = User.objects.using('read').filter(email=email)
        if not users.exists():
            return Response({'code': 404, 'msg': '该邮箱尚未注册。'})
        self.cleaned_data = {'email': email}
        return None

    def post(self, request, *args, **kwargs):
        response = self.clean()
        if response is not None:
            return response
        verification_code = generate_verification_code()
        try:
            context = {
                'verification_code': verification_code
            }
            # composes activation email
            subject = '重置密码'
            template_path = 'emails/forget_password.html'
            default_from_address = settings.DEFAULT_FROM_EMAIL_DISPLAY
            send_html_mail(subject, template_path, context, default_from_address, [self.cleaned_data.get('email')])
        except Exception as ex:
            logger.error(ex)
            return Response({'code': 500, 'msg': '邮件发送失败，请稍后重试。'})

        # save verify code into request session
        request.session['verification_code'] = verification_code
        request.session.set_expiry(5 * 60)
        return Response({'code': 200, 'msg': '验证码已发送至邮箱，注意查收，若邮件未出现在收件箱，请留意垃圾箱。'})


class CheckEmailIsBind(APIView):
    def clean(self):
        email = self.request.POST.get('email', '')
        if not email:
            return Response({'code': 400, 'msg': '请输入邮箱。'})
        if not reg_email.match(email):
            return Response({'code': 400, 'msg': '邮箱格式有误，请重新输入。'})

        users = User.objects.using('read').filter(email=email)
        if users.exists():
            return Response({'code': 403, 'msg': '该邮箱已被绑定，换一个试试。'})
        self.cleaned_data = {'email': email}
        return None

    def post(self, request, *args, **kwargs):
        response = self.clean()
        if response is not None:
            return response

        verification_code = generate_verification_code()
        try:
            context = {
                'verification_code': verification_code
            }
            subject = '绑定/修改邮箱'
            template_path = 'emails/bind_or_change_email.html'
            default_from_address = settings.DEFAULT_FROM_EMAIL_DISPLAY
            send_html_mail(subject, template_path, context, default_from_address, [self.cleaned_data.get('email')])
        except Exception as ex:
            logger.error(ex)
            return Response({'code': 500, 'msg': '邮件发送失败，请稍后重试。'})

        # save verify code into request session
        request.session['verification_code'] = verification_code
        request.session.set_expiry(5 * 60)

        return Response({'code': 200, 'msg': '验证码已发送至邮箱，注意查收，若邮件未出现在收件箱，请留意垃圾箱。'})


class SendEmailToBindOrChangeEmail(APIView):
    def clean(self):
        email = self.request.POST.get('email', '')
        if not email:
            return Response({'code': 400, 'msg': '请填入邮箱。'})
        if not reg_email.match(email):
            return Response({'code': 400, 'msg': '邮箱格式有误，请重新输入。'})
        self.cleaned_data = {'email': email}
        return None

    def post(self, request, *args, **kwargs):
        response = self.clean()
        if response is not None:
            return response

        verification_code = generate_verification_code()
        try:
            context = {
                'verification_code': verification_code
            }
            subject = '绑定/修改邮箱'
            template_path = 'emails/bind_or_change_email.html'
            default_from_address = settings.DEFAULT_FROM_EMAIL_DISPLAY
            send_html_mail(subject, template_path, context, default_from_address, [self.cleaned_data.get('email')])
        except Exception as ex:
            logger.error(ex)
            return Response({'code': 500, 'msg': '邮件发送失败，请稍后重试。'})

        # save verify code into request session
        request.session['verification_code'] = verification_code
        request.session.set_expiry(5 * 60)

        return Response({'code': 200, 'msg': '验证码已发送至邮箱，注意查收，若邮件未出现在收件箱，请留意垃圾箱。'})


class ChangeEmailView(generics.UpdateAPIView):
    serializer_class = ChangeEmailSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        users = User.objects.using('read').filter(email=serializer.validated_data.get('email'))
        if users.exists():
            return Response({'code': 403, 'msg': '该邮箱已被绑定，换一个试试。'})

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

        if request.user.email:
            return Response({'code': 400, 'msg': '您已绑定邮箱，无需重复绑定。'})
        users = User.objects.using('read').filter(email=serializer.validated_data.get('email'))
        if users.exists():
            return Response({'code': 403, 'msg': '该邮箱已被绑定，换一个试试。'})
        self.perform_update(serializer)
        return Response({
            'code': 200,
            'msg': '邮箱绑定成功。'
        })


class UnbindingSocialLoginView(generics.DestroyAPIView):
    serializer_class = UnbindingSocialLoginSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        auth_type = self.serializer_class.validated_data.get('auth_type')
        user_id = self.serializer_class.validated_data.get('user_id')

        oauth_logins = OauthLogin.objects.using('read').filter(auth_type=auth_type, user_id=user_id)
        if not oauth_logins.exists():
            raise Http404
        return oauth_logins[0]

    def destroy(self, request, *args, **kwargs):
        original_request_data = request.data.urlencode()
        new_request_data = QueryDict(original_request_data, mutable=True)
        new_request_data['user_id'] = request.user.id
        serializer = self.get_serializer(data=new_request_data)
        serializer.is_valid(raise_exception=True)

        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'code': 200,
            'msg': '解绑成功。'
        })
