from django import forms

from article.models import Article, Comment, Praise


class ArticleListForm(forms.Form):
    article_type = forms.IntegerField(required=False)
    is_released = forms.IntegerField(required=True)
    author_id = forms.IntegerField(required=False)

    def clean_is_released(self):
        is_released = self.cleaned_data.get('is_released')
        if is_released not in [0, 1]:
            raise forms.ValidationError("'is_released must be 0 or 1.'")
        return self.cleaned_data['is_released']


class PraiseListForm(forms.Form):
    user_id = forms.IntegerField(required=True)


class CommonPraiseForm(forms.Form):
    praise_type = forms.IntegerField(required=True)
    parent_id = forms.IntegerField(required=True)

    def clean_praise_type(self):
        praise_type = self.cleaned_data.get('praise_type')
        if praise_type is None:
            raise forms.ValidationError("praise_type can't be blank.")
        if praise_type not in [value for value, name in Praise.TYPE_CHOICES]:
            raise forms.ValidationError("praise_type must be 1,2.")
        return self.cleaned_data['praise_type']


class UpdateIsViewedStatusForm(forms.Form):
    object_type = forms.IntegerField(required=True)
    parent_id = forms.IntegerField(required=True)

    def clean_object_type(self):
        object_type = self.cleaned_data.get('object_type')
        if object_type is None:
            raise forms.ValidationError("object_type can't be blank.")
        if object_type not in [1, 2]:
            raise forms.ValidationError("object_type must be 1,2.")
        return self.cleaned_data['object_type']


class CheckArticleIdForm(forms.Form):
    article_id = forms.IntegerField(required=True)


class CheckCommentReplyIdForm(forms.Form):
    comment_reply_id = forms.IntegerField(required=True)


class CheckCommentIdForm(forms.Form):
    comment_id = forms.IntegerField(required=True)


class CheckParentCommentIdForm(forms.Form):
    parent_id = forms.IntegerField(required=True)


class UserCommentListForm(forms.Form):
    user_id = forms.IntegerField(required=True, min_value=1)
    comment_type = forms.IntegerField(required=True)

    def clean_comment_type(self):
        comment_type = self.cleaned_data.get('comment_type')
        if comment_type is None:
            raise forms.ValidationError("comment_type can't be blank.")
        if comment_type not in [0, 1]:
            raise forms.ValidationError("comment_type must be 0 or 1.")
        return self.cleaned_data['comment_type']
