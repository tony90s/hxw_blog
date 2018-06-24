from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.utils import timezone

from rest_framework import serializers, fields
from article.models import Article, Comment, Praise
from restful_api.article.validators import ObjectExistsValidator


class CustomDateTimeField(fields.DateTimeField):
    def to_representation(self, value):
        if not value:
            return None
        value = timezone.localtime(value).strftime("%Y-%m-%d %H:%M:%S")
        return value


class SaveArticleSerializer(serializers.Serializer):
    title = serializers.CharField(required=True, max_length=64)
    type = serializers.ChoiceField(required=True, choices=Article.TYPE_CHOICES)
    content_txt = serializers.CharField(default='', style={'type': 'textarea'})
    content_html = serializers.CharField(required=True, style={'type': 'textarea'})
    is_released = serializers.BooleanField(default=0)

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
        else:
            article.update_at = now
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


class SaveCommentSerializer(serializers.Serializer):
    article_id = serializers.IntegerField(
        required=True,
        validators=[ObjectExistsValidator(model_class=Article, message='所评论的博文不存在，请联系管理员。')]
    )
    receiver_id = serializers.IntegerField(
        required=True,
        validators=[ObjectExistsValidator(model_class=User, message='所回复的童鞋不存在，请联系管理员。')]
    )
    content = serializers.CharField(required=True, max_length=140)

    def create(self, validated_data):
        return Comment.objects.using('write').create(**validated_data)

    def update(self, instance, validated_data):
        return None


class SaveCommentReplySerializer(serializers.Serializer):
    article_id = serializers.IntegerField(
        required=True,
        validators=[ObjectExistsValidator(model_class=Article, message='所评论的博文不存在，请联系管理员。')]
    )
    parent_id = serializers.IntegerField(
        required=True,
        validators=[ObjectExistsValidator(model_class=Comment, message='所回复父级评论不存在，请联系管理员。')]
    )
    be_replied_comment_id = serializers.IntegerField(
        required=True,
        validators=[ObjectExistsValidator(model_class=Comment, message='所回复评论不存在，请联系管理员。')]
    )
    receiver_id = serializers.IntegerField(
        required=True,
        validators=[ObjectExistsValidator(model_class=User, message='所回复的童鞋不存在，请联系管理员。')]
    )
    content = serializers.CharField(required=True, max_length=140)

    def create(self, validated_data):
        return Comment.objects.using('write').create(**validated_data)

    def update(self, instance, validated_data):
        return None


class SavePraiseSerializer(serializers.Serializer):
    praise_type = serializers.ChoiceField(required=True, choices=Praise.TYPE_CHOICES)
    parent_id = serializers.IntegerField(required=True)

    def validate(self, attrs):
        praise_type = attrs.get('praise_type')
        parent_id = attrs.get('parent_id')

        if praise_type == Praise.TYPE.ARTICLE:
            praise_parents = Article.objects.using('read').filter(id=parent_id)
        else:
            praise_parents = Comment.objects.using('read').filter(id=parent_id)

        if not praise_parents.exists():
            raise serializers.ValidationError('所点赞对象不存在')
        praises = Praise.objects.using('read').filter(
            Q(praise_type=praise_type) &
            Q(parent_id=parent_id) &
            Q(user_id=self.context['request'].user.id))
        if praises.exists():
            raise serializers.ValidationError('你已点赞，无需重复点赞')
        return attrs

    def create(self, validated_data):
        return Praise.objects.using('write').create(**validated_data)

    def update(self, instance, validated_data):
        return None


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
        cover_photo = article.article_cover
        return cover_photo

    def get_author(self, article):
        article_info = article.get_author_data()
        return article_info

    def get_abstract(self, article):
        return article.content_txt[0:91] + '...'

    class Meta:
        model = Article
        fields = ('article_id', 'title', 'type', 'cover_photo', 'author', 'abstract', 'comment_times', 'praise_times',
                  'release_time', 'update_time', 'page_views')


class PraiseSerializer(serializers.ModelSerializer):
    praise_id = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    serializer_field_mapping = serializers.ModelSerializer.serializer_field_mapping
    serializer_field_mapping.update({
        models.DateTimeField: CustomDateTimeField
    })

    def get_praise_id(self, praise):
        return praise.id

    def get_user(self, praise):
        return praise.get_user_info()

    class Meta:
        model = Praise
        fields = ('praise_id', 'parent_id', 'praise_type', 'user', 'praise_at')


