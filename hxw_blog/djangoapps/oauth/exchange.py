"""
Views to support exchange of authentication credentials.
The following are currently implemented:
    1. AccessTokenExchangeView:
       3rd party (social-auth) OAuth 2.0 access token -> 1st party (open-edx) OAuth 2.0 access token
    2. LoginWithAccessTokenView:
       1st party (open-edx) OAuth 2.0 access token -> session cookie
"""

# pylint: disable=abstract-method

from django.conf import settings
from django.contrib.auth import login
import django.contrib.auth as auth
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from oauth2_provider.settings import oauth2_settings
from oauth2_provider.views.base import TokenView as DOTAccessTokenView
from oauthlib.oauth2.rfc6749.tokens import BearerToken

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from oauth import adapter
from utils.rest_framework.authentication import OAuth2AuthenticationAllowInactiveUser

# Use bit-shifting so that scopes can be easily combined and checked.
DEFAULT_SCOPE = 0
OPEN_ID_SCOPE = 1 << 0
PROFILE_SCOPE = 1 << 1
EMAIL_SCOPE = 1 << 2
COURSE_STAFF_SCOPE = 1 << 3
COURSE_INSTRUCTOR_SCOPE = 1 << 4
PERMISSIONS = 1 << 5

# Scope setting as required by django-oauth-provider
# The default scope value is SCOPES[0][0], which in this case is zero.
# `django-oauth-provider` considers a scope value of zero as empty,
# ignoring its name when requested.
SCOPES = (
    (DEFAULT_SCOPE, 'default'),
    (OPEN_ID_SCOPE, 'openid'),
    (PROFILE_SCOPE, 'profile'),
    (EMAIL_SCOPE, 'email'),
    (COURSE_STAFF_SCOPE, 'course_staff'),
    (COURSE_INSTRUCTOR_SCOPE, 'course_instructor'),
    (PERMISSIONS, 'permissions')
)

SCOPE_NAMES = [(name, name) for (value, name) in SCOPES]
SCOPE_NAME_DICT = dict([(name, value) for (value, name) in SCOPES])
SCOPE_VALUE_DICT = dict([(value, name) for (value, name) in SCOPES])

SINGLE_ACCESS_TOKEN = getattr(settings, 'OAUTH_SINGLE_ACCESS_TOKEN', False)


class AccessTokenExchangeBase(APIView):
    """
    View for token exchange from 3rd party OAuth access token to 1st party
    OAuth access token.
    """
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(AccessTokenExchangeBase, self).dispatch(*args, **kwargs)

    def get(self, request, _backend):  # pylint: disable=arguments-differ
        """
        Pass through GET requests without the _backend
        """
        return super(AccessTokenExchangeBase, self).get(request)

    def post(self, request, _backend):  # pylint: disable=arguments-differ
        """
        Handle POST requests to get a first-party access token.
        """

        user = request.POST["user"]
        scope = request.POST["scope"]
        client = request.POST["client"]

        return self.exchange_access_token(request, user, scope, client)

    def exchange_access_token(self, request, user, scope, client):
        """
        Exchange third party credentials for an edx access token, and return a
        serialized access token response.
        """
        if SINGLE_ACCESS_TOKEN:
            edx_access_token = self.get_access_token(request, user, scope, client)  # pylint: disable=no-member
        else:
            edx_access_token = self.create_access_token(request, user, scope, client)
        return self.access_token_response(edx_access_token)  # pylint: disable=no-member


class DOTAccessTokenExchangeView(AccessTokenExchangeBase, DOTAccessTokenView):
    """
    View for token exchange from 3rd party OAuth access token to 1st party
    OAuth access token.  Uses django-oauth-toolkit (DOT) to manage access
    tokens.
    """

    oauth2_adapter = adapter.DOTAdapter()

    def get(self, request, _backend):
        return Response(status=400, data={
            'error': 'invalid_request',
            'error_description': 'Only POST requests allowed.',
        })

    def get_access_token(self, request, user, scope, client):
        """
        TODO: MA-2122: Reusing access tokens is not yet supported for DOT.
        Just return a new access token.
        """
        return self.create_access_token(request, user, scope, client)

    def create_access_token(self, request, user, scope, client):
        """
        Create and return a new access token.
        """
        _days = 24 * 60 * 60
        token_generator = BearerToken(
            expires_in=settings.OAUTH_EXPIRE_PUBLIC_CLIENT_DAYS * _days,
            request_validator=oauth2_settings.OAUTH2_VALIDATOR_CLASS(),
        )
        self._populate_create_access_token_request(request, user, scope, client)
        return token_generator.create_token(request, refresh_token=True)

    def access_token_response(self, token):
        """
        Wrap an access token in an appropriate response
        """
        return Response(data=token)

    def _populate_create_access_token_request(self, request, user, scope, client):
        """
        django-oauth-toolkit expects certain non-standard attributes to
        be present on the request object.  This function modifies the
        request object to match these expectations
        """
        request.user = user
        request.scopes = [SCOPE_VALUE_DICT[scope]]
        request.client = client
        request.state = None
        request.refresh_token = None
        request.extra_credentials = None
        request.grant_type = client.authorization_grant_type

    def error_response(self, form_errors):
        """
        Return an error response consisting of the errors in the form
        """
        return Response(status=400, data=form_errors)


class LoginWithAccessTokenView(APIView):
    """
    View for exchanging an access token for session cookies
    """
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser,)
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def _get_path_of_arbitrary_backend_for_user(user):
        """
        Return the path to the first found authentication backend that recognizes the given user.
        """
        for backend_path in settings.AUTHENTICATION_BACKENDS:
            backend = auth.load_backend(backend_path)
            if backend.get_user(user.id):
                return backend_path

    @method_decorator(csrf_exempt)
    def post(self, request):
        """
        Handler for the POST method to this view.
        """
        # The django login method stores the user's id in request.session[SESSION_KEY] and the
        # path to the user's authentication backend in request.session[BACKEND_SESSION_KEY].
        # The login method assumes the backend path had been previously stored in request.user.backend
        # in the 'authenticate' call.  However, not all authentication providers do so.
        # So we explicitly populate the request.user.backend field here.
        if not hasattr(request.user, 'backend'):
            request.user.backend = self._get_path_of_arbitrary_backend_for_user(request.user)
        login(request, request.user)  # login generates and stores the user's cookies in the session
        return HttpResponse(status=204)  # cookies stored in the session are returned with the response
