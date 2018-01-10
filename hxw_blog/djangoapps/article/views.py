import logging
import os
import re

from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import render, render_to_response
from django.shortcuts import redirect
from django.http import JsonResponse, HttpResponseForbidden, Http404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse
from django.views import View
from django.utils import timezone
from django.views.decorators.cache import cache_page

from account.models import UserProfile
from article.models import Article, Comment, CommentReply, Praise
from utils.sensitive_word_handler import sensitive_words_replace

reg_number = re.compile('^\d+$')
logger = logging.getLogger('article.views')


@login_required
def create_article(request):
    template_name = 'article/article_new.html'
    user = request.user
    if not user.is_superuser:
        return HttpResponseForbidden()

    type_choices = Article.TYPE_CHOICES
    context = {
        'type_choices': type_choices
    }

    return render(request, template_name, context)


@login_required
@csrf_exempt
def save_article(request):
    user = request.user
    if not user.is_superuser:
        return HttpResponseForbidden()
    title = request.POST.get('title', '')
    article_type = request.POST.get('type')
    cover_photo = request.FILES.get('cover_photo')
    content_txt = request.POST.get('content_txt', '')
    content_html = request.POST.get('content_html', '')
    is_released = request.POST.get('is_released')

    if not title:
        return JsonResponse({'code': 400, 'msg': '请输入标题'})
    if not article_type:
        return JsonResponse({'code': 400, 'msg': '请先选择一个类别'})
    if not content_html or not content_txt:
        return JsonResponse({'code': 400, 'msg': '请先编辑内容'})
    if is_released not in ['0', '1']:
        return JsonResponse({'code': 400, 'msg': '参数有误，请联系网站管理员'})
    try:
        article = Article()
        article.author_id = user.id
        article.title = title
        article.type = int(article_type)
        article.content_html = content_html
        article.content_txt = content_txt
        if cover_photo is not None:
            article.cover_photo = cover_photo
        is_released = int(is_released)
        article.is_released = is_released
        article.save(using='write')

        if is_released:
            article.release_at = timezone.now()
            article.save(using='write')
    except Exception as e:
        logger.error(e)
        return JsonResponse({'code': 500, 'msg': '发布失败，请联系管理员。'})

    redirect_url = reverse('index')
    return JsonResponse({'code': 200, 'msg': '发布成功。', 'redirect_url': redirect_url})


@require_http_methods(['GET'])
def article_category_index_views(request, article_type):
    page_size = settings.DEFAULT_PAGE_SIZE
    page_index = 1

    article_type = int(article_type)
    if article_type not in [value for value, name in Article.TYPE_CHOICES]:
        raise Http404

    template = 'index.html'
    articles = Article.objects.using('read').filter(Q(type=article_type)).order_by('-id')[
               page_size * (page_index - 1):page_size * page_index]
    articles_summarization = [article.get_summarization() for article in articles]
    # get hot articles brief
    all_articles = Article.objects.using('read').all().order_by('-id')
    hot_articles = sorted(all_articles, key=lambda article: article.praise_times, reverse=True)
    hot_articles_briefs = [article.get_brief() for article in hot_articles[:5]]
    context = {
        'article_type': {'value': article_type, 'display_name': Article.get_type_name(article_type)},
        'articles_summarization': articles_summarization,
        'hot_articles_briefs': hot_articles_briefs,
        'page_size': page_size
    }
    return render(request, template, context)


@require_http_methods(['GET'])
def articles_list(request):
    page_size = settings.DEFAULT_PAGE_SIZE
    article_type = request.GET.get('article_type')
    page_index = request.GET.get('page_index')

    if not article_type or not page_index:
        return JsonResponse({'code': 400, 'msg': '参数缺失'})

    if not reg_number.match(article_type):
        return JsonResponse({'code': 400, 'msg': '参数有误'})
    if not reg_number.match(page_index):
        return JsonResponse({'code': 400, 'msg': '参数有误'})

    article_type = int(article_type)
    page_index = int(page_index)

    if page_index <= 0:
        return JsonResponse({'code': 400, 'msg': '参数有误'})
    if article_type not in [value for value, name in Article.TYPE_CHOICES]:
        return JsonResponse({'code': 404, 'msg': '没有此类型的博文'})
    query_condition = Q(type=article_type)

    articles = Article.objects.using('read').filter(query_condition).order_by('-id')[
               page_size * (page_index - 1):page_size * page_index]
    articles_summarization = [article.get_summarization() for article in articles]

    context = {
        'code': 200,
        'msg': '查询成功',
        'data': articles_summarization
    }
    return JsonResponse(context)


def article_details(request, article_id):
    template_name = 'article/article_detail.html'
    articles = Article.objects.using('read').filter(id=article_id)
    if not articles.exists():
        raise Http404
    article = articles[0]
    article.page_views += 1
    article.save(using='write')
    article_details = article.render_json()
    context = {
        'article_details': article_details
    }
    Comment._Comment__user_cache = dict()
    Comment._Comment__article_info_cache = dict()
    CommentReply._CommentReply__user_cache = dict()
    CommentReply._CommentReply__article_info_cache = dict()
    Praise._Praise__user_cache = dict()
    Praise._Praise__article_info_cache = dict()
    return render(request, template_name, context)


