# -*- coding: utf-8 -*-

import json
from django.http import HttpResponse
from vaas.router.models import Route
from vaas.manager.models import Director


def priorities(request, director_id, route_id, current):
    clusters_sync = request.GET.get("clusters_sync")
    if clusters_sync:
        clusters = Director.objects.get(pk=director_id).cluster.values_list('id', flat=True)
    else:
        clusters = request.GET.getlist("clusters")
    routes_with_sync = Route.objects.filter(clusters_in_sync=True, director__id=director_id,
                                            director__cluster__in=clusters)
    routes_without_sync = Route.objects.filter(clusters_in_sync=False, director__id=director_id,
                                               clusters__id__in=clusters)

    routes = routes_with_sync | routes_without_sync

    priority_list = list(range(1, 500))
    for route in routes:
        if route.id != int(route_id):
            if route.priority in priority_list:
                priority_list.remove(route.priority)
    if int(current) not in priority_list:
        current = priority_list[int(len(priority_list) / 2)]

    return HttpResponse(json.dumps({'values': priority_list, 'choose': current}), content_type="application/json")
