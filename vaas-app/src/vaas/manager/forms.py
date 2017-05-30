# -*- coding: utf-8 -*-

from django.forms import ModelForm, CheckboxSelectMultiple
from vaas.manager.models import Probe, Director, Backend, TimeProfile


class ProbeModelForm(ModelForm):
    class Meta:
        model = Probe
        fields = '__all__'


class TimeProfileModelForm(ModelForm):
    class Meta:
        model = TimeProfile
        fields = '__all__'


class DirectorModelForm(ModelForm):
    class Meta:
        widgets = {
            'cluster': CheckboxSelectMultiple()
        }
        model = Director
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(DirectorModelForm, self).__init__(*args, **kwargs)
        self.fields['probe'].queryset = Probe.objects.order_by('name')


class BackendModelForm(ModelForm):
    class Meta:
        model = Backend
        fields = '__all__'
