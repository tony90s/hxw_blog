import datetime
import logging
import os
import re
import string
import random

from django.conf import settings
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.views import View

from account.cookies import set_logged_in_cookies, delete_logged_in_cookies
from account.models import UserProfile
from utils import generate_verification_code
from utils.file_handling import get_thumbnail
from utils.html_email_utils import send_html_mail

logger = logging.getLogger('account.views')


class RegisterView(View):
    """
     Display view for account register.

    Arguments:
     - request      : HTTP request

    Returns:
     - RedirectResponse
    """
    template_name = 'account/register.html'

    def get(self, request, *args, **kwargs):
        """
        Display the login web page
        :param request:
        :return:
        """
        next = request.GET.get("next", "")
        context = {
            "next": next
        }

        return render_to_response(self.template_name, context)

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        username = request.POST.get('username', '')
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not username:
            return JsonResponse({
                'code': 400,
                'msg': '请输入昵称'
            })
        if not email:
            return JsonResponse({
                'code': 400,
                'msg': '请输入Email'
            })
        if not password:
            return JsonResponse({
                'code': 400,
                'msg': '请输入密码'
            })
        if not confirm_password:
            return JsonResponse({
                'code': 400,
                'msg': '请输入确认密码'
            })

        if password != confirm_password:
            return JsonResponse({
                'code': 400,
                'msg': '密码输入不一致'
            })
        users = User.objects.using('read').filter(username=username)
        if users.exists():
            return JsonResponse({
                'code': 400,
                'msg': '昵称已被使用，请重新输入'
            })
        users = User.objects.using('read').filter(email=email)
        if users.exists():
            return JsonResponse({
                'code': 400,
                'msg': 'Email已注册，请登录'
            })

        user = User.objects.create_user(username, email, password)
        user_profile = UserProfile()
        user_profile.user = user
        user_profile.save(using='write')
        login(request, user)

        # send email to notice users when register successfully

        redirect_url = request.POST.get('redirect_url', '').replace('#', '')
        if redirect_url == '':
            redirect_url = reverse('index')
        return JsonResponse({
            'code': 200,
            'msg': '注册成功',
            'redirect_url': redirect_url
        })


class LoginView(View):
    """
     Display view for account login.

    Arguments:
     - request      : HTTP request

    Returns:
     - RedirectResponse
    """
    template_name = 'account/login.html'

    def get(self, request, *args, **kwargs):
        """
        Display the login web page
        :param request:
        :return:
        """
        next = request.GET.get("next", "")
        context = {
            "next": next
        }

        return render_to_response(self.template_name, context)

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        account = request.POST.get('account', '')
        password = request.POST.get('password', '')

        if not account:
            return JsonResponse({
                'code': 400,
                'msg': '请输入帐号'
            })
        if not password:
            return JsonResponse({
                'code': 400,
                'msg': '请输入密码'
            })

        users = User.objects.using('read').filter(email=account)
        if not users.exists():
            return JsonResponse({
                'code': 404,
                'msg': '帐号尚未注册'
            })

        user = authenticate(username=users[0].get_username(), password=password)
        if user is None:
            return JsonResponse({
                'code': 400,
                'msg': '密码错误，请重新输入'
            })

        login(request, user)

        if request.POST.get('remember') == 'true':
            request.session.set_expiry(604800)
        else:
            request.session.set_expiry(0)

        redirect_url = request.POST.get('redirect_url', '').replace('#', '')
        if redirect_url == '':
            redirect_url = reverse('index')

        response = JsonResponse({'code': '200', 'msg': '登录成功', 'redirect_url': redirect_url})
        response = set_logged_in_cookies(request, response, user)
        return response


@csrf_exempt
def logout_view(request):
    """
    Logs out user and redirects.
    """
    target = reverse('index')
    logout(request)
    response = redirect(target)

    # Clear the cookie used by the edx.org marketing site
    delete_logged_in_cookies(response)

    return response


@login_required
def user_info(request):
    template_name = 'account/user_info.html'
    user = request.user
    context = {
        'user': user
    }

    return render_to_response(template_name, context)


@login_required
@csrf_exempt
def update_user_avatar(request):
    user = request.user
    user_profile = user.profile
    original_avatar_url = user_profile.avatar.url
    original_avatar_path = os.path.join(settings.ENV_ROOT, original_avatar_url.lstrip('/'))

    avatar = request.FILES.get('avatar')
    if avatar is None:
        return JsonResponse({'code': 400, 'msg': '请先选择图片'})

    thumbnail, error = get_thumbnail(avatar)
    if thumbnail is None:
        logger.error(error)
        return JsonResponse({'code': 500, 'msg': '头像上传失败，请稍后重试。'})

    user_profile.avatar = thumbnail
    user_profile.save(using='write')
    if original_avatar_path.split('/')[-1] != 'default_avatar.jpg':
        os.remove(original_avatar_path)

    return JsonResponse({'code': 200, 'msg': '更新头像成功', 'src': user_profile.avatar.url})


