from django.conf.urls import url
from account.views import (
    LoginView, RegisterView,
    logout_view,
    user_info,
    ResetPasswordView,
    message_comments,
    message_praises,
    weibo_login,
    weibo_auth,
    qq_login,
    qq_login_done,
    wechat_login,
    wechat_login_done,
    alipay_login,
    alipay_login_done
)

urlpatterns = [
    url(r'^register$', RegisterView.as_view(), name='register'),
    url(r'^login$', LoginView.as_view(), name='login'),
    url(r'^logout$', logout_view, name='logout'),
    url(r'^info$', user_info, name='user_info'),
    url(r'^password/reset$', ResetPasswordView.as_view(), name='reset_password'),
    url(r'^message/comments$', message_comments, name='user_message_comments'),
    url(r'^message/praises$', message_praises, name='user_message_praises')
]

urlpatterns += [
    url(r'^weibo/login$', weibo_login, name='social_weibo_login'),
    url(r'^weibo/login/done$', weibo_auth, name='social_weibo_login_done'),
    url(r'^qq/login$', qq_login, name='social_qq_login'),
    url(r'^qq/login/done$', qq_login_done, name='social_qq_login_done'),
    url(r'^wechat/login$', wechat_login, name='social_wechat_login'),
    url(r'^wechat/login/done$', wechat_login_done, name='social_wechat_login_done'),
    url(r'^alipay/login$', alipay_login, name='social_alipay_login'),
    url(r'^alipay/login/done$', alipay_login_done, name='social_alipay_login_done')
]
