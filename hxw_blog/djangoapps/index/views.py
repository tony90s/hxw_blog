import logging

from django.conf import settings
from django.shortcuts import render, HttpResponseRedirect
from django.views.decorators.csrf import ensure_csrf_cookie

from article.models import Article
from utils.context_processors import is_mobile
from utils.decorator import redirect_to_microsite

logger = logging.getLogger('index.views')


@redirect_to_microsite()
@ensure_csrf_cookie
def index_views(request):
    template = 'index.html'
    context = {
        'article_type': {'value': 0, 'display_name': Article.get_type_name(0)}
    }
    return render(request, template, context)


def search_view(request):
    template = 'search.html'
    context = {
        'key_word': request.GET.get('key_word', '')
    }
    return render(request, template, context=context)

