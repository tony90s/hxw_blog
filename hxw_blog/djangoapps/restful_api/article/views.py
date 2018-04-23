import logging
import re

from django.core.urlresolvers import reverse
from django.http import Http404
from django.db.models import Q
from django import forms
from django.utils import timezone
from django.contrib.auth.models import User

from rest_framework import serializers, generics, permissions, mixins
from rest_framework.response import Response
from article.models import Article, Comment, CommentReply, Praise, get_user_be_praised
from restful_api.article.serializers import (
    ArticleSerializer,
    CommentSerializer,
    PraiseSerializer,
    SaveArticleSerializer,
    SaveCommentSerializer,
    SaveCommentReplySerializer,
    SavePraiseSerializer
)
from restful_api.article.forms import (
    ArticleListForm,
    PraiseListForm,
    CancelPraiseForm,
    UpdateIsViewedStatusForm,
    CheckArticleIdForm,
    DeleteCommentReplyForm,
    DeleteCommentForm
)
from restful_api.article.permissions import (
    IsAuthorOrReadOnly,
    IsCommentatorOrReadOnly,
    IsReplierOrReadOnly,
    IsPraiseOwnerOrReadOnly
)
from utils.paginators import SmallResultsSetPagination
from utils.rest_framework import generics as extra_generics

reg_number = re.compile('^\d+$')
logger = logging.getLogger('api.article')


class CreateArticleView(generics.CreateAPIView):
    serializer_class = SaveArticleSerializer
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser,)

    def perform_create(self, serializer):
        serializer.save(author_id=self.request.user.id)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        is_released = serializer.validated_data.get('is_released')
        if is_released:
            msg = '发布成功'
            redirect_url = reverse('article:user_articles', kwargs={'author_id': request.user.id})
        else:
            msg = '草稿保存成功'
            redirect_url = reverse('article:user_drafts')
        return Response({'code': 200, 'msg': msg, 'redirect_url': redirect_url})


class UpdateDestroyArticleView(extra_generics.UpdateDestroyAPIView):
    serializer_class = SaveArticleSerializer
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser, IsAuthorOrReadOnly,)

    def get_object(self):
        article_id = self.kwargs.get('article_id')
        try:
            article = Article.objects.using('read').get(id=int(article_id))
        except Article.DoesNotExist:
            raise Http404
        self.check_object_permissions(self.request, article)
        return article

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        self.perform_update(serializer)
        is_released = serializer.validated_data.get('is_released')
        if is_released:
            msg = '发布成功'
            redirect_url = reverse('article:user_articles', kwargs={'author_id': request.user.id})
        else:
            msg = '草稿保存成功'
            redirect_url = reverse('article:user_drafts')
        return Response({'code': 200, 'msg': msg, 'redirect_url': redirect_url})

    def perform_destroy(self, instance):
        article_id = instance.id
        comments = Comment.objects.using('write').filter(article_id=article_id)
        comments_id = list(comments.values_list('id', flat=True).order_by('id'))
        comment_replies = CommentReply.objects.using('write').filter(comment_id__in=comments_id)
        comment_replies_id = list(comment_replies.values_list('id', flat=True).order_by('id'))
        praises = Praise.objects.using('write').filter(
            (Q(praise_type=Praise.TYPE.ARTICLE) & Q(parent_id=article_id)) | (
                Q(praise_type=Praise.TYPE.COMMENT) & Q(parent_id__in=comments_id)) | (
                Q(praise_type=Praise.TYPE.COMMENT_REPLY) & Q(parent_id__in=comment_replies_id)))
        praises.delete()
        comment_replies.delete()
        comments.delete()
        instance.delete()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'code': 200, 'msg': '删除博文成功'})


class ArticleList(generics.ListAPIView):
    """
    List all articles
    """

    pagination_class = SmallResultsSetPagination
    serializer_class = ArticleSerializer

    def get_queryset(self):
        form = ArticleListForm(self.request.query_params)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        article_type = form.cleaned_data.get('article_type') or 0
        is_released = form.cleaned_data.get('is_released')
        author_id = form.cleaned_data.get('author_id') or 0

        query_condition = Q(is_released=is_released)
        if author_id > 0:
            query_condition &= Q(author_id=author_id)
        if article_type > 0:
            query_condition &= Q(type=article_type)

        articles = Article.objects.using('read').filter(query_condition)
        if is_released:
            articles = articles.order_by('-release_at')
        else:
            articles = articles.order_by('-update_at')
        return articles

    def clean_cache(self):
        Article._Article__user_cache = dict()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(queryset, many=True)
            response = Response(serializer.data)
        self.clean_cache()
        return response


class CommentList(generics.ListAPIView):
    """
    List all comment
    """

    pagination_class = SmallResultsSetPagination
    serializer_class = CommentSerializer

    def get_queryset(self):
        form = CheckArticleIdForm(self.request.query_params)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        article_id = form.cleaned_data.get('article_id')
        articles = Article.objects.using('read').filter(id=article_id)
        if not articles.exists():
            raise Http404

        comments = Comment.objects.using('read').filter(Q(article_id=article_id)).order_by('-id')
        return comments

    def clean_cache(self):
        Comment._Comment__user_cache = dict()
        Comment._Comment__article_info_cache = dict()
        CommentReply._CommentReply__user_cache = dict()
        CommentReply._CommentReply__article_info_cache = dict()
        Praise._Praise__user_cache = dict()
        Praise._Praise__article_info_cache = dict()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(queryset, many=True)
            response = Response(serializer.data)
        self.clean_cache()
        return response


