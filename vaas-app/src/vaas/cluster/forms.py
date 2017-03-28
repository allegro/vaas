# -*- coding: utf-8 -*-
from django.forms import ModelForm
from django.core.exceptions import ValidationError
from vaas.cluster.models import LogicalCluster, Dc, VclTemplate, VarnishServer, VclTemplateBlock


class LogicalCLusterModelForm(ModelForm):
    class Meta:
        model = LogicalCluster


class DcModelForm(ModelForm):
    class Meta:
        model = Dc


class VclTemplateModelForm(ModelForm):
    class Meta:
        model = VclTemplate

    def clean_comment(self):
        if self.instance and self.instance.pk:
            if self.cleaned_data['comment'] == self.instance.comment:
                raise ValidationError('Please update comment.')
            return self.instance.comment
        else:
            return self.cleaned_data['comment']


class VarnishServerModelForm(ModelForm):
    class Meta:
        model = VarnishServer


class VclTemplateBlockModelForm(ModelForm):
    class Meta:
        model = VclTemplateBlock
