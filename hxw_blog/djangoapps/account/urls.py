from django.conf.urls import url
from account.views import (
    LoginView, RegisterView,
    logout_view,
    user_info,
    update_user_avatar,
    update_password,
    update_user_info,
    ResetPasswordView,
    send_email_to_reset_password
)

urlpatterns = [
    url(r'^register/$', RegisterView.as_view(), name='register'),
    url(r'^login/$', LoginView.as_view(), name='login'),
    url(r'^logout/$',  logout_view, name='logout'),
    url(r'^info/$', user_info, name='user_info'),
    url(r'^avator/update/$', update_user_avatar, name='update_user_avatar'),
    url(r'^password/update/$', update_password, name='update_user_password'),
    url(r'^info/update/$', update_user_info, name='update_user_info'),
    url(r'^password/reset/$', ResetPasswordView.as_view(), name='reset_password'),
    url(r'^password/reset/send_email/$', send_email_to_reset_password, name='send_email_to_reset_password')
]
