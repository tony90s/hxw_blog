import re

from django.db.models import Q
from django.http import QueryDict
from django.utils import timezone

from rest_framework import generics, permissions
from rest_framework.response import Response
from article.models import Article, Comment, CommentReply, Praise, get_user_be_praised
from restful_api.article.serializers import ArticleSerializer, PraiseSerializer
from utils.paginators import SmallResultsSetPagination

reg_number = re.compile('^\d+$')


class ArticleList(generics.ListAPIView):
    """
    List all articles
    """

    pagination_class = SmallResultsSetPagination
    serializer_class = ArticleSerializer

    def get_queryset(self):
        article_type = self.request.query_params.get('article_type', '0')
        is_released = self.request.query_params.get('is_released', '1')
        author_id = self.request.query_params.get('author_id', '0')

        article_type = int(article_type)
        author_id = int(author_id)
        is_released = int(is_released)

        query_condition = Q(is_released=is_released)
        if article_type > 0:
            query_condition &= Q(type=article_type)

        if author_id > 0:
            query_condition &= Q(author_id=author_id)

        articles = Article.objects.using('read').filter(query_condition).order_by('-id')
        return articles


class PraiseList(generics.ListAPIView):
    """
    List all user be_praises.
    """

    pagination_class = SmallResultsSetPagination
    serializer_class = PraiseSerializer

    def get_queryset(self):
        user_id = self.request.GET.get('user_id')
        return get_user_be_praised(user_id)


