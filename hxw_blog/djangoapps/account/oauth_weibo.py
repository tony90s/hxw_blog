import logging
import json
import requests

from django.conf import settings
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth import logout, authenticate, login

from account.models import UserProfile, OauthLogin
from account.cookies import set_logged_in_cookies
from utils import generate_verification_code

logger = logging.getLogger('account.oauth_weibo')

HTTP_HEAD = 'https://' if settings.HTTPS else 'http://'


class OauthWeibo(object):
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_auth_url(self):
        authorize_url = 'https://api.weibo.com/oauth2/authorize'
        redirect_uri = HTTP_HEAD + settings.HOST + self.redirect_uri
        context = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code'
        }
        url_params = "&".join("{}={}".format(k, v) for k, v in context.items())
        weibo_auth_url = '%s?%s' % (authorize_url, url_params)
        return weibo_auth_url

    def get_access_token(self, code):
        auth_url = 'https://api.weibo.com/oauth2/access_token'
        redirect_uri = HTTP_HEAD + settings.HOST + self.redirect_uri
        context = {
            'code': code,  # authorization_code
            'client_id': self.client_id,
            'client_secret':self.client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        req = requests.post(auth_url, data=context)
        data = json.loads(req.text)
        self.access_token = data
        return data

    def get_weibo_info(self):
        user_info_url = 'https://api.weibo.com/2/users/show.json'
        context = {
            'access_token': self.access_token['access_token'],
            'uid': self.access_token['uid']
        }
        resp = requests.get(user_info_url, context)
        data = json.loads(resp.text)
        return data

    def get_blog_user(self):
        access_token = self.access_token
        oauth_access_token = access_token['access_token']
        oauth_expires = access_token['expires_in']
        uid = access_token['uid']

        oauth_logins = OauthLogin.objects.using('read').filter(auth_type=OauthLogin.TYPE.WEIBO,
                                                               oauth_access_token=oauth_access_token)
        if oauth_logins.exists():
            oauth_login = oauth_logins[0]
            user_id = oauth_login.user_id
            user = User.objects.using('read').get(id=user_id)
        else:
            oauth_logins = OauthLogin.objects.using('read').filter(auth_type=OauthLogin.TYPE.WEIBO,
                                                                   oauth_id=uid)
            if oauth_logins.exists():
                oauth_login = oauth_logins[0]
                user_id = oauth_login.user_id
                user = User.objects.using('read').get(id=user_id)
            else:
                user_info = self.get_weibo_info()
                nick_name = user_info['screen_name']

                avatar = user_info['avatar_large']
                response = requests.get(avatar)
                img = response.content
                gender = user_info['gender']

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
                user.set_password(generate_verification_code())
                user.save(using='write')
                user_profile = UserProfile()
                user_profile.user = user
                user_profile.gender = gender
                user_profile.avatar = img
                user_profile.save(using='write')

                oauth_login = OauthLogin()
                oauth_login.auth_type = OauthLogin.TYPE.WEIBO
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


def weibo_login(request):
    oauth_weibo = OauthWeibo(settings.WEIBO_APP_KEY, settings.WEIBO_APP_SECRET, settings.WEIBO_LOGIN_REDIRECT_URI)
    weibo_auth_url = oauth_weibo.get_auth_url()
    logger.info(weibo_auth_url)
    request.session['redirect_uri'] = get_referer_url(request)
    return HttpResponseRedirect(weibo_auth_url)


def weibo_auth(request):
    redirect_url = reverse('index')
    if 'blog_user' in request.session:
        return HttpResponseRedirect(redirect_url)

    if 'error' in request.GET or 'code' not in request.GET:
        return HttpResponseRedirect(redirect_url)

    code = request.GET['code']
    oauth_weibo = OauthWeibo(settings.WEIBO_APP_KEY, settings.WEIBO_APP_SECRET, settings.WEIBO_LOGIN_REDIRECT_URI)

    try:
        access_token = oauth_weibo.get_access_token(code)
        user = oauth_weibo.get_blog_user()

        login(request, user)
        request.session['blog_user'] = user.id
        request.session.set_expiry(604800)
        response = HttpResponseRedirect(redirect_url)
        response = set_logged_in_cookies(request, response, user)
        return response
    except Exception as e:
        logger.error(e)
        return HttpResponseRedirect(redirect_url)
