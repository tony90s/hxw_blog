from django.conf.urls import url
from restful_api.account.views import (
    RegisterView,
    LoginView,
    UpdateUserInfoView,
    ResetUserPasswordView,
    UpdateUserPasswordView,
    UpdateUserAvatarView,
    SendEmailToResetPassword,
    CheckEmailIsBind,
    SendEmailToBindOrChangeEmail,
    ChangeEmailView,
    BindEmailView,
    UnbindingSocialLoginView
)

urlpatterns = [
    url(r'^register$', RegisterView.as_view(), name='register'),
    url(r'^login$', LoginView.as_view(), name='login'),
    url(r'^info/update$', UpdateUserInfoView.as_view(), name='update_user_info'),
    url(r'^password/reset$', ResetUserPasswordView.as_view(), name='reset_user_password'),
    url(r'^password/update$', UpdateUserPasswordView.as_view(), name='update_user_password'),
    url(r'^avatar/update$', UpdateUserAvatarView.as_view(), name='update_user_avatar'),
    url(r'^password/reset/send_email$', SendEmailToResetPassword.as_view(), name='send_email_to_reset_password'),
    url(r'^email/check$', CheckEmailIsBind.as_view(), name='check_email_is_bind'),
    url(r'^email/bind_or_change/send_verification$', SendEmailToBindOrChangeEmail.as_view(),
        name='send_verification_to_bind_or_change_email'),
    url(r'^email/change$', ChangeEmailView.as_view(), name='change_email'),
    url(r'^email/bind$', BindEmailView.as_view(), name='bind_email'),
    url(r'^social/unbind$', UnbindingSocialLoginView.as_view(), name='unbinding_social_login')
]