class DeleteArticleView(generics.DestroyAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def clean(self):
        query_data = QueryDict(self.request.body)
        article_id = query_data.get('article_id', '')
        if not article_id:
            return Response({'code': 400, 'msg': '参数缺失'})
        if not reg_number.match(article_id):
            return Response({'code': 400, 'msg': '参数有误'})
        self.cleaned_data = query_data
        return None

    def get_object(self):
        article_id = self.cleaned_data.get('article_id')
        articles = Article.objects.using('read').filter(id=int(article_id))
        if not articles.exists():
            return Response({'code': 404, 'msg': '所要删除的博文不存在'})
        return articles[0]

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
        response = self.clean()
        if response is not None:
            return response
        user = request.user
        instance = self.get_object()
        if user.id != instance.author_id:
            return Response({'code': 403, 'msg': '不能删除其它童鞋的博文'})
        self.perform_destroy(instance)
        return Response({'code': 200, 'msg': '删除博文成功'})


class DeleteCommentView(generics.DestroyAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def clean(self):
        query_data = QueryDict(self.request.body)
        comment_id = query_data.get('comment_id', '')
        if not comment_id:
            return Response({'code': 400, 'msg': '参数缺失'})
        if not reg_number.match(comment_id):
            return Response({'code': 400, 'msg': '参数有误'})
        self.cleaned_data = query_data
        return None

    def get_object(self):
        comment_id = self.cleaned_data.get('comment_id')
        comments = Comment.objects.using('read').filter(id=int(comment_id))
        if not comments.exists():
            return Response({'code': 404, 'msg': '所要删除的评论不存在'})
        return comments[0]

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
        response = self.clean()
        if response is not None:
            return response
        user = request.user
        instance = self.get_object()
        if user.id != instance.commentator_id:
            return Response({'code': 403, 'msg': '不能删除其它童鞋的评论'})
        self.perform_destroy(instance)
        return Response({'code': 200, 'msg': '删除评论成功'})


class DeleteCommentReplyView(generics.DestroyAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def clean(self):
        query_data = QueryDict(self.request.body)
        comment_reply_id = query_data.get('comment_reply_id', '')
        if not comment_reply_id:
            return Response({'code': 400, 'msg': '参数缺失'})
        if not reg_number.match(comment_reply_id):
            return Response({'code': 400, 'msg': '参数有误'})
        self.cleaned_data = query_data
        return None

    def get_object(self):
        comment_reply_id = self.cleaned_data.get('comment_reply_id')
        comment_replies = CommentReply.objects.using('read').filter(id=int(comment_reply_id))
        if not comment_replies.exists():
            return Response({'code': 404, 'msg': '所要删除的回复不存在'})
        return comment_replies[0]

    def perform_destroy(self, instance):
        praises = Praise.objects.using('write').filter(
            Q(praise_type=Praise.TYPE.COMMENT_REPLY) & Q(parent_id=instance.id))
        praises.delete()
        instance.delete()

    def destroy(self, request, *args, **kwargs):
        response = self.clean()
        if response is not None:
            return response
        user = request.user
        instance = self.get_object()
        if user.id != instance.replier_id:
            return Response({'code': 403, 'msg': '不能删除其它童鞋的回复'})
        self.perform_destroy(instance)
        return Response({'code': 200, 'msg': '删除回复成功'})


class CancelPraiseView(generics.DestroyAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def clean(self):
        query_data = QueryDict(self.request.body)
        praise_type = query_data.get('praise_type', '')
        parent_id = query_data.get('parent_id', '')

        if not praise_type or not parent_id:
            return Response({'code': 400, 'msg': '参数缺失'})
        if not reg_number.match(praise_type) or not reg_number.match(parent_id):
            return Response({'code': 400, 'msg': '参数有误'})
        if int(praise_type) not in [value for value, name in Praise.TYPE_CHOICES]:
            return Response({'code': 400, 'msg': '参数有误'})
        self.cleaned_data = query_data
        return None

    def get_object(self):
        praise_type = int(self.cleaned_data.get('praise_type'))
        parent_id = int(self.cleaned_data.get('parent_id'))
        user_id = self.request.user.id

        praises = Praise.objects.using('read').filter(Q(praise_type=praise_type) &
                                                       Q(parent_id=parent_id) & Q(user_id=user_id))
        if not praises.exists():
            return Response({'code': 400, 'msg': '您尚未点赞，不能取消赞'})
        return praises[0]

    def destroy(self, request, *args, **kwargs):
        response = self.clean()
        if response is not None:
            return response
        user = request.user
        instance = self.get_object()
        if user.id != instance.user_id:
            return Response({'code': 403, 'msg': '不能取消其它童鞋的赞'})
        self.perform_destroy(instance)
        return Response({'code': 200, 'msg': '取消点赞成功'})


class UpdateIsViewedStatusView(generics.UpdateAPIView):
    def clean(self):
        query_data = QueryDict(self.request.body)
        object_type = query_data.get('object_type')  # 1 comment  2 comment_reply   3 praise
        parent_id = query_data.get('parent_id')

        if not object_type or not parent_id:
            return Response({'code': 400, 'msg': '参数缺失'})

        if not reg_number.match(object_type) or not reg_number.match(parent_id):
            return Response({'code': 400, 'msg': '参数有误'})

        if int(object_type) not in [1, 2, 3]:
            return Response({'code': 400, 'msg': '参数有误'})
        self.cleaned_data = query_data
        return None

    def get_queryset(self):
        object_type = int(self.cleaned_data.get('object_type'))
        parent_id = int(self.cleaned_data.get('parent_id'))

        if object_type == 1:
            instances = Comment.objects.using('write').filter(id=parent_id)
        elif object_type == 2:
            instances = CommentReply.objects.using('write').filter(id=parent_id)
        else:
            instances = Praise.objects.using('write').filter(id=parent_id)
        if not instances.exists():
            return Response({'code': 404, 'msg': '对象不存在'})
        return instances

    def perform_update(self, instances):
        instances.update(is_viewed=1)

    def update(self, request, *args, **kwargs):
        response = self.clean()
        if response is not None:
            return response
        instances = self.get_queryset()
        self.perform_update(instances)
        return Response({'code': 200, 'msg': '更新成功'})


class UpdateArticleReleaseStatusView(generics.UpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def clean(self):
        query_data = QueryDict(self.request.body)
        article_id = query_data.get('article_id')
        if not article_id:
            return Response({'code': 400, 'msg': '参数缺失'})
        if not reg_number.match(article_id):
            return Response({'code': 400, 'msg': '参数有误'})
        self.cleaned_data = query_data
        return None

    def get_queryset(self):
        article_id = int(self.cleaned_data.get('article_id'))
        articles = Article.objects.using('read').filter(id=article_id)
        if not articles.exists():
            return Response({'code': 404, 'msg': '博文不存在'})
        return articles

    def perform_update(self, instances):
        now = timezone.now()
        instances.update(is_released=True, release_at=now)

    def update(self, request, *args, **kwargs):
        response = self.clean()
        if response is not None:
            return response
        user = request.user
        instances = self.get_queryset()
        if user.id != instances[0].author_id:
            return Response({'code': 403, 'msg': '不能发布其它童鞋的博文'})
        self.perform_update(instances)
        return Response({'code': 200, 'msg': '博文发布成功'})
