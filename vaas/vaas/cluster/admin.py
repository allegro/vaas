from django.contrib.admin import SimpleListFilter
from django.db import models
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import SafeText
from simple_history.admin import SimpleHistoryAdmin
from django_ace import AceWidget

from vaas.external.audit import AuditableModelAdmin
from vaas.cluster.coherency import OutdatedServerManager
from vaas.cluster.models import DomainMapping, VarnishServer, VclTemplate, VclTemplateBlock, Dc, LogicalCluster, \
    VclVariable
from vaas.cluster.forms import DomainMappingForm, VclTemplateModelForm, VarnishServerModelForm, VclVariableModelForm, \
    LogicalCLusterModelForm
from vaas.cluster.cluster import VarnishApiProvider
from vaas.manager.signals import switch_status_and_reload

ace_widget = AceWidget(theme='solarized_dark', mode='c_cpp', width='700px', height='400px')


def enable_varnish_servers(modeladmin, request, queryset):
    switch_status_and_reload(queryset, 'active')


enable_varnish_servers.short_description = "Enable varnish servers"


def maintenance_varnish_servers(modeladmin, request, queryset):
    switch_status_and_reload(queryset, 'maintenance')


maintenance_varnish_servers.short_description = "Maintenance varnish servers"


def disable_varnish_servers(modeladmin, request, queryset):
    switch_status_and_reload(queryset, 'disabled')


disable_varnish_servers.short_description = "Disable varnish servers"


class OutdatedFilter(SimpleListFilter):
    title = 'VCL Status'
    parameter_name = 'outdated'

    def lookups(self, request, model_admin):
        return (('actual', 'Actual'), ('outdated', 'Outdated'))

    def queryset(self, request, queryset):
        if self.value():
            result = OutdatedServerManager().filter(servers=queryset, outdated=(self.value() == 'outdated'))
            return queryset.filter(id__in=[server.id for server, _ in result])

        return queryset


class VarnishServerAdmin(AuditableModelAdmin):
    form = VarnishServerModelForm
    search_fields = ['dc__symbol', 'ip', 'hostname', 'template__name']
    list_filter = ['cluster__name', OutdatedFilter]
    list_display = (
        'hostname',
        'ip',
        'port',
        'http_port',
        'dc',
        'cluster',
        'cluster_weight',
        'template',
        'template_version',
        'custom_enabled',
        'is_connected',
        'custom_is_canary',
        'vcl'
    )
    actions = [enable_varnish_servers, maintenance_varnish_servers, disable_varnish_servers]
    varnish_api_provider = None

    def get_list_display(self, request):
        self.varnish_api_provider = VarnishApiProvider()
        return super(VarnishServerAdmin, self).get_list_display(request)

    def template_version(self, obj):
        return obj.template.get_template_version()

    def custom_enabled(self, obj):
        if obj.status == 'active':
            return format_html(
                "<div class='span13 text-center'>"
                "<a class='btn btn-xs btn-success' href='#'>"
                "<i class='glyphicon glyphicon-ok-sign'></i></a>"
                "</div>"
            )
        elif obj.status == 'maintenance':
            return format_html(
                "<div class='span13 text-center'>"
                "<a class='btn btn-xs btn-warning' href='#'>"
                "<i class='glyphicon glyphicon-wrench'></i></a>"
                "</div>"
            )
        else:
            return format_html(
                "<div class='span13 text-center'>"
                "<a class='btn btn-xs' href='#'><i class='glyphicon glyphicon-ban-circle'></i></a>"
                "</div>"
            )
    custom_enabled.short_description = 'Enabled'

    def is_connected(self, obj):
        if obj.status == 'active':
            return format_html(
                "<div class='span13 text-center'>"
                "<a class='btn btn-xs' data-varnish-id='" + str(obj.pk) + "' href='#'>"
                "<i class='glyphicon loader'></i>"
                "</a>"
                "</div>"
            )
        elif obj.status == 'maintenance':
            return format_html(
                "<div class='span13 text-center'>"
                "<a class='btn btn-xs btn-warning' href='#'>"
                "<i class='glyphicon glyphicon-wrench'></i></a>"
                "</div>"
            )
        else:
            return format_html(
                "<div class='span13 text-center'>"
                "<a class='btn btn-xs' href='#'><i class='glyphicon glyphicon-ban-circle'></i></a>"
                "</div>"
            )

    def custom_is_canary(self, obj):
        if obj.is_canary:
            return format_html(
                "<div class='span13 text-center'>"
                "<a class='btn btn-xs btn-success' href='#'>"
                "<i class='glyphicon glyphicon-ok-sign'></i></a>"
                "</div>"
            )
        else:
            return format_html(
                "<div class='span13 text-center'>"
                "<a class='btn btn-xs' href='#'><i class='glyphicon glyphicon-ban-circle'></i></a>"
                "</div>"
            )
    custom_is_canary.short_description = 'Canary'

    def vcl(self, obj):
        if obj.status in ('active', 'maintenance'):
            return format_html(
                ("<div class='span13 text-center'>"
                 "<button type='button' class='btn btn-success' data-toggle='modal' "
                 "data-vcl='/manager/varnish/vcl/%s/'"
                 "data-target='#vclModal'>Show vcl</button>"
                 "</div>") % obj.id
            )
        else:
            return format_html(
                ("<div class='span13 text-center'>"
                 "<button class='btn btn-danger' disabled>Show vcl</button>"
                 "</div>")
            )