class PraiseList(generics.ListAPIView):
    """
    List all user be_praises.
    """

    pagination_class = SmallResultsSetPagination
    serializer_class = PraiseSerializer

    def get_queryset(self):
        form = PraiseListForm(self.request.query_params)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        user_id = form.cleaned_data.get('user_id')
        return get_user_be_praised(user_id)

    def clean_cache(self):
        Comment._Comment__user_cache = dict()
        Comment._Comment__article_info_cache = dict()
        CommentReply._CommentReply__user_cache = dict()
        CommentReply._CommentReply__article_info_cache = dict()
        Praise._Praise__user_cache = dict()
        Praise._Praise__article_info_cache = dict()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(queryset, many=True)
            response = Response(serializer.data)
        self.clean_cache()
        return response


class SaveCommentView(generics.CreateAPIView):
    serializer_class = SaveCommentSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        serializer.save(commentator_id=self.request.user.id)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return_context = {
            'code': 200,
            'msg': '评论创建成功',
            'data': serializer.instance.render_json()
        }
        return Response(return_context)


class DeleteCommentView(generics.DestroyAPIView):
    permission_classes = (permissions.IsAuthenticated, IsCommentatorOrReadOnly,)

    def get_object(self):
        form = DeleteCommentForm(self.request.data)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        comment_id = form.cleaned_data.get('comment_id')
        comments = Comment.objects.using('read').filter(id=comment_id)
        if not comments.exists():
            raise Http404
        comment = comments[0]
        self.check_object_permissions(self.request, comment)
        return comment

    def perform_destroy(self, instance):
        comment_id = instance.id
        comment_replies = CommentReply.objects.using('write').filter(comment_id=comment_id)
        comment_replies_id = list(comment_replies.values_list('id', flat=True).order_by('id'))
        praises = Praise.objects.using('write').filter(
            (Q(praise_type=Praise.TYPE.COMMENT) & Q(parent_id=comment_id)) | (
                Q(praise_type=Praise.TYPE.COMMENT_REPLY) & Q(parent_id__in=comment_replies_id)))
        praises.delete()
        comment_replies.delete()
        instance.delete()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'code': 200, 'msg': '删除评论成功'})


class SaveCommentReplyView(generics.CreateAPIView):
    serializer_class = SaveCommentReplySerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        serializer.save(replier_id=self.request.user.id)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return_context = {
            'code': 200,
            'msg': '回复成功',
            'data': serializer.instance.render_json()
        }
        return Response(return_context)


class DeleteCommentReplyView(generics.DestroyAPIView):
    permission_classes = (permissions.IsAuthenticated, IsReplierOrReadOnly,)

    def get_object(self):
        form = DeleteCommentReplyForm(self.request.data)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        comment_reply_id = form.cleaned_data.get('comment_reply_id')
        comment_replies = CommentReply.objects.using('read').filter(id=comment_reply_id)
        if not comment_replies.exists():
            raise Http404
        comment_reply = comment_replies[0]
        self.check_object_permissions(self.request, comment_reply)
        return comment_reply

    def perform_destroy(self, instance):
        praises = Praise.objects.using('write').filter(
            Q(praise_type=Praise.TYPE.COMMENT_REPLY) & Q(parent_id=instance.id))
        praises.delete()
        instance.delete()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'code': 200, 'msg': '删除回复成功'})


class SavePraiseView(generics.CreateAPIView):
    serializer_class = SavePraiseSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user.id)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return_context = {
            'code': 200,
            'msg': '点赞成功',
            'praise_id': serializer.instance.id
        }
        return Response(return_context)


class CancelPraiseView(generics.DestroyAPIView):
    permission_classes = (permissions.IsAuthenticated, IsPraiseOwnerOrReadOnly,)

    def get_object(self):
        form = CancelPraiseForm(self.request.data)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        praise_type = form.cleaned_data.get('praise_type')
        parent_id = form.cleaned_data.get('parent_id')
        user_id = self.request.user.id
        praises = Praise.objects.using('read').filter(Q(praise_type=praise_type) &
                                                      Q(parent_id=parent_id) & Q(user_id=user_id))
        if not praises.exists():
            raise Http404
        praise = praises[0]
        self.check_object_permissions(self.request, praise)
        return praise

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'code': 200, 'msg': '取消点赞成功'})


class UpdateIsViewedStatusView(generics.UpdateAPIView):
    def get_queryset(self):
        form = UpdateIsViewedStatusForm(self.request.data)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)
        object_type = form.cleaned_data.get('object_type')
        parent_id = form.cleaned_data.get('parent_id')

        if object_type == 1:
            instances = Comment.objects.using('write').filter(id=parent_id)
        elif object_type == 2:
            instances = CommentReply.objects.using('write').filter(id=parent_id)
        else:
            instances = Praise.objects.using('write').filter(id=parent_id)
        if not instances.exists():
            raise Http404
        return instances

    def perform_update(self, instances):
        instances.update(is_viewed=1)

    def update(self, request, *args, **kwargs):
        instances = self.get_queryset()
        self.perform_update(instances)
        return Response({'code': 200, 'msg': '更新成功'})


class UpdateArticleReleaseStatusView(generics.UpdateAPIView):
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser, IsAuthorOrReadOnly,)

    def get_object(self):
        form = CheckArticleIdForm(self.request.data)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        article_id = form.cleaned_data.get('article_id')
        articles = Article.objects.using('read').filter(id=article_id)
        if not articles.exists():
            raise Http404
        article = articles[0]
        self.check_object_permissions(self.request, article)
        return article

    def perform_update(self, instance):
        now = timezone.now()
        instance.is_released = True
        instance.release_at = now
        instance.save(using='write')

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_update(instance)
        return Response({'code': 200, 'msg': '博文发布成功'})
