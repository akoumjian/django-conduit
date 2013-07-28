from django import forms
from example.models import Foo, Bar


class FooForm(forms.ModelForm):
    class Meta:
        model = Foo
        exclude = [
            'bar',
            'bazzes'
        ]


class BarForm(forms.ModelForm):
    class Meta:
        model = Bar
