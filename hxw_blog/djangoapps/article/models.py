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
        NOTE = 5

    TYPE_CHOICES = (
        (TYPE.PYTHON, 'Python'),
        (TYPE.LINUX, 'Linux'),
        (TYPE.DJANGO, 'Django'),
        (TYPE.FRONT_END, '前端技术'),
        (TYPE.NOTE, '随笔')
    )
    author_id = models.IntegerField(db_index=True, verbose_name='作者', default=0)
    title = models.CharField(max_length=64, default='', verbose_name='标题')
    content_txt = models.TextField(default='', verbose_name='纯文本内容')
    content_html = models.TextField(default='', verbose_name='html内容')
    type = models.IntegerField(choices=TYPE_CHOICES, default=TYPE.PYTHON, verbose_name='类别')
    cover_photo = models.ImageField(upload_to='article/cover', blank=True, null=True, verbose_name='封面图片')
    created_at = models.DateTimeField(auto_now_add=timezone.now, verbose_name='创建时间')
    update_at = models.DateTimeField(blank=True, null=True, verbose_name='更新时间')
    release_at = models.DateTimeField(blank=True, null=True, verbose_name='发布时间')
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
            return self.release_time

    @property
    def word_count(self):
        return len(self.content_txt)

    def get_author_data(self):
        author = User.objects.using('read').get(id=self.author_id)
        author_data = {
            'user_id': author.id,
            'username': author.username,
            'avatar': author.profile.avatar.url
        }
        return author_data

    def get_comments_json(self):
        comments = Comment.objects.using('read').filter(Q(article_id=self.id)).order_by("-id")
        comments_data = list()
        for comment in comments:
            comments_data.append(comment.render_json())
        return comments_data

    @property
    def comment_times(self):
        comments = Comment.objects.using('read').filter(Q(article_id=self.id))
        comments_count = comments.count()
        for comment in comments:
            comment_replies = CommentReply.objects.using('read').filter(Q(comment_id=comment.id))
            comments_count += comment_replies.count()
        return comments_count

    @property
    def praise_times(self):
        praises = Praise.objects.using('read').filter(Q(praise_type=Praise.TYPE.ARTICLE) & Q(parent_id=self.id))
        return praises.count()

    def render_json(self):
        context = dict()
        context['article_id'] = self.id
        context['title'] = self.title
        context['type'] = {
            'value': self.type,
            'display_name': self.get_type_display()
        }
        cover_photo = self.cover_photo
        context['cover_photo'] = cover_photo.url if cover_photo.name else ''
        context['content_html'] = self.content_html
        context['author'] = self.get_author_data()
        context['comment_times'] = self.comment_times
        context['praise_times'] = self.praise_times
        context['comments'] = self.get_comments_json()
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
        cover_photo = self.cover_photo
        context['cover_photo'] = cover_photo.url if cover_photo.name else ''
        context['author'] = self.get_author_data()
        context['abstract'] = self.content_txt[0:91] + '...'
        context['comment_times'] = self.comment_times
        context['praise_times'] = self.praise_times
        context['release_time'] = self.release_time
        context['page_views'] = self.page_views
        return context


def get_user_articles(user_id):
    articles = Article.objects.using('read').filter(author_id=user_id)
    articles_summarization = list()
    for article in articles:
        articles_summarization.append(article.get_summarization)
    return articles_summarization


class Comment(models.Model):
    article_id = models.IntegerField(db_index=True, verbose_name='博文', default=0)
    commentator_id = models.IntegerField(db_index=True, verbose_name='评论人', default=0)
    comment_at = models.DateTimeField(auto_now_add=timezone.now, verbose_name='评论时间')
    content = models.CharField(max_length=140, default='', verbose_name='评论内容')

    def __str__(self):
        return '%s %s' % (self.article.title, self.content[0:10])

    class Meta:
        verbose_name = _('comment')
        verbose_name_plural = _('comments')

    def render_json(self):
        context = dict()
        context['article_id'] = self.article_id
        context['comment_id'] = self.id
        commentator = User.objects.using('read').get(id=self.commentator_id)
        commentator_data = {
            'user_id': commentator.id,
            'username': commentator.get_username(),
            'avatar': commentator.profile.avatar.url
        }
        context['commentator'] = commentator_data
        context['comment_at'] = timezone.localtime(self.comment_at).strftime("%Y-%m-%d %H:%M:%S")
        context['content'] = self.content

        comment_replies = CommentReply.objects.using('read').filter(Q(comment_id=self.id)).order_by("-id")
        comment_replies_data = list()
        for comment_reply in comment_replies:
            comment_replies_data.append(comment_reply.render_json())
        context['comment_replies'] = comment_replies_data

        praises = Praise.objects.using('read').filter(Q(praise_type=Praise.TYPE.COMMENT) & Q(parent_id=self.id))
        context['praise_times'] = praises.count()

        return context


class CommentReply(models.Model):
    comment_id = models.IntegerField(db_index=True, verbose_name='所属评论', default=0)
    replier_id = models.IntegerField(db_index=True, verbose_name='回复人', default=0)
    receiver_id = models.IntegerField(db_index=True, verbose_name='接受者', default=0)
    reply_at = models.DateTimeField(auto_now_add=timezone.now, verbose_name='回复时间')
    content = models.CharField(max_length=140, default='', verbose_name='回复内容')

    class Meta:
        verbose_name = _('comment_reply')
        verbose_name_plural = _('comment_replies')

    def render_json(self):
        context = dict()
        context['comment_reply_id'] = self.id
        context['comment_id'] = self.comment_id
        replier = User.objects.using('read').get(id=self.replier_id)
        receiver = User.objects.using('read').get(id=self.receiver_id)
        replier_data = {
            'user_id': replier.id,
            'username': replier.get_username(),
            'avatar': replier.profile.avatar.url
        }
        receiver_data = {
            'user_id': receiver.id,
            'username': receiver.username,
            'avatar': receiver.profile.avatar.url
        }
        context['replier'] = replier_data
        context['receiver'] = receiver_data
        context['reply_at'] = timezone.localtime(self.reply_at).strftime("%Y-%m-%d %H:%M:%S")
        context['content'] = self.content
        praises = Praise.objects.using('read').filter(Q(praise_type=Praise.TYPE.COMMENT_REPLY) & Q(parent_id=self.id))
        context['praise_times'] = praises.count()
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
    parent_id = models.IntegerField(db_index=True, verbose_name='点赞对象id', default=0)
    user_id = models.IntegerField(db_index=True, verbose_name='点赞人', default=0)
    praise_at = models.DateTimeField(auto_now_add=timezone.now, verbose_name='点赞时间')

    class Meta:
        verbose_name = _('praise')
        verbose_name_plural = _('praises')
