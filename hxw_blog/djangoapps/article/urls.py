from django.conf.urls import url
from article.views import (
    create_article,
    edit_article,
    article_details,
    article_category_index_views,
    articles_list,
    article_comments_list,
    drafts,
    user_articles
)

urlpatterns = [
    url(r'^new/$', create_article, name='create_article'),
    url(r'^edit/(?P<article_id>\d+)$', edit_article, name='edit_article'),
    url(r'^details/(?P<article_id>\d+)$', article_details, name='details'),
    url(r'^category/(?P<article_type>\d+)$', article_category_index_views, name='article_category'),
    url(r'^articles$', articles_list, name='articles'),
    url(r'^comments$', article_comments_list, name='comments'),
    url(r'^drafts$', drafts, name='user_drafts'),
    url(r'^author/(?P<author_id>\d+)$', user_articles, name='user_articles'),
]
