import logging

from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie

from article.models import Article

logger = logging.getLogger('microsite_index.views')


@ensure_csrf_cookie
def index_view(request):
    template = 'index.html'
    context = {
        'article_type': {'value': 0, 'display_name': Article.get_type_name(0)}
    }
    return HttpResponse('coming soon')
