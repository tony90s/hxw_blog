import logging
import json
import requests

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth import logout, authenticate, login

from account.models import UserProfile, OauthLogin
from utils import generate_verification_code


WEIBO_APP_KEY = settings.WEIBO_APP_KEY
WEIBO_APP_SECRET = settings.WEIBO_APP_SECRET
WEIBO_LOGIN_REDIRECT_URI = settings.WEIBO_LOGIN_REDIRECT_URI
HOST = 'www.loveiters.com'

logger = logging.getLogger('account.oauth_weibo')


def get_referer_url(request):
    referer_url = request.META.get('HTTP_REFERER', reverse('index'))
    host = request.META['HTTP_HOST']
    if referer_url.startswith('http') and host not in referer_url:
        referer_url = reverse('index')
    return referer_url


def weibo_login(request):
    authorize_url = 'https://api.weibo.com/oauth2/authorize'
    redirect_uri = 'http://' + HOST + WEIBO_LOGIN_REDIRECT_URI
    context = {
        'client_id': WEIBO_APP_KEY,
        'redirect_uri': redirect_uri,
        'response_type': 'code'
    }
    url_params = "&".join("{}={}".format(k, v) for k, v in context.items())
    weibo_auth_url = '%s?%s' % (authorize_url, url_params)
    logger.info(weibo_auth_url)
    request.session['redirect_uri'] = get_referer_url(request)
    return HttpResponseRedirect(weibo_auth_url)


def get_access_token(request, code):
    auth_url = 'https://api.weibo.com/oauth2/access_token'
    redirect_uri = 'http://' + HOST + WEIBO_LOGIN_REDIRECT_URI
    context = {
        'code': code,  # authorization_code
        'client_id': WEIBO_APP_KEY,
        'client_secret': WEIBO_APP_SECRET,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    req = requests.post(auth_url, data=context)
    data = json.loads(req.text)

    return data


def get_user_info(access_info):
    user_info_url = 'https://api.weibo.com/2/users/show.json'
    context = {'access_token': access_info['access_token'], 'uid': access_info['uid']}
    resp = requests.get(user_info_url, context)
    data = json.loads(resp.text)
    return data


def get_blog_user(request, access_token):
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
            user_info = get_user_info(access_token)
            nick_name = user_info['screen_name']
            avatar = user_info['avatar_large']
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
            user_profile.save(using='write')

            oauth_login = OauthLogin()
            oauth_login.auth_type = OauthLogin.TYPE.WEIBO
            oauth_login.oauth_id = uid
            oauth_login.user_id = user.id

    login(request, user)
    # update access token
    oauth_login.oauth_access_token = oauth_access_token
    oauth_login.oauth_expires = oauth_expires
    oauth_login.save(using='write')
    return user


def weibo_auth(request):
    redirect_url = reverse('index')
    if 'blog_user' in request.session:
        return HttpResponseRedirect(redirect_url)

    if 'error' in request.GET or 'code' not in request.GET:
        return HttpResponseRedirect(redirect_url)

    code = request.GET['code']
    try:
        access_token = get_access_token(request, code)
        blog_user = get_blog_user(request, access_token)
        request.session['blog_user'] = blog_user
        request.session.set_expiry(604800)
    except Exception as e:
        logger.error(e)

    if 'state' in request.GET:
        redirect_url = request.GET['state']

    return HttpResponse('good')
