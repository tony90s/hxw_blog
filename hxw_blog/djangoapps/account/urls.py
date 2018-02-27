from django.conf.urls import url
from account.views import (
    LoginView, RegisterView,
    logout_view,
    user_info,
    update_user_avatar,
    update_password,
    update_user_info,
    ResetPasswordView,
    send_email_to_reset_password,
    message_comments,
    user_unified_comment_info_pagination,
    message_praises,
    user_praises_info_pagination
)

from account.oauth_weibo import weibo_login, weibo_auth

urlpatterns = [
    url(r'^register/$', RegisterView.as_view(), name='register'),
    url(r'^login/$', LoginView.as_view(), name='login'),
    url(r'^logout/$',  logout_view, name='logout'),
    url(r'^info/$', user_info, name='user_info'),
    url(r'^avator/update/$', update_user_avatar, name='update_user_avatar'),
    url(r'^password/update/$', update_password, name='update_user_password'),
    url(r'^info/update/$', update_user_info, name='update_user_info'),
    url(r'^password/reset/$', ResetPasswordView.as_view(), name='reset_password'),
    url(r'^password/reset/send_email/$', send_email_to_reset_password, name='send_email_to_reset_password'),
    url(r'^message/comments$', message_comments, name='user_message_comments'),
    url(r'^message/comments/pagination$', user_unified_comment_info_pagination, name='user_message_comments_pagination'),
    url(r'^message/praises$', message_praises, name='user_message_praises'),
    url(r'^message/praises/pagination$', user_praises_info_pagination, name='user_message_praises_pagination')
]

urlpatterns += [
    url(r'^weibo/login$', weibo_login, name='social_weibo_login'),
    url(r'^weibo/login/done$', weibo_auth, name='social_weibo_login_done')
]
