import csv

from django.contrib import admin
from vaas.router.models import Route
from vaas.router.forms import RouteModelForm


class RouteAdmin(admin.ModelAdmin):
    form = RouteModelForm
    search_fields = ['condition', 'cluster__name', 'director__name']
    list_display = ['condition', 'director', 'cluster', 'priority', 'action']
    fieldsets = (
        (None, {
            'fields': ('condition', 'priority', 'action', 'cluster', 'director')
        }),
    )


admin.site.register(Route, RouteAdmin)
