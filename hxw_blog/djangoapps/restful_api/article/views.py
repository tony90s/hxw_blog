import logging
import re
from datetime import timedelta

from article.models import (
    Article,
    Comment,
    Praise,
    get_user_be_praised,
    get_user_received_comments
)
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import get_object_or_404, get_list_or_404
from django.utils import timezone
from rest_framework import serializers, generics, permissions
from rest_framework.response import Response
from restful_api.article.forms import (
    ArticleListForm,
    UserPraiseListForm,
    CommonPraiseForm,
    UpdateIsViewedStatusForm,
    CheckArticleIdForm,
    ArticleCommentsForm,
    CheckCommentIdForm,
    CommentRepliesForm,
    UserCommentListForm,
    GeneralUserIdForm
)
from restful_api.article.permissions import (
    IsAuthorOrReadOnly,
    IsCommentatorOrReadOnly,
    IsPraiseOwnerOrReadOnly
)
from restful_api.article.serializers import (
    ArticleSerializer,
    CommentSerializer,
    CommentReplySerializer,
    UserCommentsSerializer,
    PraiseSerializer,
    UserPraiseSerializer,
    SaveArticleSerializer,
    SaveCommentSerializer,
    SaveCommentReplySerializer,
    SavePraiseSerializer
)
from utils.rest_framework import generics as extra_generics
from utils.rest_framework.authentication import (
    OAuth2AuthenticationAllowInactiveUser,
    SessionAuthenticationAllowInactiveUser
)
from utils.rest_framework.pagination import SmallResultsSetPagination

reg_number = re.compile('^\d+$')
logger = logging.getLogger('api.article')


class CommonListMixin(object):
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        count = len(data)
        context = {
            'results': data[:self.page_size],
            'count': count,
            'has_more': count > self.page_size
        }
        response = Response(context)
        self.clean_cache()
        return response


class CustomListAPIView(CommonListMixin, generics.GenericAPIView):
    """
    Custom concrete view for listing a queryset.
    """

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class CreateArticleView(generics.CreateAPIView):
    serializer_class = SaveArticleSerializer
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser)
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
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser, IsAuthorOrReadOnly,)

    def get_object(self):
        article_id = self.kwargs.get('article_id')
        article = get_object_or_404(Article, id=int(article_id))
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

        praises = Praise.objects.using('write').filter(
            (Q(praise_type=Praise.TYPE.ARTICLE) & Q(parent_id=article_id)) | (
                Q(praise_type=Praise.TYPE.COMMENT) & Q(parent_id__in=comments_id)))
        praises.delete()
        comments.delete()
        instance.delete()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'code': 200, 'msg': '删除博文成功'})


class ArticleList(CustomListAPIView):
    """
    List all articles
    """

    # pagination_class = SmallResultsSetPagination
    serializer_class = ArticleSerializer
    page_size = settings.PAGINATORS['SMALL_PAGE_SIZE']

    def get_queryset(self):
        form = ArticleListForm(self.request.query_params)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        article_type = form.cleaned_data.get('article_type') or 0
        is_released = form.cleaned_data.get('is_released')
        author_id = form.cleaned_data.get('author_id') or 0
        key_word = form.cleaned_data.get('key_word') or ''
        earliest_time = form.cleaned_data.get('earliest_time')
        last_time = form.cleaned_data.get('last_time')

        query_condition = Q(is_released=is_released)
        if author_id > 0:
            query_condition &= Q(author_id=author_id)
        if article_type > 0:
            query_condition &= Q(type=article_type)
        if key_word:
            query_condition &= (Q(title__icontains=key_word) | Q(content_txt__icontains=key_word))

        if is_released:
            order_field_names = ('-release_at',)
            if earliest_time and last_time:
                query_condition &= (
                    Q(release_at__gt=(earliest_time + timedelta(seconds=1))) | Q(release_at__lt=last_time))
            if earliest_time and not last_time:
                query_condition &= Q(release_at__gt=(earliest_time + timedelta(seconds=1)))
            if not earliest_time and last_time:
                query_condition &= Q(release_at__lt=last_time)
        else:
            order_field_names = ('-update_at',)
            if earliest_time and last_time:
                query_condition &= (Q(update_at__gt=(earliest_time + timedelta(seconds=1))) | Q(
                    update_at__lt=last_time))
            if earliest_time and not last_time:
                query_condition &= Q(update_at__gt=(earliest_time + timedelta(seconds=1)))
            if not earliest_time and last_time:
                query_condition &= Q(update_at__lt=last_time)
        articles = Article.objects.using('read').filter(query_condition).order_by(*order_field_names)
        return articles

    def clean_cache(self):
        Article._Article__user_cache = dict()


