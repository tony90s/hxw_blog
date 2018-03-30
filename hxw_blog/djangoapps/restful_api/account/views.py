import os
import re

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import QueryDict

from rest_framework.views import APIView
from rest_framework import generics, permissions
from rest_framework.response import Response

from utils.file_handling import get_thumbnail

reg_username = re.compile('^[\w_\u4e00-\u9fa5]{2,32}$')
reg_password = re.compile('^[\.\w@_-]{6,32}$')


class UpdateUserInfoView(generics.UpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def clean(self):
        user = self.request.user
        query_data = QueryDict(self.request.body)
        username = query_data.get('username', '')
        gender = query_data.get('gender', '')
        bio = query_data.get('bio', '')

        self.cleaned_data = dict()
        if username:
            if not reg_username.match(username):
                return Response({'code': 400, 'msg': '昵称格式有误，请重新输入。'})
            users = User.objects.using('read').filter(username=username)
            if username != user.username and users.exists():
                return Response({'code': 400, 'msg': '昵称已被使用，换一个试试。'})
            self.cleaned_data['username'] = username
        if gender:
            if gender not in ['m', 'f']:
                return Response({'code': 400, 'msg': '性别参数有误，请重试。'})
            self.cleaned_data['gender'] = gender
        if bio:
            if len(bio) > 120:
                return Response({'code': 400, 'msg': '个人简介字数至多为120，请重试。'})
            self.cleaned_data['bio'] = bio
        return None

    def perform_update(self, user):
        user_profile = user.profile
        user.username = self.cleaned_data.get('username', user.username)
        user_profile.gender = self.cleaned_data.get('gender', user_profile.gender)
        user_profile.bio = self.cleaned_data.get('bio', user_profile.bio)
        user.save(using='write')
        user_profile.save(using='write')

    def update(self, request, *args, **kwargs):
        response = self.clean()
        if response is not None:
            return response

        user = request.user
        self.perform_update(user)
        return Response({'code': 200, 'msg': '更新成功。'})


class UpdateUserPasswordView(generics.UpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def clean(self):
        user = self.request.user
        query_data = QueryDict(self.request.body)
        password = query_data.get('password', '')
        new_password = query_data.get('new_password', '')
        confirm_password = query_data.get('confirm_password', '')

        if not password or not new_password or not confirm_password:
            return Response({'code': 400, 'msg': '请完善表单。'})
        if not reg_password.match(new_password):
            return Response({'code': 400, 'msg': '新密码格式有误，请重新输入。'})
        if new_password != confirm_password:
            return Response({'code': 400, 'msg': '密码不一致，请重新输入。'})
        if not user.check_password(password):
            return Response({'code': 400, 'msg': '原密码错误，请重新输入。'})
        self.cleaned_data = query_data
        return None

    def perform_update(self, user):
        user.set_password(self.cleaned_data.get('new_password'))
        user.save()

    def update(self, request, *args, **kwargs):
        response = self.clean()
        if response is not None:
            return response

        user = request.user
        self.perform_update(user)
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
