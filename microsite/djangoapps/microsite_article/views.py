import logging

from django.shortcuts import render
from django.http import JsonResponse, Http404

from article.models import Article, Comment, CommentReply, Praise, get_user_be_praised


logger = logging.getLogger('microsite_article.views')


def article_details(request, article_id):
    template_name = 'article/article_detail.html'

    articles = Article.objects.using('read').filter(id=article_id)
    if not articles.exists():
        raise Http404
    article = articles[0]
    if not article.is_released:
        raise Http404

    article.page_views += 1
    article.save(using='write')

    context = {
        'article_details': article.render_json()
    }
    return render(request, template_name, context)
