from functools import wraps

from django.conf import settings
from django.shortcuts import HttpResponseRedirect

from utils.context_processors import is_mobile


def redirect_to_microsite(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not is_mobile(request)['is_mobile_device'] or request.get_host() == settings.MICROSITE.split('//')[1]:
            return view_func(request, *args, **kwargs)
        microsite = settings.MICROSITE
        return HttpResponseRedirect(microsite + request.path)

    return _wrapped_view