@login_required
@csrf_exempt
def save_comment(request):
    user = request.user
    article_id = request.POST.get('article_id', '')
    comment_content = request.POST.get('comment_content', '')

    if not article_id:
        return JsonResponse({'code': 400, 'msg': '参数缺失'})
    if not reg_number.match(article_id):
        return JsonResponse({'code': 400, 'msg': '参数有误'})
    if not comment_content:
        return JsonResponse({'code': 400, 'msg': '请先填写评论内容'})

    try:
        comment = Comment()
        article_id = int(article_id)
        articles = Article.objects.using('read').filter(id=article_id)
        if not articles.exists():
            return JsonResponse({'code': 404, 'msg': '所评论的博文不存在，请联系管理员'})

        comment.article_id = article_id
        comment.commentator_id = user.id
        comment.content = comment_content
        comment.save()

        return_context = {
            'code': 200,
            'msg': '评论创建成功',
            'data': comment.render_json()
        }
        return JsonResponse(return_context)
    except Exception as e:
        logger.error(e)
        return JsonResponse({'code': 500, 'msg': '保存失败，请联系管理员。'})


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
    comments = Comment.objects.using('read').filter(query_condition).order_by('-id')[
               page_size * (page_index - 1):page_size * page_index]
    comments_data = [comment.render_json() for comment in comments]

    context = {
        'code': 200,
        'msg': '查询成功',
        'data': comments_data
    }
    return JsonResponse(context)


@login_required
@csrf_exempt
def save_comment_reply(request):
    user = request.user
    comment_id = request.POST.get('comment_id', '')
    receiver_id = request.POST.get('receiver_id', '')
    content = request.POST.get('content', '')

    if not comment_id or not receiver_id:
        return JsonResponse({'code': 400, 'msg': '参数缺失'})
    if not reg_number.match(comment_id) or not reg_number.match(receiver_id):
        return JsonResponse({'code': 400, 'msg': '参数有误'})

    if not content:
        return JsonResponse({'code': 400, 'msg': '请先填写回复内容'})

    comment_id = int(comment_id)
    receiver_id = int(receiver_id)

    comments = Comment.objects.using('read').filter(id=comment_id)
    if not comments.exists():
        return JsonResponse({'code': 404, 'msg': '所回复评论不存在，请联系管理员'})
    receivers = User.objects.using('read').filter(id=receiver_id)
    if not receivers.exists():
        return JsonResponse({'code': 404, 'msg': '所回复的童鞋不存在，请联系管理员'})

    """
    if user.id == receiver_id:
        return JsonResponse({'code': 400, 'msg': '不能回复自己'})
    """

    comment_reply = CommentReply()
    comment_reply.comment_id = comment_id
    comment_reply.receiver_id = receiver_id
    comment_reply.replier_id = user.id
    comment_reply.content = content
    comment_reply.save(using='write')

    return_context = {
        'code': 200,
        'msg': '回复成功',
        'data': comment_reply.render_json()
    }
    return JsonResponse(return_context)


@login_required
@csrf_exempt
def save_praise(request):
    user = request.user
    praise_type = request.POST.get('praise_type', '')
    parent_id = request.POST.get('parent_id', '')

    if not praise_type or not parent_id:
        return JsonResponse({'code': 400, 'msg': '参数缺失'})
    if not reg_number.match(praise_type) or not reg_number.match(parent_id):
        return JsonResponse({'code': 400, 'msg': '参数有误'})

    praise_type = int(praise_type)
    parent_id= int(parent_id)
    if praise_type not in [value for value, name in Praise.TYPE_CHOICES]:
        return JsonResponse({'code': 400, 'msg': '参数有误'})

    if praise_type == Praise.TYPE.ARTICLE:
        praise_parents = Article.objects.using('read').filter(id=parent_id)
    elif praise_type == Praise.TYPE.COMMENT:
        praise_parents = Comment.objects.using('read').filter(id=parent_id)
    else:
        praise_parents = CommentReply.objects.using('read').filter(id=parent_id)

    if not praise_parents.exists():
        return JsonResponse({'code': 404, 'msg': '所点赞对象不存在'})

    praises = Praise.objects.using('read').filter(Q(praise_type=praise_type) &
                                                  Q(parent_id=parent_id) & Q(user_id=user.id))
    if praises.exists():
        return JsonResponse({'code': 304, 'msg': '你已点赞，无需重复点赞'})

    praise = Praise()
    praise.praise_type = praise_type
    praise.parent_id = parent_id
    praise.user_id = user.id
    praise.save(using='write')

    return_context = {
        'code': 200,
        'msg': '点赞成功',
        'praise_id': praise.id
    }
    return JsonResponse(return_context)


