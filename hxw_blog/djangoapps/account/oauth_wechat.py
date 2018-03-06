import logging
import json
import requests
from urllib import request as urllib_request, parse

from django.conf import settings
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth import logout, authenticate, login
from django.core.files.base import ContentFile

from account.models import UserProfile, OauthLogin
from account.cookies import set_logged_in_cookies
from utils import generate_verification_code
from utils.file_handling import get_thumbnail

logger = logging.getLogger('account.oauth_weibo')


class OauthWechat(object):
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_auth_url(self):
        authorize_url = 'https://open.weixin.qq.com/connect/qrconnect'
        context = {
            'appid': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'snsapi_login',
            'state': 1
        }
        url_params = parse.urlencode(context)
        wechat_auth_url = '%s?%s' % (authorize_url, url_params)
        return wechat_auth_url

    def get_access_token(self, code):
        get_access_token_url = 'https://api.weixin.qq.com/sns/oauth2/access_token'
        context = {
            'code': code,  # authorization_code
            'appid': self.client_id,
            'secret':self.client_secret,
            'grant_type': 'authorization_code'
        }
        resp = requests.get(get_access_token_url, context)
        data = json.loads(resp.text)
        self.access_token = data
        return data

    def get_wechat_info(self):
        user_info_url = 'https://api.weixin.qq.com/sns/userinfo'
        context = {
            'access_token': self.access_token['access_token'],
            'openid': self.access_token['openid']
        }
        resp = requests.get(user_info_url, context)
        data = json.loads(resp.text)
        return data

    def get_blog_user(self):
        access_token = self.access_token
        oauth_access_token = access_token['access_token']
        oauth_expires = access_token['expires_in']
        uid = access_token['openid']

        oauth_logins = OauthLogin.objects.using('read').filter(auth_type=OauthLogin.TYPE.WECHAT,
                                                               oauth_access_token=oauth_access_token)
        if oauth_logins.exists():
            oauth_login = oauth_logins[0]
            user_id = oauth_login.user_id
            user = User.objects.using('read').get(id=user_id)
        else:
            oauth_logins = OauthLogin.objects.using('read').filter(auth_type=OauthLogin.TYPE.WECHAT,
                                                                   oauth_id=uid)
            if oauth_logins.exists():
                oauth_login = oauth_logins[0]
                user_id = oauth_login.user_id
                user = User.objects.using('read').get(id=user_id)
            else:
                user_info = self.get_wechat_info()
                nickname = user_info['nickname']
                gender = 'm' if user_info['sex'] == 1 else 'f'

                avatar_img = None
                avatar = user_info['headimgurl']
                if avatar:
                    req = requests.get(avatar)
                    file_content = ContentFile(req.content)
                    avatar_img = get_thumbnail(file_content, 100, 100)[0]

                result_name = nickname
                all_user = User.objects.using('read').all()
                email_users = all_user.filter(username=nickname)
                if email_users.exists():
                    rand_str = generate_verification_code()
                    result_name = nickname + rand_str
                    while True:
                        if not all_user.filter(username=result_name).exists():
                            break
                        rand_str = generate_verification_code()
                        result_name = nickname + rand_str

                user = User()
                user.username = result_name
                user.set_password('888888')
                user.save(using='write')
                user_profile = UserProfile()
                user_profile.user = user
                user_profile.gender = gender
                if avatar_img is not None:
                    user_profile.avatar = avatar_img
                user_profile.save(using='write')

                oauth_login = OauthLogin()
                oauth_login.auth_type = OauthLogin.TYPE.WECHAT
                oauth_login.oauth_id = uid
                oauth_login.user_id = user.id

        # update access token
        oauth_login.oauth_access_token = oauth_access_token
        oauth_login.oauth_expires = oauth_expires
        oauth_login.save(using='write')
        return user


def get_referer_url(request):
    referer_url = request.META.get('HTTP_REFERER', reverse('index'))
    host = request.META['HTTP_HOST']
    if referer_url.startswith('http') and host not in referer_url:
        referer_url = reverse('index')
    return referer_url


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
    if request.user.is_authenticated():
        return HttpResponseRedirect(redirect_url)

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
