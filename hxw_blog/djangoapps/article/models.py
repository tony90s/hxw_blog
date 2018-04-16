import re

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class Article(models.Model):
    class TYPE:
        PYTHON = 1
        LINUX = 2
        DJANGO = 3
        FRONT_END = 4
        ESSAY = 5
        HISTORY = 6
        DIGITAL_INFO = 7
        READING = 8
        QUESTIONS_AND_ANSWERS = 9
        TOPIC = 10

    TYPE_CHOICES = (
        (TYPE.PYTHON, 'Python'),
        (TYPE.LINUX, 'Linux'),
        (TYPE.DJANGO, 'Django'),
        (TYPE.FRONT_END, '前端技术'),
        (TYPE.ESSAY, '随笔'),
        (TYPE.HISTORY, '历史'),
        (TYPE.DIGITAL_INFO, '数码资讯'),
        (TYPE.READING, '读书'),
        (TYPE.QUESTIONS_AND_ANSWERS, '问答'),
        (TYPE.TOPIC, '话题')
    )
    author_id = models.IntegerField(db_index=True, verbose_name='作者', default=0)
    title = models.CharField(max_length=64, default='', verbose_name='标题')
    content_txt = models.TextField(default='', verbose_name='纯文本内容')
    content_html = models.TextField(default='', verbose_name='html内容')
    type = models.IntegerField(choices=TYPE_CHOICES, default=TYPE.PYTHON, verbose_name='类别')
    cover_photo = models.ImageField(upload_to='article/cover', blank=True, null=True, verbose_name='封面图片')
    created_at = models.DateTimeField(auto_now_add=timezone.now, verbose_name='创建时间')
    update_at = models.DateTimeField(blank=True, null=True, verbose_name='更新时间')
    release_at = models.DateTimeField(db_index=True, blank=True, null=True, verbose_name='发布时间')
    is_released = models.BooleanField(default=False, verbose_name='是否发布')
    page_views = models.IntegerField(default=0, verbose_name='浏览量')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _('article')
        verbose_name_plural = _('articles')

    @property
    def release_time(self):
        return timezone.localtime(self.release_at).strftime("%Y-%m-%d %H:%M:%S")

    @property
    def update_time(self):
        if self.update_at:
            return timezone.localtime(self.update_at).strftime("%Y-%m-%d %H:%M:%S")
        else:
            return timezone.localtime(self.created_at).strftime("%Y-%m-%d %H:%M:%S")

    @property
    def word_count(self):
        return len(self.content_txt)

    @staticmethod
    def get_type_name(value):
        type_dict = dict(Article.TYPE_CHOICES)
        return type_dict[value] if value in type_dict else ''

    def get_author_data(self):
        author = User.objects.using('read').get(id=self.author_id)
        author_data = {
            'user_id': author.id,
            'username': author.username if len(author.username) <= 10 else (author.username[:10] + '...'),
            'avatar': author.profile.avatar.url
        }
        return author_data

    def get_comments_json(self):
        page_size = settings.DEFAULT_PAGE_SIZE
        comments = Comment.objects.using('read').filter(Q(article_id=self.id)).order_by("-id")[:page_size]
        comments_data = list()
        for comment in comments:
            comments_data.append(comment.render_json())
        return comments_data

    @property
    def comment_times(self):
        comments = Comment.objects.using('read').filter(Q(article_id=self.id))
        comments_count = comments.count()
        # comments_id = [comment.id for comment in comments]
        # comment_replies = CommentReply.objects.using('read').filter(Q(comment_id__in=comments_id))
        # comments_count += comment_replies.count()
        return comments_count

    @property
    def praise_times(self):
        praises = Praise.objects.using('read').filter(Q(praise_type=Praise.TYPE.ARTICLE) & Q(parent_id=self.id))
        return praises.count()

    @property
    def article_cover(self):
        img_pattern = '<img[^>]+src="([^"]*)"'
        covers = re.findall(img_pattern, self.content_html, re.M)
        return covers[0] if covers else ''

    def render_json(self):
        context = dict()
        context['article_id'] = self.id
        context['title'] = self.title
        context['type'] = {
            'value': self.type,
            'display_name': self.get_type_display()
        }
        context['cover_photo'] = self.article_cover
        context['content_html'] = self.content_html
        context['author'] = self.get_author_data()
        context['comment_times'] = self.comment_times
        context['praise_times'] = self.praise_times
        # context['comments'] = self.get_comments_json()
        context['word_count'] = self.word_count
        context['release_time'] = self.release_time
        context['update_time'] = self.update_time
        context['page_views'] = self.page_views
        return context

    def get_summarization(self):
        context = dict()
        context['article_id'] = self.id
        context['title'] = self.title
        context['type'] = {
            'value': self.type,
            'display_name': self.get_type_display()
        }
        context['cover_photo'] = self.article_cover
        context['author'] = self.get_author_data()
        context['abstract'] = self.content_txt[0:91] + '...'
        context['comment_times'] = self.comment_times
        context['praise_times'] = self.praise_times
        context['release_time'] = self.release_time
        context['update_time'] = self.update_time
        context['page_views'] = self.page_views
        return context

    def get_brief(self):
        context = dict()
        context['article_id'] = self.id
        context['title'] = self.title
        context['type'] = {
            'value': self.type,
            'display_name': self.get_type_display()
        }
        context['cover_photo'] = self.article_cover
        # context['author'] = self.get_author_data()
        context['abstract'] = self.content_txt[0:76] + '...'
        return context


