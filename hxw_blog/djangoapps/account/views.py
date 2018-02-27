import datetime
import time
import logging
import os
import re
import string
import random

from django.conf import settings
from django.db.models import Q
from django.shortcuts import render, render_to_response
from django.shortcuts import redirect
from django.http import JsonResponse, HttpResponseBadRequest, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.views import View
# from django.views.decorators.cache import cache_page

from account.cookies import set_logged_in_cookies, delete_logged_in_cookies
from account.models import UserProfile
from article.models import (
    Article,
    Comment,
    CommentReply,
    Praise,
    get_user_article_comments,
    get_user_comments,
    get_user_be_praised
)
from utils import generate_verification_code
from utils.file_handling import get_thumbnail
from utils.html_email_utils import send_html_mail

reg_username = re.compile('^[\w_\u4e00-\u9fa5]{2,32}$')
reg_email = re.compile('^[\w-]+(\.[\w-]+)*@[\w-]+(\.[\w-]+)+$')
reg_password = re.compile('^[\.\w@_-]{6,32}$')
reg_number = re.compile('^\d+$')
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
        if not reg_username.match(username):
            return JsonResponse({
                'code': 400,
                'msg': '昵称格式有误，请重新输入'
            })

        if not email:
            return JsonResponse({
                'code': 400,
                'msg': '请输入Email'
            })
        if not reg_email.match(email):
            return JsonResponse({
                'code': 400,
                'msg': '邮箱格式有误，请重新输入'
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
        if not reg_password.match(password):
            return JsonResponse({
                'code': 400,
                'msg': '密码格式有误，请重新输入'
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
        response = JsonResponse({
            'code': 200,
            'msg': '注册成功',
            'redirect_url': redirect_url
        })
        response = set_logged_in_cookies(request, response, user)
        return response


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
    return render(request, template_name)


@login_required
@csrf_exempt
def update_user_avatar(request):
    user = request.user
    user_profile = user.profile
    original_avatar_url = user_profile.avatar.url
    original_avatar_path = os.path.join(settings.ENV_ROOT, original_avatar_url.lstrip('/'))

    avatar = request.FILES.get('avatar')
    if avatar is None:
        return JsonResponse({'code': 400, 'msg': '请先选择图片。'})

    thumbnail, error = get_thumbnail(avatar)
    if thumbnail is None:
        logger.error(error)
        return JsonResponse({'code': 500, 'msg': '头像上传失败，请稍后重试。'})

    user_profile.avatar = thumbnail
    user_profile.save(using='write')
    if original_avatar_path.split('/')[-1] != 'default_avatar.jpg':
        os.remove(original_avatar_path)

    return JsonResponse({'code': 200, 'msg': '更新头像成功。', 'src': user_profile.avatar.url})


@login_required
@csrf_exempt
def update_password(request):
    user = request.user

    password = request.POST.get('password', '')
    new_password = request.POST.get('new_password', '')
    confirm_password = request.POST.get('confirm_password', '')

    if not password or not new_password or not confirm_password:
        return JsonResponse({'code': 400, 'msg': '请完善表单。'})

    if not reg_password.match(new_password):
        return JsonResponse({'code': 400, 'msg': '新密码格式有误，请重新输入。'})
    if new_password != confirm_password:
        return JsonResponse({'code': 400, 'msg': '密码不一致，请重新输入。'})

    if not user.check_password(password):
        return JsonResponse({'code': 400, 'msg': '原密码错误，请重新输入。'})

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
        if not reg_username.match(username):
            return JsonResponse({'code': 400, 'msg': '昵称格式有误，请重新输入。'})
        users = User.objects.using('read').filter(username=username)
        if username != user.username and users.exists():
            return JsonResponse({'code': 400, 'msg': '昵称已被使用，换一个试试。'})
        user.username = username
    if gender:
        if gender not in ['m', 'f']:
            return JsonResponse({'code': 400, 'msg': '性别参数有误，请重试。'})
        user_profile.gender = gender
    if bio:
        if len(bio) > 120:
            return JsonResponse({'code': 400, 'msg': '个人简介字数至多为120，请重试。'})
        user_profile.bio = bio

    user.save(using='write')
    user_profile.save(using='write')

    return JsonResponse({'code': 200, 'msg': '更新成功。'})


@csrf_exempt
def send_email_to_reset_password(request):
    email = request.POST.get('email', '')
    if not email:
        return JsonResponse({'code': 400, 'msg': '请填入邮箱。'})
    if not reg_email.match(email):
        return JsonResponse({'code': 400, 'msg': '邮箱格式有误，请重新输入。'})

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
        if not reg_email.match(email):
            return JsonResponse({'code': 400, 'msg': '邮箱格式有误，请重新输入。'})

        if not verification_code:
            return JsonResponse({'code': 400, 'msg': '请输入验证码。'})

        if not password or not confirm_password:
            return JsonResponse({'code': 400, 'msg': '请输入密码。'})
        if not reg_password.match(password):
            return JsonResponse({'code': 400, 'msg': '密码格式有误，请重新输入。'})

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
                'msg': '密码输入不一致。'
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


@login_required
def message_comments(request):
    page_size = settings.DEFAULT_PAGE_SIZE
    template_name = 'account/message_comments.html'
    user = request.user

    comment_type = request.GET.get('type', '0')     # 0 received comments  1 sent comments
    if not reg_number.match(comment_type):
        return HttpResponseBadRequest('参数有误。')
    comment_type = int(comment_type)
    if comment_type not in [0, 1]:
        raise Http404

    comments = get_user_article_comments(user.id)
    comment_replies = CommentReply.objects.using('read').filter(Q(receiver_id=user.id)).order_by('-id')
    not_viewed_comment_count = comments.filter(is_viewed=0).count() + comment_replies.filter(is_viewed=0).count()
    praises = get_user_be_praised(user.id)
    not_viewed_praises_count = praises.filter(is_viewed=0).count()
    if comment_type == 1:
        comments = get_user_comments(user.id)
        comment_replies = CommentReply.objects.using('read').filter(Q(replier_id=user.id)).order_by('-id')
    comments_info_list = [comment.get_unified_comment_info() for comment in comments]
    comment_replies_info_list = [comment_reply.get_unified_comment_info() for comment_reply in comment_replies]
    unified_comment_info_list = comments_info_list + comment_replies_info_list
    unified_comment_info_list.sort(
        key=lambda comment_info: time.mktime(time.strptime(comment_info['reply_at'], '%Y-%m-%d %H:%M:%S')),
        reverse=True)
    context = {
        'unified_comment_info_list': unified_comment_info_list[:page_size],
        'comment_type': comment_type,
        'page_size': page_size,
        'not_viewed_comment_count': not_viewed_comment_count,
        'not_viewed_praises_count': not_viewed_praises_count,
        'has_next': int(len(unified_comment_info_list) > page_size)
    }
    Comment._Comment__user_cache = dict()
    Comment._Comment__article_info_cache = dict()
    CommentReply._CommentReply__user_cache = dict()
    CommentReply._CommentReply__article_info_cache = dict()
    Praise._Praise__user_cache = dict()
    Praise._Praise__article_info_cache = dict()
    return render(request, template_name, context)


@require_http_methods(['GET'])
def user_unified_comment_info_pagination(request):
    page_size = settings.DEFAULT_PAGE_SIZE
    user_id = request.GET.get('user_id')
    comment_type = request.GET.get('comment_type', '0')   # 0 received comments  1 sent comments
    page_index = request.GET.get('page_index')

    if not user_id or not page_index:
        return JsonResponse({'code': 400, 'msg': '参数缺失。'})

    if not reg_number.match(user_id):
        return JsonResponse({'code': 400, 'msg': '参数有误。'})
    user_id = int(user_id)
    if user_id <= 0:
        return JsonResponse({'code': 400, 'msg': '参数有误。'})

    if not reg_number.match(comment_type):
        return JsonResponse({'code': 400, 'msg': '参数有误。'})
    comment_type = int(comment_type)
    if comment_type not in [0, 1]:
        return JsonResponse({'code': 400, 'msg': '参数有误。'})

    if not reg_number.match(page_index):
        return JsonResponse({'code': 400, 'msg': '参数有误。'})
    page_index = int(page_index)
    if page_index <= 0:
        return JsonResponse({'code': 400, 'msg': '参数有误。'})

    if comment_type == 0:
        comments = get_user_article_comments(user_id)
        comment_replies = CommentReply.objects.using('read').filter(Q(receiver_id=user_id)).order_by('-id')
    else:
        comments = get_user_comments(user_id)
        comment_replies = CommentReply.objects.using('read').filter(Q(replier_id=user_id)).order_by('-id')
    comments_info_list = [comment.get_unified_comment_info() for comment in comments]
    comment_replies_info_list = [comment_reply.get_unified_comment_info() for comment_reply in comment_replies]
    unified_comment_info_list = comments_info_list + comment_replies_info_list
    unified_comment_info_list.sort(
        key=lambda comment_info: time.mktime(time.strptime(comment_info['reply_at'], '%Y-%m-%d %H:%M:%S')),
        reverse=True)
    query_comments_info = unified_comment_info_list[page_size * (page_index - 1):page_size * page_index]
    context = {
        'code': 200,
        'msg': '查询成功',
        'data': query_comments_info,
        'has_next': int(len(unified_comment_info_list) > (page_index * page_size))
    }
    Comment._Comment__user_cache = dict()
    Comment._Comment__article_info_cache = dict()
    CommentReply._CommentReply__user_cache = dict()
    CommentReply._CommentReply__article_info_cache = dict()
    Praise._Praise__user_cache = dict()
    Praise._Praise__article_info_cache = dict()
    return JsonResponse(context)


@login_required
def message_praises(request):
    page_size = settings.DEFAULT_PAGE_SIZE
    template_name = 'account/message_praises.html'
    user = request.user

    all_praises = get_user_be_praised(user.id)
    not_viewed_praises_count = all_praises.filter(is_viewed=0).count()
    praises = all_praises[:page_size]
    praises_info = [praise.get_praise_info() for praise in praises]

    comments = get_user_article_comments(user.id)
    comment_replies = CommentReply.objects.using('read').filter(Q(receiver_id=user.id)).order_by('-id')
    not_viewed_comment_count = comments.filter(is_viewed=0).count() + comment_replies.filter(is_viewed=0).count()

    context = {
        'praises': praises_info,
        'page_size': page_size,
        'not_viewed_praises_count': not_viewed_praises_count,
        'not_viewed_comment_count': not_viewed_comment_count,
        'has_next': int(len(all_praises) > page_size)

    }
    Comment._Comment__user_cache = dict()
    Comment._Comment__article_info_cache = dict()
    CommentReply._CommentReply__user_cache = dict()
    CommentReply._CommentReply__article_info_cache = dict()
    Praise._Praise__user_cache = dict()
    Praise._Praise__article_info_cache = dict()

    return render(request, template_name, context)


@require_http_methods(['GET'])
def user_praises_info_pagination(request):
    page_size = settings.DEFAULT_PAGE_SIZE
    user_id = request.GET.get('user_id')
    page_index = request.GET.get('page_index')

    if not user_id or not page_index:
        return JsonResponse({'code': 400, 'msg': '参数缺失。'})

    if not reg_number.match(user_id):
        return JsonResponse({'code': 400, 'msg': '参数有误。'})
    user_id = int(user_id)
    if user_id <= 0:
        return JsonResponse({'code': 400, 'msg': '参数有误。'})

    if not reg_number.match(page_index):
        return JsonResponse({'code': 400, 'msg': '参数有误。'})
    page_index = int(page_index)
    if page_index <= 0:
        return JsonResponse({'code': 400, 'msg': '参数有误。'})

    praises = get_user_be_praised(user_id)
    praises_info = [praise.get_praise_info() for praise in praises[page_size * (page_index - 1):page_size * page_index]]

    context = {
        'code': 200,
        'msg': '查询成功',
        'data': praises_info,
        'has_next': int(len(praises) > (page_index * page_size))
    }
    Comment._Comment__user_cache = dict()
    Comment._Comment__article_info_cache = dict()
    CommentReply._CommentReply__user_cache = dict()
    CommentReply._CommentReply__article_info_cache = dict()
    Praise._Praise__user_cache = dict()
    Praise._Praise__article_info_cache = dict()
    return JsonResponse(context)
