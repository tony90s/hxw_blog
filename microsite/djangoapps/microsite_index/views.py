import logging

from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_page

from article.models import Article

logger = logging.getLogger('microsite_index.views')


@ensure_csrf_cookie
def index_view(request):
    template = 'index.html'
    return render(request, template)


def search_view(request):
    template = 'search.html'
    return render(request, template)