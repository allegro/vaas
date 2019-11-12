# -*- coding: utf-8 -*-

import json
from django.http import HttpResponse
from vaas.router.models import Route


def priorities(request, director_id, cluster_id, route_id, current):
    priority_list = list(range(1, 100))
    for route in Route.objects.filter(director__id=director_id, clusters__id=cluster_id):
        if route.id != int(route_id):
            priority_list.remove(route.priority)
    if int(current) not in priority_list:
        current = priority_list[int(len(priority_list) / 2)]

    return HttpResponse(json.dumps({'values': priority_list, 'choose': current}), content_type="application/json")
