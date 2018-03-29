from django.conf.urls import url
from account.views import (
    LoginView, RegisterView,
    logout_view,
    user_info,
    update_user_avatar,
    update_password,
    ResetPasswordView,
    send_email_to_reset_password,
    check_email_is_bind,
    send_email_to_bind_or_change_email,
    change_email,
    bind_email,
    message_comments,
    user_unified_comment_info_pagination,
    message_praises,
    user_praises_info_pagination,
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
    url(r'^avator/update$', update_user_avatar, name='update_user_avatar'),
    url(r'^password/update$', update_password, name='update_user_password'),
    url(r'^password/reset$', ResetPasswordView.as_view(), name='reset_password'),
    url(r'^password/reset/send_email$', send_email_to_reset_password, name='send_email_to_reset_password'),
    url(r'^email/check$', check_email_is_bind, name='check_email_is_bind'),
    url(r'^email/bind_or_change/send_verification$', send_email_to_bind_or_change_email,
        name='send_verification_to_bind_or_change_email'),
    url(r'^email/bind$', bind_email, name='bind_email'),
    url(r'^email/change$', change_email, name='change_email'),
    url(r'^message/comments$', message_comments, name='user_message_comments'),
    url(r'^message/comments/pagination$', user_unified_comment_info_pagination, name='user_message_comments_pagination'),
    url(r'^message/praises$', message_praises, name='user_message_praises'),
    url(r'^message/praises/pagination$', user_praises_info_pagination, name='user_message_praises_pagination')
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
