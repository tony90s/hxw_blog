from django import forms

from article.models import Article, Comment, CommentReply, Praise


class CancelPraiseForm(forms.Form):
    praise_type = forms.IntegerField(required=True)
    parent_id = forms.IntegerField(required=True)

    def clean_praise_type(self):
        praise_type = self.cleaned_data.get('praise_type')
        if praise_type is None:
            raise forms.ValidationError("praise_type can't be blank.")
        if praise_type not in [value for value, name in Praise.TYPE_CHOICES]:
            raise forms.ValidationError("praise_type must be 1,2,3.")
        return self.cleaned_data['praise_type']


class UpdateIsViewedStatusForm(forms.Form):
    object_type = forms.IntegerField(required=True)
    parent_id = forms.IntegerField(required=True)

    def clean_object_type(self):
        object_type = self.cleaned_data.get('object_type')
        if object_type is None:
            raise forms.ValidationError("object_type can't be blank.")
        if object_type not in [1, 2, 3]:
            raise forms.ValidationError("object_type must be 1,2,3.")
        return self.cleaned_data['object_type']


class UpdateOrDeleteArticleForm(forms.Form):
    article_id = forms.IntegerField(required=True)


class DeleteCommentReplyForm(forms.Form):
    comment_reply_id = forms.IntegerField(required=True)


class DeleteCommentForm(forms.Form):
    comment_id = forms.IntegerField(required=True)
