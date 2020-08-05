from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import UserInfo


class MovieTitleForm(forms.Form):
    movie_title = forms.CharField(max_length=100)


# class UserInfoForm(forms.ModelForm):
#     class Meta:
#         model = UserInfo
#         fields = ('first_name', 'last_name', 'email', 'education')
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.helper = FormHelper()
#         self.helper.form_method = 'post'
#         self.helper.add_input(Submit('submit', 'Validate'))

