import importlib
from django.conf import settings
from django.contrib import admin


audit_bulk_operations = getattr(settings, 'AUDIT_BULK_OPERATIONS', None)

if audit_bulk_operations:
    audit_signals_module = importlib.import_module(audit_bulk_operations['signals_module'])
    audit_bulk_delete = getattr(audit_signals_module, audit_bulk_operations['delete'])
    audit_bulk_update = getattr(audit_signals_module, audit_bulk_operations['update'])


class AuditableModelAdmin(admin.ModelAdmin):
    def delete_queryset(self, request, queryset):
        if audit_bulk_operations:
            old_values = list(queryset)
        res = super().delete_queryset(request, queryset)
        if audit_bulk_operations:
            audit_bulk_delete.send(sender=queryset.model, deleted_instances=old_values)
        return res
