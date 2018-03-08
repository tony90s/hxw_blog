from base64 import b64encode, b64decode
from datetime import datetime
import logging
import json
import os
import requests
from urllib import request as urllib_request, parse

from django.conf import settings
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth import logout, authenticate, login
from django.core.files.base import ContentFile

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.exceptions import InvalidSignature

from account.models import UserProfile, OauthLogin
from account.cookies import set_logged_in_cookies
from utils import generate_verification_code
from utils.file_handling import get_thumbnail


PUBLIC_KEY_PATH = os.path.join(settings.ENV_ROOT, 'rsa_key/public_key.pem')
PRIVATE_KEY_PATH = os.path.join(settings.ENV_ROOT, 'rsa_key/private_key.pem')

logger = logging.getLogger('account.oauth_alipay')


class OauthAlipay(object):
    def __init__(self, alipay_url, appid, app_private_key, format, charset, alipay_public_key, sign_type, redirect_uri):
        self.alipay_url = alipay_url
        self.appid = appid
        self.app_private_key = app_private_key
        self.format = format
        self.charset = charset
        self.alipay_public_key = alipay_public_key
        self.sign_type = sign_type
        self.redirect_uri = redirect_uri

    def get_auth_url(self):
        authorize_url = 'https://openauth.alipay.com/oauth2/publicAppAuthorize.htm'
        context = {
            'app_id': self.appid,
            'redirect_uri': self.redirect_uri,
            'scope': 'auth_user',

        }
        url_params = parse.urlencode(context)
        alipay_auth_url = '%s?%s' % (authorize_url, url_params)
        return alipay_auth_url

    def ordered_params(self, params):
        complex_keys = []
        for key, value in params.items():
            if isinstance(value, dict):
                complex_keys.append(key)
        for key in complex_keys:
            params[key] = json.dumps(params[key], sort_keys=True).replace(" ", "")
        return sorted([(k, v) for k, v in params.items()])

    def generate_signature(self, unsigned_data):
        with open(self.app_private_key, "rb") as private_key_file:
            private_key = serialization.load_pem_private_key(
                private_key_file.read(),
                password=None,
                backend=default_backend()
            )
        signature = private_key.sign(
            unsigned_data,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return b64encode(signature)

    def verify_signature(self, signature, data):
        with open(self.alipay_public_key, "rb") as public_key_file:
            public_key = serialization.load_pem_public_key(
                public_key_file.read(),
                backend=default_backend()
            )

        verify_ok = False
        try:
            public_key.verify(
                b64decode(signature),
                data,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
        except InvalidSignature:
            logger.error('invalid signature!')
        else:
            verify_ok = True
        return verify_ok

    def get_access_token(self, auth_code):
        auth_url = self.alipay_url
        now = datetime.now()
        context = {
            'app_id': self.appid,
            'method': 'alipay.system.oauth.token',
            'charset': self.charset,
            'sign_type': self.sign_type,
            'version': settings.ALIPAY_VERSION,
            'timestamp': now.strftime("%Y-%m-%d %H:%M:%S"),
            'grant_type': 'authorization_code',
            'code': auth_code
        }
        ordered_params = self.ordered_params(context)
        unsigned_data = "&".join("{}={}".format(k, v) for k, v in ordered_params).encode('utf-8')
        sign = self.generate_signature(unsigned_data)
        context['sign'] = sign
        """
        params = parse.urlencode(context).encode('utf-8')
        req = urllib_request.Request(auth_url, data=params)
        page = urllib_request.urlopen(req).read()
        """
        logger.error(json.dumps(context))
        req = requests.get(auth_url, context)
        logger.error(req.text)
        data = json.loads(req.text)
        self.access_token = data['alipay_system_oauth_token_response']
        return self.access_token

    def get_alipay_info(self):
        auth_url = self.alipay_url
        now = datetime.now()
        context = {
            'app_id': self.appid,
            'method': 'alipay.user.info.share',
            'charset': self.charset,
            'sign_type': self.sign_type,
            'version': settings.ALIPAY_VERSION,
            'timestamp': now.strftime("%Y-%m-%d %H:%M:%S"),
            'auth_token': self.access_token['access_token']
        }
        ordered_params = self.ordered_params(context)
        unsigned_data = "&".join("{}={}".format(k, v) for k, v in ordered_params).encode('utf-8')
        sign = self.generate_signature(unsigned_data)
        context['sign'] = sign
        """
        params = parse.urlencode(context)
        req = urllib_request.Request(auth_url, data=params)
        page = urllib_request.urlopen(req).read()
        """
        logger.error(json.dumps(context))
        req = requests.get(auth_url, context)
        logger.error(req.text)
        data = json.loads(req.text)
        return data['alipay_user_info_share_response']

    def get_blog_user(self):
        access_token = self.access_token
        oauth_access_token = access_token['access_token']
        oauth_expires = access_token['expires_in']
        uid = access_token['user_id']

        oauth_logins = OauthLogin.objects.using('read').filter(auth_type=OauthLogin.TYPE.ALIPAY,
                                                               oauth_access_token=oauth_access_token)
        if oauth_logins.exists():
            oauth_login = oauth_logins[0]
            user_id = oauth_login.user_id
            user = User.objects.using('read').get(id=user_id)
        else:
            oauth_logins = OauthLogin.objects.using('read').filter(auth_type=OauthLogin.TYPE.ALIPAY,
                                                                   oauth_id=uid)
            if oauth_logins.exists():
                oauth_login = oauth_logins[0]
                user_id = oauth_login.user_id
                user = User.objects.using('read').get(id=user_id)
            else:
                user_info = self.get_alipay_info()
                nick_name = user_info['nick_name']
                gender = 'm' if user_info['gender'] == 'M' else 'f'

                avatar_img = None
                avatar = user_info['avatar']
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
                oauth_login.auth_type = OauthLogin.TYPE.ALIPAY
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
    if request.user.is_authenticated():
        return HttpResponseRedirect(redirect_url)

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
