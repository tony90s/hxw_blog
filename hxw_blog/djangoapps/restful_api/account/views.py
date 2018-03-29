import re

from django.contrib.auth.models import User
from django.db.models import Q
from django.http import QueryDict

from rest_framework import generics, permissions
from rest_framework.response import Response

reg_username = re.compile('^[\w_\u4e00-\u9fa5]{2,32}$')


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
