from django.conf.urls import url
from restful_api.article.views import (
    CreateArticleView,
    UpdateDestroyArticleView,
    ArticleList,
    CommentList,
    CommentReplyList,
    UserCommentList,
    PraiseList,
    UserPraiseList,
    SaveCommentView,
    DeleteCommentView,
    SaveCommentReplyView,
    SavePraiseView,
    CancelPraiseView,
    UpdateIsViewedStatusView,
    UpdateArticleReleaseStatusView,
    MessagesNotViewedCountView
)

urlpatterns = [
    url(r'^create$', CreateArticleView.as_view(), name='create_article'),
    url(r'^(?P<article_id>[0-9]+)$', UpdateDestroyArticleView.as_view(), name='update_destroy_article'),
    url(r'^articles$', ArticleList.as_view(), name='articles'),
    url(r'^comments$', CommentList.as_view(), name='comments'),
    url(r'^comment/replies$', CommentReplyList.as_view(), name='comment_replies'),
    url(r'^user/comments$', UserCommentList.as_view(), name='user_comments'),
    url(r'^user/praises$', UserPraiseList.as_view(), name='user_praises'),
    url(r'^praises$', PraiseList.as_view(), name='praises'),
    url(r'^comment/save$', SaveCommentView.as_view(), name='save_comment'),
    url(r'^comment/reply/save$', SaveCommentReplyView.as_view(), name='save_comment_reply'),
    url(r'^praise/save$', SavePraiseView.as_view(), name='save_praise'),
    url(r'^comment/delete$', DeleteCommentView.as_view(), name='delete_comment'),
    url(r'^praise/cancel$', CancelPraiseView.as_view(), name='cancel_praise'),
    url(r'^is_viewed_status/update$', UpdateIsViewedStatusView.as_view(), name='update_is_viewed_status'),
    url(r'^release$', UpdateArticleReleaseStatusView.as_view(), name='update_article_release_status'),
    url(r'^user/messages/not_viewed$', MessagesNotViewedCountView.as_view(), name='user_not_viewed_messages')
]
