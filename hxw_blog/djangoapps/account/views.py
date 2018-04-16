from itertools import chain
import logging
import os
import re
import time

from django.conf import settings
from django.db.models import Q
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest, Http404, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.views import View

from rest_framework import serializers

from account.cookies import set_logged_in_cookies, delete_logged_in_cookies
from article.models import (
    Article,
    Comment,
    CommentReply,
    Praise,
    get_user_article_comments,
    get_user_comments,
    get_user_be_praised
)
from account.forms import UnifiedCommentListForm
from account.oauth2.oauth_weibo import OauthWeibo
from account.oauth2.oauth_qq import OauthQQ
from account.oauth2.oauth_wechat import OauthWechat
from account.oauth2.oauth_alipay import OauthAlipay


PUBLIC_KEY_PATH = os.path.join(settings.ENV_ROOT, 'rsa_key/public_key.pem')
PRIVATE_KEY_PATH = os.path.join(settings.ENV_ROOT, 'rsa_key/private_key.pem')

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
        next = request.GET.get("next", reverse('index'))
        context = {
            "next": next
        }

        return render(request, self.template_name, context)


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
        next = request.GET.get("next", reverse('index'))
        context = {
            "next": next
        }

        return render(request, self.template_name, context)


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
    email = request.user.email
    email_display = email
    if email and len(email.split('@')[0]) >= 3:
        email_display = email[0] + '***' + email[(email.index('@') - 1):]

    context = {
        'email_display': email_display
    }

    template_name = 'account/user_info.html'
    return render(request, template_name, context=context)


class ResetPasswordView(View):
    """View for reset password."""
    template_name = 'account/forget_password.html'

    def get(self, request, *args, **kwargs):
        """
        Display the reset password web page
        :param request:
        :return:
        """
        return render(request, self.template_name)


