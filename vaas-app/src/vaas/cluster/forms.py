# -*- coding: utf-8 -*-

from django.forms import ModelForm
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


class VarnishServerModelForm(ModelForm):
    class Meta:
        model = VarnishServer


class VclTemplateBlockModelForm(ModelForm):
    class Meta:
        model = VclTemplateBlock