@login_required
@csrf_exempt
def delete_article(request):
    user = request.user
    article_id = request.POST.get('article_id', '')

    if not article_id:
        return JsonResponse({'code': 400, 'msg': '参数缺失'})
    if not reg_number.match(article_id):
        return JsonResponse({'code': 400, 'msg': '参数有误'})

    article_id = int(article_id)
    articles = Article.objects.using('write').filter(id=article_id)
    if not articles.exists():
        return JsonResponse({'code': 404, 'msg': '所要删除的博文不存在'})

    if user.id != articles[0].author_id:
        return JsonResponse({'code': 403, 'msg': '不能删除其它童鞋的博文'})

    articles.delete()
    return JsonResponse({'code': 200, 'msg': '删除博文成功'})


@login_required
@csrf_exempt
def delete_comment(request):
    user = request.user
    comment_id = request.POST.get('comment_id', '')

    if not comment_id:
        return JsonResponse({'code': 400, 'msg': '参数缺失'})
    if not reg_number.match(comment_id):
        return JsonResponse({'code': 400, 'msg': '参数有误'})

    comment_id = int(comment_id)
    comments = Comment.objects.using('write').filter(id=comment_id)
    if not comments.exists():
        return JsonResponse({'code': 404, 'msg': '所要删除的评论不存在'})

    if user.id != comments[0].commentator_id:
        return JsonResponse({'code': 403, 'msg': '不能删除其它童鞋的评论'})

    comments.delete()
    comment_replies = CommentReply.objects.using('write').filter(comment_id=comment_id)
    comment_replies.delete()
    return JsonResponse({'code': 200, 'msg': '删除评论成功'})


@login_required
@csrf_exempt
def delete_comment_reply(request):
    user = request.user
    comment_reply_id = request.POST.get('comment_reply_id', '')

    if not comment_reply_id:
        return JsonResponse({'code': 400, 'msg': '参数缺失'})
    if not reg_number.match(comment_reply_id):
        return JsonResponse({'code': 400, 'msg': '参数有误'})

    comment_reply_id = int(comment_reply_id)
    comment_replies = CommentReply.objects.using('write').filter(id=comment_reply_id)
    if not comment_replies.exists():
        return JsonResponse({'code': 404, 'msg': '所要删除的回复不存在'})

    if user.id != comment_replies[0].replier_id:
        return JsonResponse({'code': 403, 'msg': '不能删除其它童鞋的回复'})

    comment_replies.delete()
    return JsonResponse({'code': 200, 'msg': '删除回复成功'})


@login_required
@csrf_exempt
def cancel_praise(request):
    user = request.user
    praise_type = request.POST.get('praise_type', '')
    parent_id = request.POST.get('parent_id', '')

    if not praise_type or not parent_id:
        return JsonResponse({'code': 400, 'msg': '参数缺失'})
    if not reg_number.match(praise_type) or not reg_number.match(parent_id):
        return JsonResponse({'code': 400, 'msg': '参数有误'})

    praise_type = int(praise_type)
    parent_id = int(parent_id)
    if praise_type not in [value for value, name in Praise.TYPE_CHOICES]:
        return JsonResponse({'code': 400, 'msg': '参数有误'})

    praises = Praise.objects.using('write').filter(Q(praise_type=praise_type) &
                                                  Q(parent_id=parent_id) & Q(user_id=user.id))
    if not praises.exists():
        return JsonResponse({'code': 400, 'msg': '您尚未点赞，不能取消赞'})

    praises.delete()
    return JsonResponse({'code': 200, 'msg': '取消点赞成功'})


@csrf_exempt
def update_is_viewed_status(request):
    object_type = request.POST.get('object_type')   # 1 comment  2 comment_reply   3 praise
    parent_id = request.POST.get('parent_id')

    if not object_type or not parent_id:
        return JsonResponse({'code': 400, 'msg': '参数缺失'})

    if not reg_number.match(object_type) or not reg_number.match(parent_id):
        return JsonResponse({'code': 400, 'msg': '参数有误'})

    object_type = int(object_type)
    parent_id = int(parent_id)

    if object_type not in [1, 2, 3]:
        return JsonResponse({'code': 400, 'msg': '参数有误'})

    if object_type == 1:
        comments = Comment.objects.using('read').filter(id=parent_id)
        if not comments.exists():
            return JsonResponse({'code': 404, 'msg': '对象不存在'})
        comment = comments[0]
        comment.is_viewed = 1
        comment.save(using='write')
    elif object_type == 2:
        comment_replies = CommentReply.objects.using('read').filter(id=parent_id)
        if not comment_replies.exists():
            return JsonResponse({'code': 404, 'msg': '对象不存在'})
        comment_reply = comment_replies[0]
        comment_reply.is_viewed = 1
        comment_reply.save(using='write')
    else:
        praises = Praise.objects.using('read').filter(id=parent_id)
        if not praises.exists():
            return JsonResponse({'code': 404, 'msg': '对象不存在'})
        praise = praises[0]
        praise.is_viewed = 1
        praise.save(using='write')
    return JsonResponse({'code': 200, 'msg': '更新成功'})
