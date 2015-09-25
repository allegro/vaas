# -*- coding: utf-8 -*-

from django.forms import ModelForm, CheckboxSelectMultiple
from vaas.manager.models import Probe, Director, Backend


class ProbeModelForm(ModelForm):
    class Meta:
        model = Probe


class DirectorModelForm(ModelForm):
    class Meta:
        widgets = {
            'cluster': CheckboxSelectMultiple()
        }
        model = Director


class BackendModelForm(ModelForm):
    class Meta:
        model = Backend
