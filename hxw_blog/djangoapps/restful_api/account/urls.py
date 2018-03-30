from django.conf.urls import url
from restful_api.account.views import (
    UpdateUserInfoView,
    UpdateUserPasswordView,
    UpdateUserAvatarView
)

urlpatterns = [
    url(r'^info/update$', UpdateUserInfoView.as_view(), name='update_user_info'),
    url(r'^password/update$', UpdateUserPasswordView.as_view(), name='update_user_password'),
    url(r'^avatar/update$', UpdateUserAvatarView.as_view(), name='update_user_avatar'),
]
