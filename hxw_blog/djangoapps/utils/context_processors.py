import re
from django.conf import settings


def site_info(request):
    return {'site_name': settings.SITE_NAME}


def is_mobile(request):
    is_mobile_flag = False
    user_agent = request.META['HTTP_USER_AGENT']

    pattern = r'(AppleWebKit.*Mobile.*)|Android|iPhone|iPad|MicroMessenger|(\sQQ)|(\(i[^;]+;( U;)? CPU.+Mac OS X)'
    mobile_matches = re.compile(pattern, re.IGNORECASE)

    if mobile_matches.search(user_agent) is not None:
        is_mobile_flag = True
    return {
        'is_mobile_device': is_mobile_flag
    }
