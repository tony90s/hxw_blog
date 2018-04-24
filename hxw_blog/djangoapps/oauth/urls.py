"""
OAuth2 wrapper urls
"""
from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from . import views
from . import exchange as auth_exchange

urlpatterns = [
    url(r'^authorize$', csrf_exempt(views.AuthorizationView.as_view()), name='authorize'),
    url(r'^access_token$', csrf_exempt(views.AccessTokenView.as_view()), name='access_token'),
    url(r'^revoke_token$', csrf_exempt(views.RevokeTokenView.as_view()), name="revoke_token")
]

urlpatterns += [
    url(r'^login$', auth_exchange.LoginWithAccessTokenView.as_view(), name="login_with_access_token")
]
