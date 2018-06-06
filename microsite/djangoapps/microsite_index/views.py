import logging

from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie

from article.models import Article

logger = logging.getLogger('microsite_index.views')


@ensure_csrf_cookie
def index_view(request):
    template = 'index.html'
    article_type = int(request.GET.get('article_type', '0'))
    context = {
        'article_type': {'value': article_type, 'display_name': Article.get_type_name(article_type)}
    }
    return render(request, template, context)
