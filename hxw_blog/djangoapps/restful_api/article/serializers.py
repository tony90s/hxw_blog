from django.conf import settings
from django.utils import timezone

from rest_framework import serializers
from article.models import Article, Comment, CommentReply, Praise


class ArticleSerializer(serializers.ModelSerializer):
    article_id = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    cover_photo = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()
    abstract = serializers.SerializerMethodField()

    def get_article_id(self, article):
        return article.id

    def get_type(self, article):
        return {
            'value': article.type,
            'display_name': article.get_type_display()
        }

    def get_cover_photo(self, article):
        cover_photo = article.cover_photo
        return cover_photo.url if cover_photo.name else ''

    def get_author(self, article):
        article_info = article.get_author_data()
        return article_info

    def get_abstract(self, article):
        return article.content_txt[0:91] + '...'

    class Meta:
        model = Article
        fields = ('article_id', 'title', 'type', 'cover_photo', 'author', 'abstract', 'comment_times', 'praise_times',
                  'release_time', 'page_views')


class PraiseSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    praise_at = serializers.SerializerMethodField()
    article_info = serializers.SerializerMethodField()
    receiver_info = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()

    def get_user(self, praise):
        return praise.get_user_info()

    def get_praise_at(self, praise):
        praise_at = timezone.localtime(praise.praise_at).strftime("%Y-%m-%d %H:%M:%S")
        return praise_at

    def get_article_info(self, praise):
        article_info = praise.get_article_info()
        return article_info

    def get_receiver_info(self, praise):
        receiver_info = praise.get_receiver_info()
        return receiver_info

    def get_content(self, praise):
        comment_content = praise.get_comment_content()
        return comment_content

    class Meta:
        model = Praise
        fields = ('id', 'praise_type', 'user', 'praise_at', 'article_info', 'receiver_info', 'content', 'is_viewed')
