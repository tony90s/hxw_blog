from django import forms


class UnifiedCommentListForm(forms.Form):
    user_id = forms.IntegerField(required=True, min_value=1)
    comment_type = forms.IntegerField(required=True)
    page_index = forms.IntegerField(required=True, min_value=1)

    def clean_comment_type(self):
        comment_type = self.cleaned_data.get('comment_type')
        if comment_type is None:
            raise forms.ValidationError("comment_type can't be blank.")
        if comment_type not in [0, 1]:
            raise forms.ValidationError("comment_type must be 0 or 1.")
        return self.cleaned_data['comment_type']
