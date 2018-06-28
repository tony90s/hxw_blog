from django.conf.urls import url
from article.views import (
    article_details,
    user_articles
)

from microsite_article.views import (
    comment_details
)

urlpatterns = [
    url(r'^details/(?P<article_id>\d+)$', article_details, name='details'),
    url(r'^comment/details/(?P<comment_id>\d+)$', comment_details, name='comment_details'),
    url(r'^author/(?P<author_id>\d+)$', user_articles, name='user_articles'),
]
