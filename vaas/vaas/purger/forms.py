from django import forms
from django.core.validators import URLValidator
from vaas.cluster.models import LogicalCluster


class PurgeForm(forms.Form):
    url = forms.CharField(label="Url to purge", validators=[URLValidator()])
    cluster = forms.ModelChoiceField(
        label="Varnish cluster", queryset=LogicalCluster.objects.all()
    )
