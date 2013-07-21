from django import forms
from example.models import Foo, Bar


class FooForm(forms.ModelForm):
    class Meta:
        model = Foo
        exclude = [
            'bar',
            'bazzes'
        ]

    # def clean_name(self):
    #     data = self.cleaned_data['name']
    #     raise forms.ValidationError('Fake validation error', code='fake')
    #     return data


class BarForm(forms.ModelForm):
    class Meta:
        model = Bar

    # def clean_name(self):
    #     data = self.cleaned_data['name']
    #     raise forms.ValidationError('Fake validation error', code='fake')
    #     return data
