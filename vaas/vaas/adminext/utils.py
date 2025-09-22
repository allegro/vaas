class HistoryMixinAdmin:
    history_list_per_page = 10
    def get_readonly_fields(self, request, obj=None):
        if obj and hasattr(obj, "_history"):
            return [field.name for field in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)