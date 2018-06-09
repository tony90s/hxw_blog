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
    Article._Article__user_cache = dict()
    return render(request, template_name, context)


def comment_details(request, comment_id):
    template_name = 'article/comment_details.html'

    comments = Comment.objects.using('read').filter(id=comment_id)
    if not comments.exists():
        raise Http404
    comment = comments[0]

    context = {
        'comment': comment.get_comment_summary()
    }
    Comment._Comment__user_cache = dict()
    return render(request, template_name, context)
