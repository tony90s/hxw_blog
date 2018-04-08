from django.conf import settings
from django.utils import timezone

from rest_framework import serializers
from article.models import Article, Comment, CommentReply, Praise


class SaveArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ('author_id', 'title', 'type', 'content_txt', 'content_html', 'is_released')

    def create(self, validated_data):
        is_released = validated_data.get('is_released')
        now = timezone.now()

        article = Article()
        article.author_id = validated_data.get('author_id')
        article.title = validated_data.get('title')
        article.type = validated_data.get('type')
        article.content_html = validated_data.get('content_html')
        article.content_txt = validated_data.get('content_txt')
        article.is_released = is_released
        article.created_at = now
        if is_released:
            article.release_at = now
        article.save(using='write')
        return article

    def update(self, instance, validated_data):
        is_released = validated_data.get('is_released')
        now = timezone.now()

        instance.title = validated_data.get('title', instance.title)
        instance.type = validated_data.get('type', instance.type)
        instance.content_html = validated_data.get('content_html', instance.content_html)
        instance.content_txt = validated_data.get('content_txt', instance.content_txt)
        instance.is_released = is_released
        instance.update_at = now
        if is_released:
            instance.release_at = now
        instance.save(using='write')
        return instance


class SaveCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('article_id', 'commentator_id', 'content')

    def create(self, validated_data):
        return Comment.objects.using('write').create(**validated_data)


class SaveCommentReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentReply
        fields = ('comment_id', 'receiver_id', 'replier_id', 'content')

    def create(self, validated_data):
        return CommentReply.objects.using('write').create(**validated_data)


class SavePraiseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Praise
        fields = ('praise_type', 'parent_id', 'user_id')

    def create(self, validated_data):
        return Praise.objects.using('write').create(**validated_data)


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


class CommentReplySerializer(serializers.ModelSerializer):
    comment_reply_id = serializers.SerializerMethodField()
    replier = serializers.SerializerMethodField()
    receiver = serializers.SerializerMethodField()
    reply_at = serializers.SerializerMethodField()

    def get_comment_reply_id(self, comment_reply):
        return comment_reply.id

    def get_replier(self, comment_reply):
        replier_info = comment_reply.get_replier_info()
        return replier_info

    def get_receiver(self, comment_reply):
        receiver_info = comment_reply.get_receiver_info()
        return receiver_info

    def get_reply_at(self, comment_reply):
        reply_at = timezone.localtime(comment_reply.reply_at).strftime("%Y-%m-%d %H:%M:%S")
        return reply_at

    class Meta:
        model = CommentReply
        fields = ('comment_reply_id', 'comment_id', 'replier', 'receiver', 'reply_at', 'content', 'praise_times')


class CommentSerializer(serializers.ModelSerializer):
    comment_id = serializers.SerializerMethodField()
    commentator = serializers.SerializerMethodField()
    comment_at = serializers.SerializerMethodField()
    comment_replies = serializers.SerializerMethodField()

    def get_comment_id(self, comment):
        return comment.id

    def get_commentator(self, comment):
        commentator_info = comment.get_commentator_info()
        return commentator_info

    def get_comment_at(self, comment):
        comment_at = timezone.localtime(comment.comment_at).strftime("%Y-%m-%d %H:%M:%S")
        return comment_at

    def get_comment_replies(self, comment):
        comment_replies = CommentReply.objects.using('read').filter(comment_id=comment.id).order_by("-id")
        comment_replies_data = list()
        for comment_reply in comment_replies:
            comment_replies_data.append(comment_reply.render_json())
        return comment_replies_data

    class Meta:
        model = Comment
        fields = ('article_id', 'comment_id', 'commentator', 'comment_at', 'content', 'praise_times', 'comment_replies')