class UserPraiseSerializer(serializers.ModelSerializer):
    praise_id = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    article_info = serializers.SerializerMethodField()
    receiver_info = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    is_viewed = serializers.SerializerMethodField()

    serializer_field_mapping = serializers.ModelSerializer.serializer_field_mapping
    serializer_field_mapping.update({
        models.DateTimeField: CustomDateTimeField
    })

    def get_praise_id(self, praise):
        return praise.id

    def get_type(self, praise):
        return praise.praise_type

    def get_user(self, praise):
        return praise.get_user_info()

    def get_article_info(self, praise):
        article_info = praise.get_article_info()
        return article_info

    def get_receiver_info(self, praise):
        receiver_info = praise.get_receiver_info()
        return receiver_info

    def get_content(self, praise):
        comment_content = praise.get_comment_content()
        return comment_content

    def get_is_viewed(self, praise):
        return int(praise.is_viewed)

    class Meta:
        model = Praise
        fields = ('praise_id', 'type', 'user', 'praise_at', 'article_info', 'receiver_info', 'content', 'is_viewed')


class CommentReplySerializer(serializers.ModelSerializer):
    comment_id = serializers.SerializerMethodField()
    replier = serializers.SerializerMethodField()
    receiver = serializers.SerializerMethodField()
    reply_at = serializers.SerializerMethodField()

    serializer_field_mapping = serializers.ModelSerializer.serializer_field_mapping
    serializer_field_mapping.update({
        models.DateTimeField: CustomDateTimeField
    })

    def get_comment_id(self, comment):
        return comment.id

    def get_replier(self, comment):
        replier_info = comment.get_commentator_info()
        return replier_info

    def get_receiver(self, comment):
        receiver_info = comment.get_receiver_info()
        return receiver_info

    def get_reply_at(self, comment):
        return timezone.localtime(comment.comment_at).strftime("%Y-%m-%d %H:%M:%S")

    class Meta:
        model = Comment
        fields = ('comment_id', 'parent_id', 'replier', 'receiver', 'reply_at', 'content', 'praise_times')


class UserCommentsSerializer(serializers.ModelSerializer):
    parent_id = serializers.SerializerMethodField()
    comment_id = serializers.SerializerMethodField()
    replier = serializers.SerializerMethodField()
    receiver = serializers.SerializerMethodField()
    article_info = serializers.SerializerMethodField()
    reply_at = serializers.SerializerMethodField()
    is_viewed = serializers.SerializerMethodField()

    serializer_field_mapping = serializers.ModelSerializer.serializer_field_mapping
    serializer_field_mapping.update({
        models.DateTimeField: CustomDateTimeField
    })

    def get_parent_id(self, comment):
        return comment.parent_id if comment.parent_id > 0 else comment.id

    def get_comment_id(self, comment):
        return comment.id

    def get_article_info(self, comment):
        article_info = comment.get_article_info()
        return article_info

    def get_replier(self, comment):
        replier_info = comment.get_commentator_info()
        return replier_info

    def get_receiver(self, comment):
        receiver_info = comment.get_receiver_info()
        return receiver_info

    def get_reply_at(self, comment):
        return timezone.localtime(comment.comment_at).strftime("%Y-%m-%d %H:%M:%S")

    def get_is_viewed(self, comment):
        return int(comment.is_viewed)

    class Meta:
        model = Comment
        fields = ('comment_id', 'parent_id', 'article_info', 'replier', 'receiver', 'reply_at', 'content', 'is_viewed')


class CommentSerializer(serializers.ModelSerializer):
    comment_id = serializers.SerializerMethodField()
    commentator = serializers.SerializerMethodField()
    comment_replies = serializers.SerializerMethodField()

    serializer_field_mapping = serializers.ModelSerializer.serializer_field_mapping
    serializer_field_mapping.update({
        models.DateTimeField: CustomDateTimeField
    })

    def get_comment_id(self, comment):
        return comment.id

    def get_commentator(self, comment):
        commentator_info = comment.get_commentator_info()
        return commentator_info

    def get_comment_replies(self, comment):
        comment_replies = Comment.objects.using('read').filter(parent_id=comment.id).order_by("-id")[:2]
        comment_replies_data = list()
        for comment_reply in comment_replies:
            comment_replies_data.append(comment_reply.render_comment_reply_json())
        return comment_replies_data

    class Meta:
        model = Comment
        fields = ('article_id', 'comment_id', 'commentator', 'comment_at', 'content', 'praise_times', 'replies_count',
                  'comment_replies')