def get_user_articles(user_id):
    articles = Article.objects.using('read').filter(author_id=user_id).order_by('-id')
    articles_summarization = [article.get_summarization() for article in articles]
    return articles_summarization


class Comment(models.Model):
    article_id = models.IntegerField(db_index=True, verbose_name='博文', default=0)
    commentator_id = models.IntegerField(db_index=True, verbose_name='评论人', default=0)
    comment_at = models.DateTimeField(auto_now_add=timezone.now, verbose_name='评论时间')
    content = models.CharField(max_length=140, default='', verbose_name='评论内容')
    is_viewed = models.BooleanField(default=0, verbose_name='是否已查看')
    __user_cache = dict()
    __article_info_cache = dict()

    def __str__(self):
        return '%s %s' % (self.article.title, self.content[0:10])

    class Meta:
        verbose_name = _('comment')
        verbose_name_plural = _('comments')

    @property
    def praise_times(self):
        praises = Praise.objects.using('read').filter(Q(praise_type=Praise.TYPE.COMMENT) & Q(parent_id=self.id))
        return praises.count()

    @property
    def unified_reply_at(self):
        return timezone.localtime(self.comment_at).strftime("%Y-%m-%d %H:%M:%S")

    def get_commentator_info(self):
        if self.commentator_id in self.__user_cache:
            return self.__user_cache[self.commentator_id]
        commentator = User.objects.using('read').get(id=self.commentator_id)
        commentator_info = {
            'user_id': commentator.id,
            'username': commentator.username if len(commentator.username) <= 10 else (commentator.username[:10] + '...'),
            'avatar': commentator.profile.avatar.url
        }
        self.__user_cache.update({self.commentator_id: commentator_info})
        return commentator_info

    def render_json(self):
        context = dict()
        context['article_id'] = self.article_id
        context['comment_id'] = self.id
        context['commentator'] = self.get_commentator_info()
        context['comment_at'] = timezone.localtime(self.comment_at).strftime("%Y-%m-%d %H:%M:%S")
        context['content'] = self.content

        comment_replies = CommentReply.objects.using('read').filter(Q(comment_id=self.id)).order_by("-id")
        comment_replies_data = list()
        for comment_reply in comment_replies:
            comment_replies_data.append(comment_reply.render_json())
        context['comment_replies'] = comment_replies_data
        context['praise_times'] = self.praise_times

        return context

    def get_article_author_info(self):
        article = Article.objects.using('read').get(id=self.article_id)
        return article.get_author_data()

    def get_article_author_id(self):
        article = Article.objects.using('read').get(id=self.article_id)
        return article.author_id

    def get_article_info(self):
        if self.article_id in self.__article_info_cache:
            return self.__article_info_cache[self.article_id]
        article = Article.objects.using('read').get(id=self.article_id)
        article_info = article.get_brief()
        self.__article_info_cache.update({self.article_id: article_info})
        return article_info

    def get_unified_comment_info(self):
        context = dict()
        context['comment_id'] = self.id
        context['comment_reply_id'] = 0
        context['article_info'] = self.get_article_info()
        context['replier'] = self.get_commentator_info()
        context['receiver'] = {
            'user_id': 0,
            'username': '',
            'avatar': ''
        }
        context['reply_at'] = self.unified_reply_at
        context['content'] = self.content
        context['is_viewed'] = int(self.is_viewed)

        return context


