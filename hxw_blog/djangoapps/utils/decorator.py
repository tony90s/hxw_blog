from functools import wraps

from django.conf import settings
from django.shortcuts import HttpResponseRedirect
from django.utils.decorators import available_attrs

from utils.context_processors import is_mobile


def redirect_to_microsite(microsite_base_url=settings.MICROSITE):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not is_mobile(request)['is_mobile_device'] or request.get_host() == microsite_base_url.split('//')[1]:
                return view_func(request, *args, **kwargs)
            return HttpResponseRedirect(microsite_base_url + request.path)

        return _wrapped_view
    return decorator
