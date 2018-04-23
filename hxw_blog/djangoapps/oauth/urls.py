"""
OAuth2 wrapper urls
"""
from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from . import views


urlpatterns = [
    url(r'^authorize$', csrf_exempt(views.AuthorizationView.as_view()), name='authorize'),
    url(r'^access_token$', csrf_exempt(views.AccessTokenView.as_view()), name='access_token')
]