def get_user_article_comments(user_id):
    articles = Article.objects.using('read').filter(author_id=user_id)
    article_ids = list(articles.values_list('id', flat=True))
    comments = Comment.objects.using('read').filter(article_id__in=article_ids).order_by('-id')
    return comments


def get_user_comments(user_id):
    comments = Comment.objects.using('read').filter(commentator_id=user_id).order_by('-id')
    return comments


class CommentReply(models.Model):
    comment_id = models.IntegerField(db_index=True, verbose_name='所属评论', default=0)
    replier_id = models.IntegerField(db_index=True, verbose_name='回复人', default=0)
    receiver_id = models.IntegerField(db_index=True, verbose_name='接受者', default=0)
    reply_at = models.DateTimeField(auto_now_add=timezone.now, verbose_name='回复时间')
    content = models.CharField(max_length=140, default='', verbose_name='回复内容')
    is_viewed = models.BooleanField(default=0, verbose_name='是否已查看')
    __user_cache = dict()
    __article_info_cache = dict()

    class Meta:
        verbose_name = _('comment_reply')
        verbose_name_plural = _('comment_replies')

    @property
    def praise_times(self):
        praises = Praise.objects.using('read').filter(Q(praise_type=Praise.TYPE.COMMENT_REPLY) & Q(parent_id=self.id))
        return praises.count()

    @property
    def unified_reply_at(self):
        return timezone.localtime(self.reply_at).strftime("%Y-%m-%d %H:%M:%S")

    def get_replier_info(self):
        if self.replier_id in self.__user_cache:
            return self.__user_cache[self.replier_id]
        replier = User.objects.using('read').get(id=self.replier_id)
        replier_data = {
            'user_id': replier.id,
            'username': replier.username if len(replier.username) <= 10 else (replier.username[:10] + '...'),
            'avatar': replier.profile.avatar.url
        }
        self.__user_cache.update({self.replier_id: replier_data})
        return replier_data

    def get_receiver_info(self):
        if self.receiver_id in self.__user_cache:
            return self.__user_cache[self.receiver_id]
        receiver = User.objects.using('read').get(id=self.receiver_id)
        receiver_data = {
            'user_id': receiver.id,
            'username': receiver.username if len(receiver.username) <= 10 else (receiver.username[:10] + '...'),
            'avatar': receiver.profile.avatar.url
        }
        self.__user_cache.update({self.receiver_id: receiver_data})
        return receiver_data

    def get_article_info(self):
        comment = Comment.objects.using('read').get(id=self.comment_id)
        article_id = comment.article_id
        if article_id in self.__article_info_cache:
            return self.__article_info_cache[article_id]
        article = Article.objects.using('read').get(id=article_id)
        article_info = article.get_brief()
        self.__article_info_cache.update({article_id: article_info})
        return article_info

    def render_json(self):
        context = dict()
        context['comment_reply_id'] = self.id
        context['comment_id'] = self.comment_id
        context['replier'] = self.get_replier_info()
        context['receiver'] = self.get_receiver_info()
        context['reply_at'] = timezone.localtime(self.reply_at).strftime("%Y-%m-%d %H:%M:%S")
        context['content'] = self.content
        context['praise_times'] = self.praise_times
        return context

    def get_unified_comment_info(self):
        context = dict()
        context['comment_id'] = self.comment_id
        context['comment_reply_id'] = self.id
        context['article_info'] = self.get_article_info()
        context['replier'] = self.get_replier_info()
        context['receiver'] = self.get_receiver_info()
        context['reply_at'] = self.unified_reply_at
        context['content'] = self.content
        context['is_viewed'] = int(self.is_viewed)
        return context


