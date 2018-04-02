from django.conf.urls import url
from restful_api.article.views import (
    CreateArticleView,
    UpdateArticleView,
    ArticleList,
    PraiseList,
    DeleteCommentView,
    DeleteArticleView,
    DeleteCommentReplyView,
    CancelPraiseView,
    UpdateIsViewedStatusView,
    UpdateArticleReleaseStatusView
)

urlpatterns = [
    url(r'^create$', CreateArticleView.as_view(), name='create_article'),
    url(r'^update$', UpdateArticleView.as_view(), name='update_article'),
    url(r'^articles$', ArticleList.as_view(), name='articles'),
    url(r'^user/praises$', PraiseList.as_view(), name='user_praises'),
    url(r'^comment/delete$', DeleteCommentView.as_view(), name='delete_comment'),
    url(r'^delete$', DeleteArticleView.as_view(), name='delete_article'),
    url(r'^comment/reply/delete$', DeleteCommentReplyView.as_view(), name='delete_comment_reply'),
    url(r'^praise/cancel$', CancelPraiseView.as_view(), name='cancel_praise'),
    url(r'^is_viewed_status/update$', UpdateIsViewedStatusView.as_view(), name='update_is_viewed_status'),
    url(r'^release$', UpdateArticleReleaseStatusView.as_view(), name='update_article_release_status'),
]
