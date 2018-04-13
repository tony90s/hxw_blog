from datetime import timedelta
import logging

from django.conf import settings
from django.shortcuts import render
from django.db.models import Q
from django.views.decorators.csrf import ensure_csrf_cookie

from article.models import Article, Comment, CommentReply, Praise

logger = logging.getLogger('index.views')


@ensure_csrf_cookie
def index_views(request):
    page_size = settings.DEFAULT_PAGE_SIZE
    template = 'index.html'
    articles = Article.objects.using('read').filter(Q(is_released=1)).order_by('-release_at')
    articles_summarization = [article.get_summarization() for article in articles[:page_size]]
    context = {
        'article_type': {'value': 0, 'display_name': Article.get_type_name(0)},
        'articles_summarization': articles_summarization,
        'page_size': page_size,
        'has_next': int(articles.count() > page_size)
    }
    return render(request, template, context)