class CommentList(CustomListAPIView):
    """
    List all comment
    """

    # pagination_class = SmallResultsSetPagination
    serializer_class = CommentSerializer
    page_size = settings.PAGINATORS['SMALL_PAGE_SIZE']

    def get_queryset(self):
        form = ArticleCommentsForm(self.request.query_params)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        article_id = form.cleaned_data.get('article_id')
        min_primary_id = form.cleaned_data.get('min_primary_id') or 0
        max_primary_id = form.cleaned_data.get('max_primary_id') or 0

        article = get_object_or_404(Article, id=article_id)

        query_condition = Q(article_id=article_id, parent_id=0)
        if min_primary_id and max_primary_id:
            query_condition &= (Q(id__gt=max_primary_id) | Q(id__lt=min_primary_id))
        if max_primary_id and not min_primary_id:
            query_condition &= Q(id__gt=max_primary_id)
        if not max_primary_id and min_primary_id:
            query_condition &= Q(id__lt=min_primary_id)
        comments = Comment.objects.using('read').filter(query_condition).order_by('-id')
        return comments

    def clean_cache(self):
        Comment._Comment__user_cache = dict()
        Comment._Comment__article_info_cache = dict()


class CommentReplyList(CustomListAPIView):
    """
    List all replies of a comment
    """

    # pagination_class = SmallResultsSetPagination
    serializer_class = CommentReplySerializer
    page_size = settings.PAGINATORS['SMALL_PAGE_SIZE']

    def get_queryset(self):
        form = CommentRepliesForm(self.request.query_params)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        parent_id = form.cleaned_data.get('parent_id')
        min_primary_id = form.cleaned_data.get('min_primary_id')
        max_primary_id = form.cleaned_data.get('max_primary_id')

        query_condition = Q(parent_id=parent_id)
        if min_primary_id and max_primary_id:
            query_condition &= (Q(id__gt=max_primary_id) | Q(id__lt=min_primary_id))
        if max_primary_id and not min_primary_id:
            query_condition &= Q(id__gt=max_primary_id)
        if not max_primary_id and min_primary_id:
            query_condition &= Q(id__lt=min_primary_id)

        comment_replies = Comment.objects.using('read').filter(query_condition).order_by('-id')
        return comment_replies

    def clean_cache(self):
        Comment._Comment__user_cache = dict()
        Comment._Comment__article_info_cache = dict()


class UserCommentList(CustomListAPIView):
    """
    List all comment of user.
    """

    # pagination_class = SmallResultsSetPagination
    serializer_class = UserCommentsSerializer
    page_size = settings.PAGINATORS['SMALL_PAGE_SIZE']

    def get_queryset(self):
        form = UserCommentListForm(self.request.query_params)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        user_id = form.cleaned_data.get('user_id')
        comment_type = form.cleaned_data.get('comment_type')
        min_primary_id = form.cleaned_data.get('min_primary_id')
        max_primary_id = form.cleaned_data.get('max_primary_id')

        query_condition = Q()

        if comment_type == 0:
            query_condition &= Q(receiver_id=user_id)
        else:
            query_condition &= Q(commentator_id=user_id)
        if min_primary_id and max_primary_id:
            query_condition &= (Q(id__gt=max_primary_id) | Q(id__lt=min_primary_id))
        if max_primary_id and not min_primary_id:
            query_condition &= Q(id__gt=max_primary_id)
        if not max_primary_id and min_primary_id:
            query_condition &= Q(id__lt=min_primary_id)

        comments = Comment.objects.using('read').filter(query_condition).order_by('-id')
        return comments

    def clean_cache(self):
        Comment._Comment__user_cache = dict()
        Comment._Comment__article_info_cache = dict()


class PraiseList(generics.ListAPIView):
    """
    List all praises.
    """

    pagination_class = SmallResultsSetPagination
    serializer_class = PraiseSerializer

    def get_queryset(self):
        form = CommonPraiseForm(self.request.query_params)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        praise_type = form.cleaned_data.get('praise_type')
        parent_id = form.cleaned_data.get('parent_id')
        praises = Praise.objects.using('read').filter(praise_type=praise_type, parent_id=parent_id).order_by('-id')
        return praises

    def clean_cache(self):
        Praise._Praise__user_cache = dict()

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


