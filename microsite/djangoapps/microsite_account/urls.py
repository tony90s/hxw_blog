from django.conf.urls import url
from account.views import (
    LoginView, RegisterView,
    logout_view,
    ResetPasswordView,
    user_unified_comment_info_pagination,
    weibo_login,
    weibo_auth,
    qq_login,
    qq_login_done,
    wechat_login,
    wechat_login_done,
    alipay_login,
    alipay_login_done
)
from microsite_account.views import (
    user_center,
    user_avatar_preview,
    user_messages
)

urlpatterns = [
    url(r'^register$', RegisterView.as_view(), name='register'),
    url(r'^login$', LoginView.as_view(), name='login'),
    url(r'^logout$', logout_view, name='logout'),
    url(r'^password/reset$', ResetPasswordView.as_view(), name='reset_password'),
    url(r'^center$', user_center, name='user_center'),
    url(r'^avatar$', user_avatar_preview, name='user_avatar'),
    url(r'^messages$', user_messages, name='user_messages'),
    url(r'^messages/comments/pagination$', user_unified_comment_info_pagination, name='user_message_comments_pagination'),
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
