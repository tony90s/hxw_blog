from django.conf.urls import url
from microsite_article.views import (
    article_details,
)

urlpatterns = [
    url(r'^details/(?P<article_id>\d+)$', article_details, name='details'),
]
