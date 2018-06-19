import logging

from django.conf import settings
from django.shortcuts import render, HttpResponseRedirect
from django.views.decorators.csrf import ensure_csrf_cookie

from article.models import Article
from utils.context_processors import is_mobile

logger = logging.getLogger('index.views')


@ensure_csrf_cookie
def index_views(request):
    is_mobile_device = is_mobile(request)['is_mobile_device']
    if is_mobile_device:
        return HttpResponseRedirect(settings.MICROSITE)
    
    template = 'index.html'
    context = {
        'article_type': {'value': 0, 'display_name': Article.get_type_name(0)}
    }
    return render(request, template, context)
