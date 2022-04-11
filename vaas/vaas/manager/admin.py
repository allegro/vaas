import csv

from django.contrib import admin

from vaas.manager.models import Director, Backend, Probe, TimeProfile
from vaas.manager.forms import DirectorModelForm
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from taggit.models import Tag
from taggit.admin import TagAdmin
from tastypie.models import ApiKey
from django_celery_beat.admin import IntervalSchedule, CrontabSchedule, SolarSchedule, ClockedSchedule
from django.utils.html import format_html
from vaas.monitor.models import BackendStatus
from vaas.manager.signals import switch_state_and_reload
from django.http import HttpResponse
from django.utils.encoding import smart_str
from vaas.external.audit import AuditableModelAdmin

try:
    admin.site.unregister(Group)
    admin.site.unregister(User)
    admin.site.unregister(ApiKey)
    admin.site.unregister(Tag)
    admin.site.unregister(TagAdmin)
except:
    pass


def enable_backend(modeladmin, request, queryset):
    switch_state_and_reload(queryset, True)


def disable_backend(modeladmin, request, queryset):
    switch_state_and_reload(queryset, False)


def switch_backend_status(modeladmin, request, queryset):
    enabledSet = Backend.objects.filter(pk__in=map(lambda backend: backend.pk, queryset.filter(enabled=True)))
    disabledSet = Backend.objects.filter(pk__in=map(lambda backend: backend.pk, queryset.filter(enabled=False)))
    switch_state_and_reload(disabledSet, True)
    switch_state_and_reload(enabledSet, False)


def export_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=backend_list.csv'
    writer = csv.writer(response, csv.excel)
    response.write('\ufeff'.encode('utf8'))
    writer.writerow([
        smart_str("id"),
        smart_str("address"),
        smart_str("port"),
        smart_str("director"),
        smart_str("dc"),
        smart_str("status"),
        smart_str("enabled"),
        smart_str("inherit_time_profile"),
        smart_str("weight"),
        smart_str("tags")

    ])
    backend_status_list = BackendStatus.objects.all()
    for obj in queryset:
        status_list = list(filter(
            lambda backend_status: backend_status.address == obj.address and backend_status.port == obj.port,
            backend_status_list
        ))
        status = 'unknown'
        if len(status_list) == 1:
            status = status_list[0].status

        writer.writerow([
            smart_str(obj.pk),
            smart_str(obj.address),
            smart_str(obj.port),
            smart_str(obj.director),
            smart_str(obj.dc),
            smart_str(status),
            smart_str(obj.enabled),
            smart_str(obj.inherit_time_profile),
            smart_str(obj.weight),
            smart_str(obj.tags.all())
        ])
    return response


def enable_director(modeladmin, request, queryset):
    switch_state_and_reload(queryset, True)


def disable_director(modeladmin, request, queryset):
    switch_state_and_reload(queryset, False)


class DirectorAdmin(AuditableModelAdmin):
    search_fields = ['name', 'route_expression']
    form = DirectorModelForm
    list_display = (
        'name', 'service', 'reachable_via_service_mesh', 'service_mesh_label', 'service_tag', 'get_clusters',
        'route_expression', 'probe', 'protocol', 'custom_enabled', 'virtual',)
    list_filter = ['cluster__name', 'service']
    actions = [enable_director, disable_director]

    def get_clusters(self, obj):
        """Return string with newline separated clusters for directory passed as argument"""
        return "\n".join([cluster.name for cluster in obj.cluster.all()])

    get_clusters.short_description = 'Clusters'

    def get_form(self, request, obj=None, **kwargs):
        form = super(DirectorAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['cluster'].widget.can_add_related = False
        return form

    def custom_enabled(self, obj):
        return self._custom_flag(obj.enabled)

    def _custom_flag(self, flag):
        if flag:
            return format_html(
                "<div class='span13 text-center'>" +
                "<a class='btn btn-xs btn-success' href='#'><i class='glyphicon glyphicon-ok-sign'></i></a>" +
                "</div>"
            )
        else:
            return format_html(
                "<div class='span13 text-center'><a class='btn btn-xs' href='#'>" +
                "<i class='glyphicon glyphicon-ban-circle'>" +
                "</i></a></div>"
            )

    custom_enabled.short_description = 'Enabled'


class BackendAdmin(AuditableModelAdmin):
    search_fields = ['address', 'director__name', 'tags__name']
    list_display = ('address', 'port', 'director', 'dc', 'is_healthy', 'custom_enabled', 'get_tags')
    list_filter = ['director__name', 'director__service', 'director__cluster__name', 'dc__symbol']
    actions = [enable_backend, disable_backend, switch_backend_status, export_to_csv]
    fieldsets = (
        (None, {
            'fields': ('address', 'port', 'director', 'dc', 'weight', 'tags', 'inherit_time_profile')
        }),
        ('Advanced options', {
            'fields': ('max_connections', 'connect_timeout', 'first_byte_timeout', 'between_bytes_timeout')
        }),
    )
    backend_status_list = []

    def get_form(self, request, obj=None, **kwargs):
        form = super(BackendAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['dc'].widget.can_add_related = False
        return form

    def get_tags(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])

    get_tags.short_description = 'Tags'

    def get_queryset(self, request):
        return super(BackendAdmin, self).get_queryset(request).prefetch_related('tags', 'director')\
            .extra(select={
                'status':
                    "SELECT status from monitor_backendstatus"
                    " WHERE monitor_backendstatus.address=manager_backend.address"
                    " AND monitor_backendstatus.port=manager_backend.port"
                    " LIMIT 1"
            })

    def custom_enabled(self, obj):
        if obj.enabled:
            return format_html(
                "<div class='span13 text-center'>" +
                "<a class='btn btn-xs btn-success' href='#'><i class='glyphicon glyphicon-ok-sign'></i></a>" +
                "</div>"
            )
        else:
            return format_html(
                "<div class='span13 text-center'><a class='btn btn-xs' href='#'>" +
                "<i class='glyphicon glyphicon-ban-circle'>" +
                "</i></a></div>"
            )

    custom_enabled.short_description = 'Enabled'

    def is_healthy(self, obj):
        if obj.status:
            if obj.status == 'Healthy':
                return format_html(
                    "<div class='span13 text-center'><a class='btn btn-xs btn-success' href='#'>" +
                    "<i class='glyphicon glyphicon-ok'> </i></a></div>"
                )
            else:
                return format_html(
                    "<div class='span13 text-center'><a class='btn btn-xs btn-danger' href='#'>" +
                    "<i class='glyphicon glyphicon-off'> </i></a></div>"
                )
        else:
            return format_html(
                "<div class='span13 text-center'><a class='btn btn-xs' href='#'>" +
                "<i class='glyphicon glyphicon-off'></i></a></div>"
            )

    class Media:
        js = ('js/switch-inherit-profile.js',)


class ProbeAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('name', 'url', 'expected_response', 'start_as_healthy')
        }),
        ('Advanced options', {
            'classes': ('collapse',),
            'fields': ('interval', 'timeout', 'window', 'threshold')
        }),
    )


class TimeProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_connections', 'connect_timeout', 'first_byte_timeout', 'between_bytes_timeout')


admin.site.unregister([
    IntervalSchedule,
    CrontabSchedule,
    SolarSchedule,
    ClockedSchedule,
])
admin.site.register(Director, DirectorAdmin)
admin.site.register(Backend, BackendAdmin)
admin.site.register(Probe, ProbeAdmin)
admin.site.register(TimeProfile, TimeProfileAdmin)
