from django.conf.urls import url
from article.views import (
    create_article,
    save_article,
    article_details,
    save_comment,
    save_comment_reply,
    save_praise,
    delete_article,
    delete_comment,
    delete_comment_reply,
    cancel_praise,
    article_category_index_views,
    articles_list,
    article_comments_list,
    update_is_viewed_status,
)

urlpatterns = [
    url(r'^new/$', create_article, name='create_article'),
    url(r'^save/$', save_article, name='save_article'),
    url(r'^details/(?P<article_id>\d+)$', article_details, name='details'),
    url(r'^comment/save$', save_comment, name='save_comment'),
    url(r'^comment/reply/save$', save_comment_reply, name='save_comment_reply'),
    url(r'^praise/save$', save_praise, name='save_praise'),
    url(r'^delete$', delete_article, name='delete_article'),
    url(r'^comment/delete$', delete_comment, name='delete_comment'),
    url(r'^comment/reply/delete$', delete_comment_reply, name='delete_comment_reply'),
    url(r'^praise/cancel$', cancel_praise, name='cancel_praise'),
    url(r'^category/(?P<article_type>\d+)$', article_category_index_views, name='article_category'),
    url(r'^articles$', articles_list, name='articles'),
    url(r'^comments$', article_comments_list, name='comments'),
    url(r'^is_viewed_status/update$', update_is_viewed_status, name='update_is_viewed_status'),
]