class VclTemplateBlockAdmin(SimpleHistoryAdmin):
    formfield_overrides = {
        models.TextField: {'widget': ace_widget},
    }
    list_display = ['tag', 'template']


class DomainMappingAdmin(SimpleHistoryAdmin):
    form = DomainMappingForm
    search_fields = ['domain', 'mapping', 'type', 'clusters__name']
    list_display = ['domain', 'mapping', 'type', 'get_clusters']

    def get_clusters(self, obj: DomainMapping) -> str:
        return ", ".join([c.name for c in obj.clusters.all()])

    get_clusters.short_description = 'Related clusters'


class VclTemplateAdmin(SimpleHistoryAdmin, AuditableModelAdmin):
    form = VclTemplateModelForm
    search_fields = ['name']
    formfield_overrides = {
        models.TextField: {'widget': ace_widget},
    }
    list_display = ['name', 'version']
    object_history_template = "custom_simple_history/object_history.html"


class LogicalClusterAdmin(admin.ModelAdmin):
    form = LogicalCLusterModelForm
    search_fields = ['name', 'labels']
    list_display = [
        'name',
        'service_mesh_routing',
        'partial_reload',
        'reload_timestamp',
        'error_timestamp',
        'last_error_info',
        'get_tags',
        'labels',
        'get_domains',
        'varnish_servers'
    ]
    exclude = ('last_error_info', 'reload_timestamp', 'error_timestamp')

    def get_tags(self, obj: LogicalCluster) -> str:
        return ", ".join(obj.current_vcls)

    get_tags.short_description = 'Current vcls'

    def labels(self, obj: LogicalCluster) -> SafeText:
        labels_list_html = ''
        if obj.labels:
            for label in obj.labels:
                labels_list_html += "<span class='label label-default'>%s</span>" % label
        return format_html(labels_list_html)

    labels.short_description = 'Labels'

    def get_domains(self, obj: LogicalCluster) -> SafeText:
        domains_html = ''
        for domain in obj.domainmapping_set.all():
            domains_html += ("<span class='label label-primary'>%s</apan>") % domain.domain
        return format_html(domains_html)

    get_domains.short_description = 'Related Domains'

    def varnish_servers(self, obj: LogicalCluster) -> SafeText:
        return format_html(
            ("<div class='span13 text-center'>"
             "<a class='btn btn-success' href='/admin/cluster/varnishserver/?cluster__name=%s' "
             ">Show varnish servers (%d)</a>"
             "</div><br/>"
             "<div class='span13 text-center'>"
             "<a class='btn btn-danger' href='/admin/cluster/varnishserver/?cluster__name=%s&outdated=outdated' "
             ">Show outdated servers</a>"
             "</div>") % (obj.name, obj.varnish_count(), obj.name)
        )


class VclVariableAdmin(admin.ModelAdmin):
    form = VclVariableModelForm
    list_display = ['key', 'value', 'cluster']


admin.site.register(VarnishServer, VarnishServerAdmin)
admin.site.register(VclTemplate, VclTemplateAdmin)
admin.site.register(VclTemplateBlock, VclTemplateBlockAdmin)
admin.site.register(Dc)
admin.site.register(DomainMapping, DomainMappingAdmin)
admin.site.register(LogicalCluster, LogicalClusterAdmin)
admin.site.register(VclVariable, VclVariableAdmin)
