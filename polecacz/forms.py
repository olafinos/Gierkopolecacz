from django import forms

from polecacz.models import Opinion


class OpinionForm(forms.ModelForm):
    """
    Class responsible for creating Opinion model form and also for validating its data
    """
    rating = forms.IntegerField(max_value=10, min_value=1)
    description = forms.CharField(widget=forms.Textarea, max_length=500)

    class Meta:
        model = Opinion
        fields = ("rating",
                  "description")
