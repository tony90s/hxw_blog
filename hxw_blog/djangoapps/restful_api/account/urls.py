from django.conf.urls import url
from restful_api.account.views import (
    UpdateUserInfoView,
)

urlpatterns = [
    url(r'^info/update$', UpdateUserInfoView.as_view(), name='update_user_info'),
]
