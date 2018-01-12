from django.conf.urls import url
from restful_api.article.views import (
    ArticleList,
    PraiseList
)

urlpatterns = [
    url(r'^articles$', ArticleList.as_view(), name='articles'),
    url(r'^user/praises$', PraiseList.as_view(), name='user_praises'),
]
