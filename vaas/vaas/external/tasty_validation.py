from django.forms import ModelChoiceField
from tastypie.bundle import Bundle
from tastypie.validation import CleanedDataFormValidation

"""
github source: https://github.com/toastdriven/django-tastypie/issues/152
"""


class ModelCleanedDataFormValidation(CleanedDataFormValidation):
    """
    Override tastypie's standard ``FormValidation`` since this does not care
    about URI to PK conversion for ``ToOneField`` or ``ToManyField``.
    """

    def uri_to_pk(self, uri):
        """
        Returns the integer PK part of a URI.

        Assumes ``/api/v1/resource/123/`` format. If conversion fails, this just
        returns the URI unmodified.

        Also handles lists of URIs
        """

        if uri is None:
            return None

        if isinstance(uri, int):
            return uri

        if isinstance(uri, Bundle):
            uri = uri.data

        if isinstance(uri, dict):
            if 'resource_uri' in uri:
                uri = uri['resource_uri']
            else:
                return None

        # convert everything to lists
        multiple = not isinstance(uri, str)
        uris = uri if multiple else [uri]

        # handle all passed URIs
        converted = []

        for one_uri in uris:
            try:
                # hopefully /api/v1/<resource_name>/<pk>/
                converted.append(int(one_uri.split('/')[-2]))
            except (IndexError, ValueError):
                raise ValueError("URI %s could not be converted to PK integer." % one_uri)

        # convert back to original format
        return converted if multiple else converted[0]

    def form_args(self, bundle):
        kwargs = super(ModelCleanedDataFormValidation, self).form_args(bundle)
        kwargs['data'].update(bundle.data)

        # check if model is already in database, if true change internal state
        if hasattr(kwargs['instance'], 'pk') and kwargs['instance'].pk is not None:
            if self.form_class._meta.model._default_manager.filter(pk=kwargs['instance'].pk).exists():
                kwargs['instance']._state.adding = False

        relation_fields = [name for name, field in
                           self.form_class.base_fields.items()
                           if issubclass(field.__class__, ModelChoiceField)]

        for field in relation_fields:
            if field in kwargs['data']:
                if isinstance(kwargs['data'][field], list):
                    kwargs['data'][field] = list(map(self.uri_to_pk, kwargs['data'][field]))
                else:
                    kwargs['data'][field] = self.uri_to_pk(kwargs['data'][field])

        return kwargs
