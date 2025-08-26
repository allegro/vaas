from django.contrib import admin

from vaas.external.audit import AuditableModelAdmin
from vaas.router.models import PositiveUrl, Route, Redirect, RedirectAssertion
from vaas.router.forms import PositiveUrlForm, RedirectAssertionForm, RouteModelForm, RedirectModelForm
from django.conf import settings


class RedirectAssertionAdmin(admin.TabularInline):
    model = RedirectAssertion
    form = RedirectAssertionForm

    def get_extra(self, request, obj=None, **kwargs):
        if obj and obj.assertions.count() > 0:
            return 0
        return 1


class PositiveURLAdmin(admin.TabularInline):
    model = PositiveUrl
    form = PositiveUrlForm

    def get_extra(self, request, obj=None, **kwargs):
        if obj and obj.positive_urls.count() > 0:
            return 0
        return 1


class RedirectAdmin(AuditableModelAdmin):
    form = RedirectModelForm
    inlines = [RedirectAssertionAdmin]
    search_fields = ['condition', 'src_domain__domain', 'destination']
    list_display = ['condition', 'src_domain', 'destination', 'action', 'priority', 'preserve_query_params']

    class Media:
        js = ('utils/js/labels.js', 'js/test-report.js', )
        css = {'all': ('css/test-report.css', )}


class RouteAdmin(AuditableModelAdmin):
    form = RouteModelForm
    inlines = [PositiveURLAdmin]
    search_fields = ['condition', 'clusters__name', 'director__name']
    list_display = ['condition', 'director', 'priority', 'action', 'exposed_on_clusters']
    change_list_template = "router/admin_app_route_description.html"
    fieldsets = (
        (None, {
            'fields': ('condition', 'priority', 'action', 'director', 'clusters_in_sync', 'clusters',)
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
        js = ('js/test-report.js', 'utils/js/labels.js')
        css = {'all': ('css/test-report.css', )}


admin.site.register(Route, RouteAdmin)
admin.site.register(Redirect, RedirectAdmin)
