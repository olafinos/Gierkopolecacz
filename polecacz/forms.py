from django import forms

from polecacz.models import Opinion


class OpinionForm(forms.ModelForm):
    rating = forms.IntegerField(max_value=10, min_value=1)
    description = forms.CharField(widget=forms.Textarea, max_length=500)
    class Meta:
        model = Opinion
        fields = ("rating",
                  "description")
