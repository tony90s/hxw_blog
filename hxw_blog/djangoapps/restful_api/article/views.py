from django.db.models import Q

from rest_framework import generics
from article.models import Article, Comment, CommentReply, Praise, get_user_be_praised
from restful_api.article.serializers import ArticleSerializer, PraiseSerializer
from utils.paginators import SmallResultsSetPagination


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
