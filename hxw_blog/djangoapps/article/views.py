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

from account.models import render_user_info
from article.models import Article, Comment, Praise, get_user_be_praised, get_user_article_count, get_user_praises_count
# from utils.sensitive_word_handler import sensitive_words_replace
from utils.decorator import redirect_to_microsite

reg_number = re.compile('^\d+$')
logger = logging.getLogger('article.views')


@login_required
def create_article(request):
    template_name = 'article/article_new.html'
    user = request.user
    if not user.is_staff:
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
    if not user.is_staff:
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
    template = 'index.html'
    article_type = int(article_type)
    if article_type not in [value for value, name in Article.TYPE_CHOICES]:
        raise Http404

    context = {
        'article_type': {'value': article_type, 'display_name': Article.get_type_name(article_type)}
    }
    return render(request, template, context)


@redirect_to_microsite
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


@login_required()
def drafts(request):
    user = request.user
    user_data = render_user_info(user)

    drafts = Article.objects.using('read').filter(Q(author_id=user.id) & Q(is_released=0)).order_by('-update_at',
                                                                                                    '-created_at')
    drafts_count = drafts.count()
    context = {
        'user_data': user_data,
        'drafts_count': drafts_count
    }
    return render(request, 'article/user_drafts.html', context)


@redirect_to_microsite
def user_articles(request, author_id):
    authors = User.objects.using('read').filter(id=author_id)
    if not authors.exists():
        raise Http404

    author = authors[0]
    author_data = render_user_info(author)

    article_count = get_user_article_count(author.id)
    praises_count = get_user_praises_count(author.id)
    context = {
        'author_data': author_data,
        'article_count': article_count,
        'praises_count': praises_count,
    }
    return render(request, 'article/user_articles.html', context)
