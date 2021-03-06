import logging
import os
import re

from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.views import View

from account.cookies import set_logged_in_cookies, delete_logged_in_cookies
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

    # Clear the cookie when logout
    delete_logged_in_cookies(response)
    return response


@login_required
def user_info(request):
    template_name = 'account/user_info.html'
    return render(request, template_name)


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
    template_name = 'account/message_comments.html'
    return render(request, template_name)


@login_required
def message_praises(request):
    template_name = 'account/message_praises.html'
    return render(request, template_name)


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
