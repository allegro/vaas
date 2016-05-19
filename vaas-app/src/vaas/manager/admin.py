from django.contrib import admin
from vaas.manager.models import Director, Backend, Probe, TimeProfile
from vaas.manager.forms import DirectorModelForm
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from taggit.models import Tag
from taggit.admin import TagAdmin
from tastypie.models import ApiKey
from django.utils.html import format_html
from vaas.monitor.models import BackendStatus
from vaas.manager.signals import switch_state_and_reload


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


def enable_director(modeladmin, request, queryset):
    switch_state_and_reload(queryset, True)


def disable_director(modeladmin, request, queryset):
    switch_state_and_reload(queryset, False)


class DirectorAdmin(admin.ModelAdmin):
    search_fields = ['name', 'route_expression']
    form = DirectorModelForm
    list_display = ('name', 'service', 'get_clusters', 'route_expression', 'probe', 'custom_enabled')
    list_filter = ['cluster__name']
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
        if obj.enabled:
            return format_html(
                "<div class='span13 text-center'>" +
                "<a class='btn btn-mini btn-success' href='#'><i class='icon-ok-circle'></i></a>" +
                "</div>"
            )
        else:
            return format_html(
                "<div class='span13 text-center'><a class='btn btn-mini' href='#'><i class='icon-ban-circle'>" +
                "</i></a></div>"
            )
    custom_enabled.short_description = 'Enabled'


class BackendAdmin(admin.ModelAdmin):
    search_fields = ['address', 'director__name', 'tags__name']
    list_display = ('address', 'port', 'director', 'dc', 'is_healthy', 'custom_enabled', 'get_tags')
    list_filter = ['director__name', 'director__cluster__name', 'dc__symbol']
    actions = [enable_backend, disable_backend, switch_backend_status]
    fieldsets = (
        (None, {
            'fields': ('address', 'port', 'director', 'dc', 'weight', 'tags', 'inherit_time_profile')
        }),
        ('Advanced options', {
            'classes': ('collapse',),
            'fields': ('max_connections', 'connect_timeout', 'first_byte_timeout', 'between_bytes_timeout')
        }),
    )
    backend_status_list = []

    def get_form(self, request, obj=None, **kwargs):
        form = super(BackendAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['dc'].widget.can_add_related = False
        return form

    def get_list_display(self, request):
        self.backend_status_list = BackendStatus.objects.all()
        return super(BackendAdmin, self).get_list_display(request)

    def get_tags(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])

    get_tags.short_description = 'Tags'

    def custom_enabled(self, obj):
        if obj.enabled:
            return format_html(
                "<div class='span13 text-center'>" +
                "<a class='btn btn-mini btn-success' href='#'><i class='icon-ok-circle'></i></a>" +
                "</div>"
            )
        else:
            return format_html(
                "<div class='span13 text-center'><a class='btn btn-mini' href='#'><i class='icon-ban-circle'>" +
                "</i></a></div>"
            )
    custom_enabled.short_description = 'Enabled'

    def is_healthy(self, obj):
        status_list = filter(
            lambda backend_status: backend_status.address == obj.address and backend_status.port == obj.port,
            self.backend_status_list
        )
        if len(status_list) == 1:
            if status_list[0].status == 'Healthy':
                return format_html(
                    "<div class='span13 text-center'><a class='btn btn-mini btn-success' href='#'><i class='icon-ok'>" +
                    "</i></a></div>"
                )
            else:
                return format_html(
                    "<div class='span13 text-center'><a class='btn btn-mini btn-danger' href='#'><i class='icon-off'>" +
                    "</i></a></div>"
                )
        else:
            return format_html(
                "<div class='span13 text-center'><a class='btn btn-mini' href='#'><i class='icon-off'></i></a></div>"
            )


class ProbeAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('name', 'url', 'expected_response')
        }),
        ('Advanced options', {
            'classes': ('collapse',),
            'fields': ('interval', 'timeout', 'window', 'threshold')
        }),
    )


class TimeProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_connections', 'connect_timeout', 'first_byte_timeout', 'between_bytes_timeout')

admin.site.register(Director, DirectorAdmin)
admin.site.register(Backend, BackendAdmin)
admin.site.register(Probe, ProbeAdmin)
admin.site.register(TimeProfile, TimeProfileAdmin)
