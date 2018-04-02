from django.conf.urls import url
from restful_api.account.views import (
    UpdateUserInfoView,
    UpdateUserPasswordView,
    UpdateUserAvatarView,
    SendEmailToResetPassword,
    CheckEmailIsBind,
    SendEmailToBindOrChangeEmail,
    ChangeEmailView,
    BindEmailView
)

urlpatterns = [
    url(r'^info/update$', UpdateUserInfoView.as_view(), name='update_user_info'),
    url(r'^password/update$', UpdateUserPasswordView.as_view(), name='update_user_password'),
    url(r'^avatar/update$', UpdateUserAvatarView.as_view(), name='update_user_avatar'),
    url(r'^password/reset/send_email$', SendEmailToResetPassword.as_view(), name='send_email_to_reset_password'),
    url(r'^email/check$', CheckEmailIsBind.as_view(), name='check_email_is_bind'),
    url(r'^email/bind_or_change/send_verification$', SendEmailToBindOrChangeEmail.as_view(),
        name='send_verification_to_bind_or_change_email'),
    url(r'^email/change$', ChangeEmailView.as_view(), name='change_email'),
    url(r'^email/bind$', BindEmailView.as_view(), name='bind_email')
]
