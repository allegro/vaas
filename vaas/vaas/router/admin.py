from django.contrib import admin

from vaas.external.audit import AuditableModelAdmin
from vaas.router.models import Route, Redirect, RedirectAssertion
from vaas.router.forms import RouteModelForm, RedirectModelForm
from django.conf import settings


class RedirectAssertionAdmin(admin.TabularInline):
    model = RedirectAssertion
    extra = 1


class RedirectAdmin(AuditableModelAdmin):
    form = RedirectModelForm
    inlines = [
        RedirectAssertionAdmin,
    ]
    list_display = ['condition', 'src_domain', 'destination', 'action', 'priority', 'preserve_query_params']

class RouteAdmin(AuditableModelAdmin):
    form = RouteModelForm
    search_fields = ['condition', 'clusters__name', 'director__name']
    list_display = ['condition', 'director', 'priority', 'action', 'exposed_on_clusters']
    fieldsets = (
        (None, {
            'fields': ('condition', 'positive_urls', 'priority', 'action', 'director', 'clusters_in_sync', 'clusters',)
        }),
    )

    def exposed_on_clusters(self, obj):
        if obj.clusters_in_sync:
            return "all clusters where the director is present"
        return [c.name for c in obj.clusters.all()]

    def changelist_view(self, request, extra_context=None):
        ctx = {'route_tests_enabled': settings.ROUTE_TESTS_ENABLED}
        return super().changelist_view(request, extra_context=ctx)

    class Media:
        js = ('js/clusters-sync.js', 'utils/js/labels.js')


admin.site.register(Route, RouteAdmin)
admin.site.register(Redirect, RedirectAdmin)
