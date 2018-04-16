from datetime import timedelta
import logging
import re

from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from article.models import Article, Comment, CommentReply, Praise, get_user_be_praised
from utils.sensitive_word_handler import sensitive_words_replace

reg_number = re.compile('^\d+$')
logger = logging.getLogger('article.views')


@login_required
def create_article(request):
    template_name = 'article/article_new.html'
    user = request.user
    if not user.is_superuser:
        raise PermissionDenied

    type_choices = Article.TYPE_CHOICES
    context = {
        'article_id': 0,
        'type_choices': type_choices
    }

    return render(request, template_name, context)


@login_required
def edit_article(request, article_id):
    template_name = 'article/article_new.html'
    user = request.user
    if not user.is_superuser:
        raise PermissionDenied

    articles = Article.objects.using('read').filter(id=article_id)
    if not articles.exists():
        raise Http404
    article = articles[0]
    type_choices = Article.TYPE_CHOICES
    context = {
        'article_id': article_id,
        'type_choices': type_choices,
        'article': article
    }

    return render(request, template_name, context)


@require_http_methods(['GET'])
def article_category_index_views(request, article_type):
    page_size = settings.PAGINATORS['SMALL_PAGE_SIZE']

    article_type = int(article_type)
    if article_type not in [value for value, name in Article.TYPE_CHOICES]:
        raise Http404

    template = 'index.html'
    articles = Article.objects.using('read').filter(Q(is_released=1) & Q(type=article_type)).order_by('-release_at')
    articles_summarization = [article.get_summarization() for article in articles[:page_size]]
    context = {
        'article_type': {'value': article_type, 'display_name': Article.get_type_name(article_type)},
        'articles_summarization': articles_summarization,
        'has_next': int(articles.count() > page_size)
    }
    return render(request, template, context)


def article_details(request, article_id):
    page_size = settings.PAGINATORS['SMALL_PAGE_SIZE']
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
        'article_details': article.render_json(),
        'page_size': page_size
    }
    Comment._Comment__user_cache = dict()
    Comment._Comment__article_info_cache = dict()
    CommentReply._CommentReply__user_cache = dict()
    CommentReply._CommentReply__article_info_cache = dict()
    Praise._Praise__user_cache = dict()
    Praise._Praise__article_info_cache = dict()
    return render(request, template_name, context)


@login_required()
def drafts(request):
    page_size = settings.PAGINATORS['SMALL_PAGE_SIZE']
    user = request.user
    user_data = {
        'user_id': user.id,
        'username': user.username if len(user.username) <= 10 else (user.username[:10] + '...'),
        'avatar': user.profile.avatar.url,
        'bio': user.profile.bio
    }

    drafts = Article.objects.using('read').filter(Q(author_id=user.id) & Q(is_released=0)).order_by('-update_at',
                                                                                                    '-created_at')
    drafts_info = [draft.get_summarization() for draft in drafts[:page_size]]
    drafts_count = drafts.count()
    context = {
        'drafts_info': drafts_info,
        'user_data': user_data,
        'drafts_count': drafts_count,
        'has_next': int(drafts_count > page_size)
    }
    return render(request, 'article/user_drafts.html', context)


def user_articles(request, author_id):
    page_size = settings.PAGINATORS['SMALL_PAGE_SIZE']

    authors = User.objects.using('read').filter(id=author_id)
    if not authors.exists():
        raise Http404

    author = authors[0]
    author_data = {
        'user_id': author.id,
        'username': author.username if len(author.username) <= 10 else (author.username[:10] + '...'),
        'avatar': author.profile.avatar.url,
        'bio': author.profile.bio
    }

    articles = Article.objects.using('read').filter(Q(author_id=author.id) & Q(is_released=1)).order_by('-release_at')
    articles_info = [article.get_summarization() for article in articles[:page_size]]
    article_count = articles.count()
    author_praises = get_user_be_praised(author.id)
    context = {
        'articles_info': articles_info,
        'author_data': author_data,
        'article_count': article_count,
        'praises_count': author_praises.count(),
        'has_next': int(article_count > page_size)
    }
    return render(request, 'article/user_articles.html', context)
