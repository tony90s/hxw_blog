import json
import requests
from urllib import request as urllib_request, parse

from django.contrib.auth.models import User
from django.core.files.base import ContentFile

from account.models import UserProfile, OauthLogin
from utils import generate_verification_code
from utils.file_handling import get_thumbnail


class OauthWeibo(object):
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_auth_url(self):
        authorize_url = 'https://api.weibo.com/oauth2/authorize'
        context = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code'
        }
        url_params = parse.urlencode(context)
        weibo_auth_url = '%s?%s' % (authorize_url, url_params)
        return weibo_auth_url

    def get_access_token(self, code):
        auth_url = 'https://api.weibo.com/oauth2/access_token'
        context = {
            'code': code,  # authorization_code
            'client_id': self.client_id,
            'client_secret':self.client_secret,
            'redirect_uri': self.redirect_uri,
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
                nick_name = user_info['screen_name'] if 'screen_name' in user_info else '微博用户{random_str}'.format(
                    random_str=generate_verification_code(3))
                gender = user_info['gender'] if 'gender' in user_info else UserProfile.GENDER.MALE

                avatar_img = None
                if 'avatar_large' in user_info:
                    avatar = user_info['avatar_large']
                elif 'profile_image_url' in user_info:
                    avatar = user_info['profile_image_url']
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
                oauth_login.auth_type = OauthLogin.TYPE.WEIBO
                oauth_login.oauth_id = uid
                oauth_login.user_id = user.id

        # update access token
        oauth_login.oauth_access_token = oauth_access_token
        oauth_login.oauth_expires = oauth_expires
        oauth_login.save(using='write')
        return user
