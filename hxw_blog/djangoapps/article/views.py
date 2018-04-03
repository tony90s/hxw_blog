from datetime import timedelta
import logging
import os
import re

from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import render, render_to_response, redirect
from django.http import JsonResponse, HttpResponseForbidden, Http404, QueryDict
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse
from django.views import View
from django.utils import timezone
# from django.views.decorators.cache import cache_page

from account.models import UserProfile
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
    page_size = settings.DEFAULT_PAGE_SIZE
    page_index = 1

    article_type = int(article_type)
    if article_type not in [value for value, name in Article.TYPE_CHOICES]:
        raise Http404

    template = 'index.html'
    all_articles = Article.objects.using('read').filter(Q(is_released=1))
    articles = all_articles.filter(Q(type=article_type)).order_by('-id')
    articles_summarization = [article.get_summarization() for article in
                              articles[page_size * (page_index - 1):page_size * page_index]]
    """
    # get hot articles brief
    now = timezone.now()
    hot_articles = sorted(all_articles.filter(Q(release_at__gte=(now + timedelta(days=-60)))),
                          key=lambda article: article.praise_times, reverse=True)[:5]
    hot_articles_briefs = [article.get_brief() for article in hot_articles]
    """
    context = {
        'article_type': {'value': article_type, 'display_name': Article.get_type_name(article_type)},
        'articles_summarization': articles_summarization,
        'page_size': page_size,
        'has_next': len(articles) > page_size
    }
    return render(request, template, context)


@require_http_methods(['GET'])
def articles_list(request):
    page_size = settings.DEFAULT_PAGE_SIZE
    article_type = request.GET.get('article_type', '0')
    page_index = request.GET.get('page_index', '1')
    author_id = request.GET.get('author_id', '0')
    is_released = request.GET.get('is_released', '1')

    if not reg_number.match(article_type) or not reg_number.match(page_index) or not reg_number.match(
            author_id) or not reg_number.match(is_released):
        return JsonResponse({'code': 400, 'msg': '参数有误'})

    article_type = int(article_type)
    page_index = int(page_index)
    author_id = int(author_id)
    is_released = int(is_released)

    if page_index <= 0:
        return JsonResponse({'code': 400, 'msg': '参数有误'})
    if is_released not in [0, 1]:
        return JsonResponse({'code': 400, 'msg': '参数有误'})

    query_condition = Q(is_released=is_released)
    if article_type > 0:
        if article_type not in [value for value, name in Article.TYPE_CHOICES]:
            return JsonResponse({'code': 404, 'msg': '没有此类型的博文'})
        query_condition &= Q(type=article_type)

    if author_id > 0:
        query_condition &= Q(author_id=author_id)

    articles = Article.objects.using('read').filter(query_condition).order_by('-id')
    articles_summarization = [article.get_summarization() for article in
                              articles[page_size * (page_index - 1):page_size * page_index]]

    context = {
        'code': 200,
        'msg': '查询成功',
        'data': articles_summarization,
        'has_next': int(len(articles) > (page_index * page_size))
    }
    return JsonResponse(context)


def article_details(request, article_id):
    page_size = settings.DEFAULT_PAGE_SIZE
    template_name = 'article/article_detail.html'
    articles = Article.objects.using('read').filter(id=article_id)
    if not articles.exists():
        raise Http404
    article = articles[0]
    if not article.is_released:
        raise Http404
    article.page_views += 1
    article.save(using='write')
    article_details = article.render_json()
    context = {
        'article_details': article_details,
        'page_size': page_size
    }
    Comment._Comment__user_cache = dict()
    Comment._Comment__article_info_cache = dict()
    CommentReply._CommentReply__user_cache = dict()
    CommentReply._CommentReply__article_info_cache = dict()
    Praise._Praise__user_cache = dict()
    Praise._Praise__article_info_cache = dict()
    return render(request, template_name, context)


@require_http_methods(['GET'])
def article_comments_list(request):
    page_size = settings.DEFAULT_PAGE_SIZE
    article_id = request.GET.get('article_id')
    page_index = request.GET.get('page_index')
    if not article_id or not page_index:
        return JsonResponse({'code': 400, 'msg': '参数缺失'})
    if not reg_number.match(article_id) or not reg_number.match(page_index):
        return JsonResponse({'code': 400, 'msg': '参数有误'})
    article_id = int(article_id)
    page_index = int(page_index)

    if page_index <= 0:
        return JsonResponse({'code': 400, 'msg': '参数有误'})
    articles = Article.objects.using('read').filter(id=article_id)
    if not articles.exists():
        return JsonResponse({'code': 404, 'msg': '博文不存在'})

    query_condition = Q(article_id=article_id)
    comments = Comment.objects.using('read').filter(query_condition).order_by('-id')
    query_comments = comments[page_size * (page_index - 1):page_size * page_index]
    comments_data = [comment.render_json() for comment in query_comments]

    context = {
        'code': 200,
        'msg': '查询成功',
        'count': len(comments),
        'data': comments_data,
        'has_next': len(comments) > (page_index * page_size)
    }
    return JsonResponse(context)


@login_required()
def drafts(request):
    page_size = settings.DEFAULT_PAGE_SIZE
    user = request.user
    user_data = {
        'user_id': user.id,
        'username': user.username if len(user.username) <= 10 else (user.username[:10] + '...'),
        'avatar': user.profile.avatar.url,
        'bio': user.profile.bio
    }

    drafts = Article.objects.using('read').filter(Q(author_id=user.id) & Q(is_released=0)).order_by('-id')
    drafts_info = [draft.get_summarization() for draft in drafts[:page_size]]
    context = {
        'drafts_info': drafts_info,
        'page_size': page_size,
        'user_data': user_data,
        'drafts_count': len(drafts),
        'has_next': int(len(drafts) > page_size)
    }
    return render(request, 'article/user_drafts.html', context)


def user_articles(request, author_id):
    page_size = settings.DEFAULT_PAGE_SIZE

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

    articles = Article.objects.using('read').filter(Q(author_id=author.id) & Q(is_released=1)).order_by('-id')
    articles_info = [article.get_summarization() for article in articles[:page_size]]
    author_praises = get_user_be_praised(author.id)
    context = {
        'articles_info': articles_info,
        'page_size': page_size,
        'author_data': author_data,
        'article_count': articles.count(),
        'praises_count': author_praises.count(),
        'has_next': int(len(articles) > page_size)
    }
    return render(request, 'article/user_articles.html', context)
