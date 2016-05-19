# -*- coding: utf-8 -*-

from django.forms import ModelForm, CheckboxSelectMultiple
from vaas.manager.models import Probe, Director, Backend, TimeProfile


class ProbeModelForm(ModelForm):
    class Meta:
        model = Probe


class TimeProfileModelForm(ModelForm):
    class Meta:
        model = TimeProfile


class DirectorModelForm(ModelForm):
    class Meta:
        widgets = {
            'cluster': CheckboxSelectMultiple()
        }
        model = Director


class BackendModelForm(ModelForm):
    class Meta:
        model = Backend
