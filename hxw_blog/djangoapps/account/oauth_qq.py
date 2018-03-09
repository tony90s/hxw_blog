import re
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

logger = logging.getLogger('account.oauth_qq')


class OauthQQ(object):
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_auth_url(self):
        authorize_url = 'https://graph.qq.com/oauth2.0/authorize'
        context = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'get_user_info',
            'state': 1
        }
        url_params = parse.urlencode(context)
        qq_auth_url = '%s?%s' % (authorize_url, url_params)
        return qq_auth_url

    def get_access_token(self, code):
        get_access_token_url = 'https://graph.qq.com/oauth2.0/token'
        context = {
            'code': code,  # authorization_code
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code'
        }
        params = parse.urlencode(context).encode('utf-8')
        req = urllib_request.Request(get_access_token_url, data=params)
        page = urllib_request.urlopen(req).read().decode('utf-8')
        re_search_result = re.search('{.+}', page)
        if re_search_result is not None:
            data = json.loads(re_search_result.group(0))
        else:
            result = parse.parse_qs(page)
            data = dict([(k, v[0]) for k, v in result.items()])
        self.access_token = data
        return data

    def get_openid(self):
        get_openid_url = 'https://graph.qq.com/oauth2.0/me'
        context = {
            'access_token': self.access_token['access_token']
        }
        params = parse.urlencode(context).encode('utf-8')
        req = urllib_request.Request(get_openid_url, data=params)
        page = urllib_request.urlopen(req).read().decode('utf-8')
        re_search_result = re.search('{.+}', page)
        if re_search_result is not None:
            data = json.loads(re_search_result.group(0))
        else:
            result = parse.parse_qs(page)
            data = dict([(k, v[0]) for k, v in result.items()])
        openid = data['openid']
        self.openid = openid
        return openid

    def get_qq_info(self):
        user_info_url = 'https://graph.qq.com/user/get_user_info'
        context = {
            'access_token': self.access_token['access_token'],
            'oauth_consumer_key': self.client_id,
            'openid': self.openid
        }
        resp = requests.get(user_info_url, context)
        data = json.loads(resp.text)
        return data

    def get_blog_user(self):
        oauth_access_token = self.access_token['access_token']
        oauth_expires = int(self.access_token['expires_in'])

        oauth_logins = OauthLogin.objects.using('read').filter(auth_type=OauthLogin.TYPE.QQ,
                                                               oauth_access_token=oauth_access_token)
        if oauth_logins.exists():
            oauth_login = oauth_logins[0]
            user_id = oauth_login.user_id
            user = User.objects.using('read').get(id=user_id)
        else:
            uid = self.get_openid()
            oauth_logins = OauthLogin.objects.using('read').filter(auth_type=OauthLogin.TYPE.QQ,
                                                                   oauth_id=uid)
            if oauth_logins.exists():
                oauth_login = oauth_logins[0]
                user_id = oauth_login.user_id
                user = User.objects.using('read').get(id=user_id)
            else:
                user_info = self.get_qq_info()
                nick_name = user_info['nickname'] if 'nickname' in user_info else 'QQ用户{random_str}'.format(
                    random_str=generate_verification_code(3))
                if 'gender' in user_info:
                    gender = UserProfile.GENDER.MALE if user_info['gender'] == '男' else UserProfile.GENDER.FEMALE
                else:
                    gender = UserProfile.GENDER.MALE

                avatar_img = None
                if 'figureurl_qq_2' in user_info:
                    avatar = user_info['figureurl_qq_2']
                elif 'figureurl_qq_1' in user_info:
                    avatar = user_info['figureurl_qq_1']
                else:
                    avatar = None
                if avatar:
                    req = requests.get(avatar)
                    file_content = ContentFile(req.content)
                    avatar_img = get_thumbnail(file_content, 100, 100)[0]

                result_name = nick_name
                all_user = User.objects.using('read').all()
                email_users = all_user.filter(username=nick_name)
                if email_users.exists():
                    rand_str = generate_verification_code()
                    result_name = nick_name + rand_str
                    while True:
                        if not all_user.filter(username=result_name).exists():
                            break
                        rand_str = generate_verification_code()
                        result_name = nick_name + rand_str

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
                oauth_login.auth_type = OauthLogin.TYPE.QQ
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