class Praise(models.Model):
    class TYPE:
        ARTICLE = 1
        COMMENT = 2
        COMMENT_REPLY = 3

    TYPE_CHOICES = (
        (TYPE.ARTICLE, '博文'),
        (TYPE.COMMENT, '评论'),
        (TYPE.COMMENT_REPLY, '评论回复')
    )
    praise_type = models.IntegerField(choices=TYPE_CHOICES, default=TYPE.ARTICLE, verbose_name='点赞类型')
    parent_id = models.IntegerField(verbose_name='点赞对象id', default=0)
    user_id = models.IntegerField(db_index=True, verbose_name='点赞人', default=0)
    praise_at = models.DateTimeField(auto_now_add=timezone.now, verbose_name='点赞时间')
    is_viewed = models.BooleanField(default=0, verbose_name='是否已查看')
    __user_cache = dict()
    __article_info_cache = dict()

    class Meta:
        verbose_name = _('praise')
        verbose_name_plural = _('praises')
        index_together = [('praise_type', 'parent_id')]

    def get_user_info(self):
        if self.user_id in self.__user_cache:
            return self.__user_cache[self.user_id]
        user = User.objects.using('read').get(id=self.user_id)
        user_data = {
            'user_id': user.id,
            'username': user.username if len(user.username) <= 10 else (user.username[:10] + '...'),
            'avatar': user.profile.avatar.url
        }
        self.__user_cache.update({self.user_id: user_data})
        return user_data

    def get_article_info(self):
        praise_type = self.praise_type
        parent_id = self.parent_id
        if praise_type == self.TYPE.ARTICLE:
            article_id = parent_id
        elif praise_type == self.TYPE.COMMENT:
            comment = Comment.objects.using('read').get(id=parent_id)
            article_id = comment.article_id
        else:
            comment_reply = CommentReply.objects.using('read').get(id=parent_id)
            comment_id = comment_reply.comment_id
            comment = Comment.objects.using('read').get(id=comment_id)
            article_id = comment.article_id

        if article_id in self.__article_info_cache:
            return self.__article_info_cache[article_id]
        article = Article.objects.using('read').get(id=article_id)
        article_info = article.get_brief()
        self.__article_info_cache.update({article_id: article_info})
        return article_info

    def get_comment_content(self):
        praise_type = self.praise_type
        parent_id = self.parent_id
        if praise_type == self.TYPE.ARTICLE:
            content = ''
        elif praise_type == self.TYPE.COMMENT:
            comment = Comment.objects.using('read').get(id=parent_id)
            content = comment.content
        else:
            comment_reply = CommentReply.objects.using('read').get(id=parent_id)
            content = comment_reply.content
        return content

    def get_receiver_info(self):
        praise_type = self.praise_type
        parent_id = self.parent_id
        receiver_info = {
            'user_id': 0,
            'username': '',
            'avatar': ''
        }
        if praise_type == self.TYPE.COMMENT_REPLY:
            comment_reply = CommentReply.objects.using('read').get(id=parent_id)
            receiver_info = comment_reply.get_receiver_info()
        return receiver_info

    def get_praise_info(self):
        context = dict()
        context['praise_id'] = self.id
        context['type'] = self.praise_type
        context['user'] = self.get_user_info()
        context['praise_at'] = timezone.localtime(self.praise_at).strftime("%Y-%m-%d %H:%M:%S")
        context['article_info'] = self.get_article_info()
        context['receiver_info'] = self.get_receiver_info()
        context['content'] = self.get_comment_content()
        context['is_viewed'] = int(self.is_viewed)
        return context


def get_user_be_praised(user_id):
    articles = Article.objects.using('read').filter(author_id=user_id)
    article_ids = list(articles.values_list('id', flat=True))
    query_condition = (Q(praise_type=Praise.TYPE.ARTICLE) & Q(parent_id__in=article_ids))

    comments = Comment.objects.using('read').filter(commentator_id=user_id)
    comment_ids = list(comments.values_list('id', flat=True))
    query_condition |= (Q(praise_type=Praise.TYPE.COMMENT) & Q(parent_id__in=comment_ids))

    comment_replies = CommentReply.objects.using('read').filter(replier_id=user_id)
    comment_reply_ids = list(comment_replies.values_list('id', flat=True))
    query_condition |= (Q(praise_type=Praise.TYPE.COMMENT_REPLY) & Q(parent_id__in=comment_reply_ids))

    praises = Praise.objects.using('read').filter(query_condition).order_by('-id')
    return praises
