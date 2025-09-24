from django.contrib import admin


class HistoryMixinAdmin(admin.ModelAdmin):
    history_list_per_page = 10

    def get_readonly_fields(self, request, obj=None):
        if "history" in request.path:
            return [f.name for f in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)
