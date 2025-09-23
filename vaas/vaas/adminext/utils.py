from django import forms

class HistoryMixinAdmin:
    history_list_per_page = 10
    
    ## The problem here is that History Form (during Revert operation) is giving us editable form. Below is making all fields as read-only
    def get_form(self, request, obj=None, **kwargs):
        if 'history' in request.path:
            class DynamicReadOnlyHistoryForm(forms.ModelForm):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    for field_name, field in self.fields.items():
                        field.disabled = True

                class Meta:
                    model = self.model
                    fields = '__all__'
            return DynamicReadOnlyHistoryForm
        return super().get_form(request, obj, **kwargs)