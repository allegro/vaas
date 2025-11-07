# -*- coding: utf-8 -*-
from django.forms import ModelForm, TextInput
from django.contrib.admin.widgets import FilteredSelectMultiple

from django.forms import ModelMultipleChoiceField

from vaas.adminext.widgets import SearchableSelect
from vaas.cluster.models import (
    LogicalCluster,
    Dc,
    VclTemplate,
    VarnishServer,
    VclTemplateBlock,
    VclVariable,
    DomainMapping,
)


class LogicalCLusterModelForm(ModelForm):
    class Meta:
        model = LogicalCluster
        fields = "__all__"


class DomainMappingForm(ModelForm):
    clusters = ModelMultipleChoiceField(
        queryset=LogicalCluster.objects.order_by("name"),
        widget=FilteredSelectMultiple(is_stacked=False, verbose_name="clusters"),
        required=False,
    )

    class Meta:
        model = DomainMapping
        fields = "__all__"

    class Media:
        js = ("js/mapping-type-switch.js",)

    def clean(self):
        cleaned_data = super(DomainMappingForm, self).clean()
        if cleaned_data.get("type", "static") in ["static", "static_regex"]:
            if len(cleaned_data.get("clusters", None)) == 0:
                self._errors["clusters"] = self.error_class(
                    ["Selecting clusters is required for static mapping"]
                )
        return self.cleaned_data


class DcModelForm(ModelForm):
    class Meta:
        model = Dc
        fields = "__all__"


class VclTemplateModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        initial = kwargs.get("initial", {})
        initial["comment"] = None
        kwargs["initial"] = initial
        super(VclTemplateModelForm, self).__init__(*args, **kwargs)

    class Meta:
        model = VclTemplate
        fields = "__all__"

    class Media:
        js = (
            "js/vcl-validation.js",
            "utils/js/labels.js",
        )


class VarnishServerModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(VarnishServerModelForm, self).__init__(*args, **kwargs)
        for related in ("dc", "template", "cluster"):
            if hasattr(self.fields[related].widget, "widget"):
                self.fields[related].widget = self.fields[related].widget.widget

    class Meta:
        model = VarnishServer
        fields = "__all__"
        widgets = {
            "ip": TextInput(attrs={"class": "form-control"}),
            "hostname": TextInput(attrs={"class": "form-control"}),
            "cluster_weight": TextInput(attrs={"class": "form-control"}),
            "secret": TextInput(attrs={"class": "form-control"}),
            "status": SearchableSelect(),
            "dc": SearchableSelect(),
            "template": SearchableSelect(),
            "cluster": SearchableSelect(),
        }


class VclVariableModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(VclVariableModelForm, self).__init__(*args, **kwargs)
        if hasattr(self.fields["cluster"].widget, "widget"):
            self.fields["cluster"].widget = self.fields["cluster"].widget.widget

    class Meta:
        model = VclVariable
        fields = "__all__"
        widgets = {
            "key": TextInput(attrs={"class": "form-control"}),
            "value": TextInput(attrs={"class": "form-control"}),
            "cluster": SearchableSelect(),
        }


class VclTemplateBlockModelForm(ModelForm):
    class Meta:
        model = VclTemplateBlock
        fields = "__all__"
