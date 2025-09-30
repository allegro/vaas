from django import forms


class HistoryMixinAdmin:
    history_list_per_page = 10
    # The problem here is that History Form (during Revert operation)
    # is giving us editable form. Below is making all fields as read-only

    def get_form(self, request, obj=None, **kwargs):
        if 'history' in request.path:
            class DynamicReadOnlyHistoryForm(forms.ModelForm):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    for field_name, field in self.fields.items():
                        field.disabled = True

                def clean(self):
                    cleaned_data = super().clean()
                    # This is custom overlay for historic form - as history model display all model values,
                    # some of our custom logic either FE or BE is skipped and form submission fails
                    # for fields that may not be required in certain scenarios
                    if cleaned_data.get("type") == "dynamic" or cleaned_data.get("clusters_in_sync"):
                        if self._errors.get("clusters"):
                            del self._errors["clusters"]
                    return self.cleaned_data

                class Meta:
                    model = self.model
                    fields = '__all__'
            return DynamicReadOnlyHistoryForm
        return super().get_form(request, obj, **kwargs)
