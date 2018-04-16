import logging

from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

from article.models import Article

logger = logging.getLogger('index.views')


@ensure_csrf_cookie
def index_views(request):
    template = 'index.html'
    context = {
        'article_type': {'value': 0, 'display_name': Article.get_type_name(0)}
    }
    return render(request, template, context)