@login_required
@csrf_exempt
def update_password(request):
    user = request.user

    password = request.POST.get('password', '')
    new_password = request.POST.get('new_password', '')
    confirm_password = request.POST.get('confirm_password', '')

    if not password or not new_password or not confirm_password:
        return JsonResponse({'code': 400, 'msg': '请完善表单'})

    if new_password != confirm_password:
        return JsonResponse({'code': 400, 'msg': '密码不一致，请重新输入'})

    if not user.check_password(password):
        return JsonResponse({'code': 400, 'msg': '原密码错误，请重新输入'})

    user.set_password(new_password)
    user.save()
    return JsonResponse({'code': 200, 'msg': '密码更新成功，请重新登录。'})


@login_required
@csrf_exempt
def update_user_info(request):
    user = request.user
    user_profile = user.profile

    username = request.POST.get('username', '')
    gender = request.POST.get('gender', '')
    bio = request.POST.get('bio', '')

    if username:
        users = User.objects.using('read').filter(username=username)
        if username != user.username and users.exists():
            return JsonResponse({'code': 400, 'msg': '昵称已被使用，换一个试试。'})
        user.username = username
    if gender:
        if gender not in ['m', 'f']:
            return JsonResponse({'code': 400, 'msg': '性别参数有误，请重试。'})
        user_profile.gender = gender
    if bio:
        user_profile.bio = bio

    user.save(using='write')
    user_profile.save(using='write')

    return JsonResponse({'code': 200, 'msg': '更新成功。'})


@csrf_exempt
def send_email_to_reset_password(request):
    email = request.POST.get('email', '')
    if not email:
        return JsonResponse({'code': 400, 'msg': '请填入邮箱。'})

    users = User.objects.using('read').filter(email=email)
    if not users.exists():
        return JsonResponse({'code': 404, 'msg': '该邮箱尚未注册。'})

    verification_code = generate_verification_code()
    try:
        context = {
            'verification_code': verification_code
        }
        # composes activation email
        subject = '重置密码'
        template_path = 'emails/forget_password.html'
        from_address_name = settings.DEFAULT_FROM_EMAIL_DISPLAY
        send_html_mail(subject, template_path, context, from_address_name, [email])
    except Exception as ex:
        logger.error(ex)
        return JsonResponse({'code': 500, 'msg': '邮件发送失败，请稍后重试。'})

    # save verify code into request session
    request.session['verification_code'] = verification_code
    request.session.set_expiry(5 * 60)

    return JsonResponse({'code': 200, 'msg': '邮件发送成功，注意查收，若邮件未出现在收件箱，请留意垃圾箱。'})


class ResetPasswordView(View):
    """View for reset password."""
    template_name = 'account/forget_password.html'

    def get(self, request, *args, **kwargs):
        """
        Display the reset password web page
        :param request:
        :return:
        """
        return render_to_response(self.template_name)

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        email = request.POST.get('email', '')
        verification_code = request.POST.get('verification_code', '')
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not email:
            return JsonResponse({'code': 400, 'msg': '请输入邮箱。'})
        if not verification_code:
            return JsonResponse({'code': 400, 'msg': '请输入验证码。'})
        if not password or not confirm_password:
            return JsonResponse({'code': 400, 'msg': '请输入密码。'})

        users = User.objects.using('read').filter(email=email)
        if not users.exists():
            return JsonResponse({'code': 404, 'msg': '该邮箱尚未注册。'})

        verification_code_in_session = request.session.get('verification_code', '')
        if not verification_code_in_session:
            return JsonResponse({'code': 301, 'msg': '验证码已过期，请重新获取。'})
        if verification_code != verification_code_in_session:
            return JsonResponse({'code': 400, 'msg': '验证码错误，请重新输入。'})

        if password != confirm_password:
            return JsonResponse({
                'code': 400,
                'msg': '密码输入不一致'
            })

        # set new password
        user = users[0]
        user.set_password(password)
        user.save(using='write')

        redirect_url = reverse('account:login')
        return JsonResponse({
            'code': 200,
            'msg': '密码重置成功，马上登录。',
            'redirect_url': redirect_url
        })
