"""
Views that dispatch processing of OAuth requests to django-oauth2-provider or
django-oauth-toolkit as appropriate.
"""
import json
import logging
from time import time
import jwt
from oauth2_provider import models as dot_models, views as dot_views  # django-oauth-toolkit

from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils.functional import cached_property
from django.views.generic import View

from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from . import adapter
from . import exchange as auth_exchange_views

log = logging.getLogger("access_token")


class _DispatchingView(View):
    """
    Base class that route views to the appropriate provider view.  The default
    behavior routes based on client_id, but this can be overridden by redefining
    `select_backend()` if particular views need different behavior.
    """
    # pylint: disable=no-member

    dot_adapter = adapter.DOTAdapter()

    def get_adapter(self, request):
        """
        Returns the appropriate adapter based on the OAuth client linked to the request.
        """
        if dot_models.Application.objects.filter(client_id=self._get_client_id(request)).exists():
            return self.dot_adapter
        else:
            raise KeyError('Failed to dispatch view. Invalid client id')

    def dispatch(self, request, *args, **kwargs):
        """
        Dispatch the request to the selected backend's view.
        """
        backend = self.select_backend(request)
        view = self.get_view_for_backend(backend)
        return view(request, *args, **kwargs)

    def select_backend(self, request):
        """
        Given a request that specifies an oauth `client_id`, return the adapter
        for the appropriate OAuth handling library.  If the client_id is found
        in a django-oauth-toolkit (DOT) Application, use the DOT adapter,
        otherwise use the django-oauth-provider (DOP) adapter, and allow the
        calls to fail normally if the client does not exist.
        """
        return self.get_adapter(request).backend

    def get_view_for_backend(self, backend):
        """
        Return the appropriate view from the requested backend.
        """
        if backend == self.dot_adapter.backend:
            return self.dot_view.as_view()
        else:
            raise KeyError('Failed to dispatch view. Invalid backend {}'.format(backend))

    def _get_client_id(self, request):
        """
        Return the client_id from the provided request
        """
        if request.method == 'GET':
            return request.GET.get('client_id')
        else:
            return request.POST.get('client_id')


class AccessTokenView(_DispatchingView):
    """
    Handle access token requests.
    """
    dot_view = dot_views.TokenView

    @cached_property
    def claim_handlers(self):
        """ Returns a dictionary mapping scopes to methods that will add claims to the JWT payload. """

        return {
            'email': self._attach_email_claim,
            'profile': self._attach_profile_claim
        }

    def dispatch(self, request, *args, **kwargs):
        if request.method.lower() != 'post':
            return JsonResponse({
                'error': 'invalid_request',
                'error_description': 'Only POST requests allowed.',
            }, status=405)

        try:
            response = super(AccessTokenView, self).dispatch(request, *args, **kwargs)
        except KeyError as e:
            return JsonResponse({
                'error': 'invalid client id',
                'error_description': str(e).strip("'")
            }, status=400)

        if response.status_code == 200 and request.POST.get('token_type', '').lower() == 'jwt':
            expires_in, scopes, user = self._decompose_access_token_response(request, response)

            content = {
                'access_token': self._generate_jwt(user, scopes, expires_in),
                'expires_in': expires_in,
                'token_type': 'JWT',
                'scope': ' '.join(scopes)
            }
            response.content = json.dumps(content)

        return response

    def _decompose_access_token_response(self, request, response):
        """ Decomposes the access token in the request to an expiration date, scopes, and User. """
        content = json.loads(response.content.decode('utf-8'))
        access_token = content['access_token']
        scope = content['scope']
        access_token_obj = self.get_adapter(request).get_access_token(access_token)
        user = access_token_obj.user
        scopes = scope.split(' ')
        expires_in = content['expires_in']
        return expires_in, scopes, user

    def _generate_jwt(self, user, scopes, expires_in):
        """ Returns a JWT access token. """
        now = int(time())
        jwt_auth = settings.JWT_AUTH
        payload = {
            'iss': jwt_auth['JWT_ISSUER'],
            'aud': jwt_auth['JWT_AUDIENCE'],
            'exp': now + expires_in,
            'iat': now,
            'preferred_username': user.username,
            'scopes': scopes,
        }

        for scope in scopes:
            handler = self.claim_handlers.get(scope)

            if handler:
                handler(payload, user)

        secret = jwt_auth['JWT_SECRET_KEY']
        token = jwt.encode(payload, secret, algorithm=jwt_auth['JWT_ALGORITHM']).decode('utf-8')

        return token

    def _attach_email_claim(self, payload, user):
        """ Add the email claim details to the JWT payload. """
        payload['email'] = user.email

    def _attach_profile_claim(self, payload, user):
        """ Add the profile claim details to the JWT payload. """
        payload.update({
            'family_name': user.last_name,
            'name': user.get_full_name(),
            'given_name': user.first_name,
            'administrator': user.is_staff,
        })


class AuthorizationView(_DispatchingView):
    """
    Part of the authorization flow.
    """
    dot_view = dot_views.AuthorizationView


class AccessTokenExchangeView(_DispatchingView):
    """
    Exchange a third party auth token.
    """
    dot_view = auth_exchange_views.DOTAccessTokenExchangeView


class RevokeTokenView(_DispatchingView):
    """
    Dispatch to the RevokeTokenView of django-oauth-toolkit
    """
    dot_view = dot_views.RevokeTokenView