class UserPraiseList(CustomListAPIView):
    """
    List all user be_praises.
    """

    # pagination_class = SmallResultsSetPagination
    serializer_class = UserPraiseSerializer
    page_size = settings.PAGINATORS['SMALL_PAGE_SIZE']

    def get_queryset(self):
        form = UserPraiseListForm(self.request.query_params)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        user_id = form.cleaned_data.get('user_id')
        min_primary_id = form.cleaned_data.get('min_primary_id')
        max_primary_id = form.cleaned_data.get('max_primary_id')

        query_condition = Q()

        articles = Article.objects.using('read').filter(author_id=user_id)
        article_ids = list(articles.values_list('id', flat=True))

        comments = Comment.objects.using('read').filter(commentator_id=user_id)
        comment_ids = list(comments.values_list('id', flat=True))

        query_condition &= (Q(praise_type=Praise.TYPE.ARTICLE, parent_id__in=article_ids) | Q(
            praise_type=Praise.TYPE.COMMENT, parent_id__in=comment_ids))

        if min_primary_id and max_primary_id:
            query_condition &= (Q(id__gt=max_primary_id) | Q(id__lt=min_primary_id))
        if max_primary_id and not min_primary_id:
            query_condition &= Q(id__gt=max_primary_id)
        if not max_primary_id and min_primary_id:
            query_condition &= Q(id__lt=min_primary_id)

        praises = Praise.objects.using('read').filter(query_condition).order_by('-id')
        return praises

    def clean_cache(self):
        Comment._Comment__user_cache = dict()
        Comment._Comment__article_info_cache = dict()
        Praise._Praise__user_cache = dict()
        Praise._Praise__article_info_cache = dict()


class SaveCommentView(generics.CreateAPIView):
    serializer_class = SaveCommentSerializer
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser)
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
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser)
    permission_classes = (permissions.IsAuthenticated, IsCommentatorOrReadOnly,)

    def get_object(self):
        form = CheckCommentIdForm(self.request.data)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        comment_id = form.cleaned_data.get('comment_id')
        comment = get_object_or_404(Comment, id=comment_id)
        self.check_object_permissions(self.request, comment)
        return comment

    def perform_destroy(self, instance):
        comment_id = instance.id
        comment_replies = Comment.objects.using('write').filter(parent_id=comment_id)
        comment_replies_id = list(comment_replies.values_list('id', flat=True))
        praises = Praise.objects.using('write').filter(
            Q(praise_type=Praise.TYPE.COMMENT, parent_id__in=[comment_id] + comment_replies_id))
        praises.delete()
        comment_replies.delete()
        instance.delete()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'code': 200, 'msg': '删除评论成功'})


class SaveCommentReplyView(generics.CreateAPIView):
    serializer_class = SaveCommentReplySerializer
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser)
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        serializer.save(commentator_id=self.request.user.id)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return_context = {
            'code': 200,
            'msg': '回复成功',
            'data': serializer.instance.render_comment_reply_json()
        }
        return Response(return_context)


class SavePraiseView(generics.CreateAPIView):
    serializer_class = SavePraiseSerializer
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser)
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
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser)
    permission_classes = (permissions.IsAuthenticated, IsPraiseOwnerOrReadOnly,)

    def get_object(self):
        form = CommonPraiseForm(self.request.data)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        praise_type = form.cleaned_data.get('praise_type')
        parent_id = form.cleaned_data.get('parent_id')
        user_id = self.request.user.id
        praise = get_object_or_404(Praise, praise_type=praise_type, parent_id=parent_id, user_id=user_id)
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
            model_class = Comment
        else:
            model_class = Praise
        instance = get_object_or_404(model_class, id=parent_id)
        return instance

    def perform_update(self, instance):
        instance.is_viewed = 1
        instance.save(using='write')

    def update(self, request, *args, **kwargs):
        instance = self.get_queryset()
        self.perform_update(instance)
        return Response({'code': 200, 'msg': '更新成功'})


class UpdateArticleReleaseStatusView(generics.UpdateAPIView):
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser, IsAuthorOrReadOnly,)

    def get_object(self):
        form = CheckArticleIdForm(self.request.data)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        article_id = form.cleaned_data.get('article_id')
        article = get_object_or_404(Article, id=article_id)
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


class MessagesNotViewedCountView(generics.GenericAPIView):
    def get_cleaned_data(self):
        form = GeneralUserIdForm(self.request.query_params)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        return self.request.query_params

    def get(self, request, *args, **kwargs):
        cleaned_data = self.get_cleaned_data()
        user_id = cleaned_data['user_id']
        comments = get_user_received_comments(user_id)
        not_viewed_comment_count = comments.filter(is_viewed=0).count()
        praises = get_user_be_praised(user_id)
        not_viewed_praises_count = praises.filter(is_viewed=0).count()
        return Response({
            'code': 200,
            'msg': '查询成功',
            'data': {
                'not_viewed_comment_count': not_viewed_comment_count,
                'not_viewed_praises_count': not_viewed_praises_count
            }
        })
