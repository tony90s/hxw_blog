import logging

from django.conf import settings
from django.shortcuts import render_to_response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.template import RequestContext

from account.models import UserProfile
from article.models import Article

logger = logging.getLogger('index.views')


@ensure_csrf_cookie
@require_http_methods(['GET'])
def index_views(request):
    page_size = 25
    page_index = 1
    user = request.user
    template = 'index.html'
    articles = Article.objects.using('read').all().order_by('-id')
    hot_articles = sorted(articles, key=lambda article: article.praise_times, reverse=True)
    hot_articles_briefs = [article.get_brief() for article in hot_articles[:5]]
    articles_summarization = [article.get_summarization() for article in articles][page_size*(page_index-1):page_size*page_index]
    context = {
        'user': user,
        'article_type': 0,
        'articles_summarization': articles_summarization,
        'hot_articles_briefs': hot_articles_briefs
    }
    return render_to_response(template, context)
