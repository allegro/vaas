from django.contrib import admin
from django.utils.html import format_html
from simple_history.admin import SimpleHistoryAdmin

from vaas.cluster.models import VarnishServer, VclTemplate, VclTemplateBlock, Dc, LogicalCluster
from vaas.cluster.cluster import VarnishApiProvider
from vaas.manager.signals import switch_state_and_reload


def enable_varnish_servers(modeladmin, request, queryset):
    switch_state_and_reload(queryset, True)
enable_varnish_servers.short_description = "Enable varnish servers"


def disable_varnish_servers(modeladmin, request, queryset):
    switch_state_and_reload(queryset, False)
disable_varnish_servers.short_description = "Disable varnish servers"


class VarnishServerAdmin(admin.ModelAdmin):
    search_fields = ['dc__symbol', 'ip', 'hostname', 'template__name']
    list_display = (
        'hostname',
        'ip',
        'port',
        'dc',
        'cluster',
        'cluster_weight',
        'template',
        'custom_enabled',
        'is_connected',
        'vcl'
    )
    actions = [enable_varnish_servers, disable_varnish_servers]
    varnish_api_provider = None

    def get_list_display(self, request):
        self.varnish_api_provider = VarnishApiProvider()
        return super(VarnishServerAdmin, self).get_list_display(request)

    def custom_enabled(self, obj):
        if obj.enabled:
            return format_html(
                "<div class='span13 text-center'>" +
                "<a class='btn btn-mini btn-success' href='#'>" +
                "<i class='icon-ok-circle'></i></a>" +
                "</div>"
            )
        else:
            return format_html(
                "<div class='span13 text-center'>" +
                "<a class='btn btn-mini' href='#'><i class='icon-ban-circle'></i></a>" +
                "</div>"
            )
    custom_enabled.short_description = 'Enabled'

    def is_connected(self, obj):
        try:
            self.varnish_api_provider.get_api(obj)
            return format_html(
                "<div class='span13 text-center'>" +
                "<a class='btn btn-mini btn-success' href='#'><i class='icon-ok'></i></a>" +
                "</div>"
            )
        except:
            return format_html(
                "<div class='span13 text-center'>" +
                "<a class='btn btn-mini btn-danger' href='#'><i class='icon-off'></i></a>" +
                "</div>"
            )

    def vcl(self, obj):
        return format_html(
            ("<div class='span13 text-center'>" +
             "<button class='btn btn-success' data-remote='/manager/varnish/vcl/%s/' " +
             "data-toggle='modal' data-target='#vclModal'>Show vcl</button>" +
             "</div>") % obj.id
        )


class VclTemplateBlockAdmin(admin.ModelAdmin):
    list_display = ['tag', 'template']


admin.site.register(VarnishServer, VarnishServerAdmin)
admin.site.register(VclTemplate, SimpleHistoryAdmin)
admin.site.register(VclTemplateBlock, VclTemplateBlockAdmin)
admin.site.register(Dc)
admin.site.register(LogicalCluster)