@login_required
def message_comments(request):
    page_size = settings.PAGINATORS['SMALL_PAGE_SIZE']
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

    unified_comment_list = list(chain(comments, comment_replies))
    unified_comment_list.sort(
        key=lambda comment: time.mktime(time.strptime(comment.unified_reply_at, '%Y-%m-%d %H:%M:%S')),
        reverse=True)
    query_comments_list = unified_comment_list[:page_size]
    query_comments_info = [comment.get_unified_comment_info() for comment in query_comments_list]
    context = {
        'unified_comment_info_list': query_comments_info,
        'comment_type': comment_type,
        'page_size': page_size,
        'not_viewed_comment_count': not_viewed_comment_count,
        'not_viewed_praises_count': not_viewed_praises_count,
        'has_next': int(len(unified_comment_list) > page_size)
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
    page_size = settings.PAGINATORS['SMALL_PAGE_SIZE']

    form = UnifiedCommentListForm(request.GET)
    if not form.is_valid():
        raise serializers.ValidationError(form.errors)

    comment_type = form.cleaned_data.get('comment_type')
    user_id = form.cleaned_data.get('user_id')
    page_index = form.cleaned_data.get('page_index')

    if comment_type == 0:
        comments = get_user_article_comments(user_id)
        comment_replies = CommentReply.objects.using('read').filter(Q(receiver_id=user_id)).order_by('-id')
    else:
        comments = get_user_comments(user_id)
        comment_replies = CommentReply.objects.using('read').filter(Q(replier_id=user_id)).order_by('-id')

    unified_comment_list = list(chain(comments, comment_replies))
    unified_comment_list.sort(
        key=lambda comment: time.mktime(time.strptime(comment.unified_reply_at, '%Y-%m-%d %H:%M:%S')),
        reverse=True)
    query_comments_list = unified_comment_list[page_size * (page_index - 1):page_size * page_index]
    query_comments_info = [comment.get_unified_comment_info() for comment in query_comments_list]
    context = {
        'code': 200,
        'msg': '查询成功',
        'data': query_comments_info,
        'has_next': int(len(unified_comment_list) > (page_index * page_size))
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
    page_size = settings.PAGINATORS['SMALL_PAGE_SIZE']
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


def weibo_login(request):
    redirect_url = request.GET.get('redirect_url', reverse('index'))
    oauth_weibo = OauthWeibo(settings.WEIBO_APP_KEY, settings.WEIBO_APP_SECRET, settings.WEIBO_LOGIN_REDIRECT_URI)
    weibo_auth_url = oauth_weibo.get_auth_url()
    logger.info(weibo_auth_url)
    request.session['redirect_url'] = redirect_url
    return HttpResponseRedirect(weibo_auth_url)


def weibo_auth(request):
    redirect_url = reverse('index')
    if 'redirect_url' in request.session:
        redirect_url = request.session['redirect_url']

    if 'error' in request.GET or 'code' not in request.GET:
        return HttpResponseRedirect(redirect_url)

    code = request.GET.get('code')
    oauth_weibo = OauthWeibo(settings.WEIBO_APP_KEY, settings.WEIBO_APP_SECRET, settings.WEIBO_LOGIN_REDIRECT_URI)

    try:
        access_token = oauth_weibo.get_access_token(code)
        user = oauth_weibo.get_blog_user()

        login(request, user)
        request.session.set_expiry(604800)
        response = HttpResponseRedirect(redirect_url)
        response = set_logged_in_cookies(request, response, user)
        return response
    except Exception as e:
        logger.error(e)
        return HttpResponseRedirect(redirect_url)


def qq_login(request):
    redirect_url = request.GET.get('redirect_url', reverse('index'))
    oauth_qq = OauthQQ(settings.QQ_APP_KEY, settings.QQ_APP_SECRET, settings.QQ_LOGIN_REDIRECT_URI)
    qq_auth_url = oauth_qq.get_auth_url()
    logger.info(qq_auth_url)
    request.session['redirect_url'] = redirect_url
    return HttpResponseRedirect(qq_auth_url)


def qq_login_done(request):
    redirect_url = reverse('index')
    if 'redirect_url' in request.session:
        redirect_url = request.session['redirect_url']

    if 'error' in request.GET or 'code' not in request.GET:
        return HttpResponseRedirect(redirect_url)

    code = request.GET.get('code')
    oauth_qq = OauthQQ(settings.QQ_APP_KEY, settings.QQ_APP_SECRET, settings.QQ_LOGIN_REDIRECT_URI)

    try:
        access_token = oauth_qq.get_access_token(code)
        open_id = oauth_qq.get_openid()
        user = oauth_qq.get_blog_user()

        login(request, user)
        request.session.set_expiry(604800)
        response = HttpResponseRedirect(redirect_url)
        response = set_logged_in_cookies(request, response, user)
        return response
    except Exception as e:
        logger.error(e)
        return HttpResponseRedirect(redirect_url)


def wechat_login(request):
    redirect_url = request.GET.get('redirect_url', reverse('index'))
    oauth_wechat = OauthWechat(settings.WECHAT_APP_KEY, settings.WECHAT_APP_SECRET, settings.WECHAT_LOGIN_REDIRECT_URI)
    wechat_auth_url = oauth_wechat.get_auth_url()
    logger.info(wechat_auth_url)
    request.session['redirect_url'] = redirect_url
    return HttpResponseRedirect(wechat_auth_url)


def wechat_login_done(request):
    redirect_url = reverse('index')
    if 'redirect_url' in request.session:
        redirect_url = request.session['redirect_url']

    if 'error' in request.GET or 'code' not in request.GET:
        return HttpResponseRedirect(redirect_url)

    code = request.GET.get('code')
    oauth_wechat = OauthWechat(settings.WECHAT_APP_KEY, settings.WECHAT_APP_SECRET, settings.WECHAT_LOGIN_REDIRECT_URI)

    try:
        access_token = oauth_wechat.get_access_token(code)
        user = oauth_wechat.get_blog_user()

        login(request, user)
        request.session.set_expiry(604800)
        response = HttpResponseRedirect(redirect_url)
        response = set_logged_in_cookies(request, response, user)
        return response
    except Exception as e:
        logger.error(e)
        return HttpResponseRedirect(redirect_url)


def alipay_login(request):
    redirect_url = request.GET.get('redirect_url', reverse('index'))
    oauth_alipay = OauthAlipay(
        settings.ALIPAY_URL,
        settings.ALIPAY_APPID,
        PRIVATE_KEY_PATH,
        settings.ALIPAY_FORMAT,
        settings.ALIPAY_CHARSET,
        PUBLIC_KEY_PATH,
        settings.ALIPAY_SIGN_TYPE,
        settings.ALIPAY_LOGIN_REDIRECT_URI
    )
    alipay_auth_url = oauth_alipay.get_auth_url()
    logger.info(alipay_auth_url)
    request.session['redirect_url'] = redirect_url
    return HttpResponseRedirect(alipay_auth_url)


def alipay_login_done(request):
    redirect_url = reverse('index')
    if 'redirect_url' in request.session:
        redirect_url = request.session['redirect_url']

    if 'error' in request.GET or 'auth_code' not in request.GET:
        return HttpResponseRedirect(redirect_url)

    auth_code = request.GET.get('auth_code')
    oauth_alipay = OauthAlipay(
        settings.ALIPAY_URL,
        settings.ALIPAY_APPID,
        PRIVATE_KEY_PATH,
        settings.ALIPAY_FORMAT,
        settings.ALIPAY_CHARSET,
        PUBLIC_KEY_PATH,
        settings.ALIPAY_SIGN_TYPE,
        settings.ALIPAY_LOGIN_REDIRECT_URI
    )

    try:
        access_token = oauth_alipay.get_access_token(auth_code)
        user = oauth_alipay.get_blog_user()

        login(request, user)
        request.session.set_expiry(604800)
        response = HttpResponseRedirect(redirect_url)
        response = set_logged_in_cookies(request, response, user)
        return response
    except Exception as e:
        logger.error(e)
        return HttpResponseRedirect(redirect_url)
