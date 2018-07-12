import json
import requests
from urllib import request as urllib_request, parse

from django.contrib.auth.models import User
from django.core.files.base import ContentFile

from account.models import UserProfile, OauthLogin
from utils import generate_verification_code
from utils.file_handling import get_thumbnail


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
                nickname = user_info['nickname'] if 'nickname' in user_info else '微信用户{random_str}'.format(
                    random_str=generate_verification_code(3))
                if 'sex' in user_info:
                    gender = UserProfile.GENDER.MALE if user_info['sex'] == 1 else UserProfile.GENDER.FEMALE
                else:
                    gender = UserProfile.GENDER.MALE

                avatar_img = None
                avatar = user_info['headimgurl'] if 'headimgurl' in user_info else None
                if avatar:
                    req = requests.get(avatar)
                    file_content = ContentFile(req.content)
                    avatar_img = get_thumbnail(file_content, 100, 100)

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

    def bind(self, user):
        oauth_access_token = self.access_token['access_token']
        oauth_expires = self.access_token['expires_in']
        uid = self.access_token['openid']

        oauth_login = OauthLogin()
        oauth_login.auth_type = OauthLogin.TYPE.WECHAT
        oauth_login.oauth_id = uid
        oauth_login.user_id = user.id
        oauth_login.oauth_access_token = oauth_access_token
        oauth_login.oauth_expires = oauth_expires
        oauth_login.save(using='write')
        return oauth_login
