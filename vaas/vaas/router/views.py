# -*- coding: utf-8 -*-

import json
from typing import Set, List

from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_GET
from django.template.loader import render_to_string

from vaas.router.models import Route, Redirect, provide_route_configuration
from vaas.manager.models import Director
from vaas.adminext.widgets import ConditionWidget

MAX_PRIORITY = 500


def allowed_route_priorities(request: HttpRequest, director_id: int, route_id: int, current: int) -> HttpResponse:
    clusters = request.GET.getlist("clusters")
    if request.GET.get("clusters_sync"):
        clusters = Director.objects.filter(pk=director_id).values_list('cluster__id', flat=True)

    existing_priorities = set(
        Route.objects.filter(
            clusters_in_sync=True, director__cluster__in=clusters
        ).exclude(id=route_id).values_list('priority', flat=True) | Route.objects.filter(
            clusters_in_sync=False, clusters__id__in=clusters
        ).exclude(id=route_id).values_list('priority', flat=True)
    )
    return _provide_priority_response(existing_priorities, current)


def allowed_redirect_priorities(request: HttpRequest, domain: str, redirect_id: int, current: int) -> HttpResponse:
    existing_priorities = set(
        list(Redirect.objects.filter(src_domain__domain=domain).exclude(id=redirect_id).values_list(
            'priority', flat=True
        ))
    )
    return _provide_priority_response(existing_priorities, current)

@require_GET
def add_condition(request: HttpRequest) -> HttpResponse:
    configuration = provide_route_configuration()
    variables = tuple((left.left, left.name) for left in configuration.lefts)
    operators = tuple((operator.operator, operator.name) for operator in configuration.operators)
    widget = ConditionWidget(variables, operators)
    print("Widget template name:", widget.template_name)
    print("Widget attributes:", widget.attrs) # empty
    print("Subwidgets:", widget.widgets) # three, correct
    print("boss", widget.template_name)
    print("0th", widget.widgets[0].attrs)
    html_content = render_to_string(
        widget.template_name,
        {
            "widget": widget,
            'value': None,
        }
    )
    # html_content = "<button>button_content</button>"
    return HttpResponse(json.dumps({'html': html_content}), content_type="application/json")

def _provide_priority_response(existing_priorities: Set[int], current: int) -> HttpResponse:
    priorities_set = set(range(1, MAX_PRIORITY))
    priorities = list(priorities_set.difference(existing_priorities))
    sorted(priorities)
    if current not in priorities:
        current = _choose_closest(priorities, current)

    return HttpResponse(json.dumps({'values': priorities, 'choose': current}), content_type="application/json")


def _choose_closest(priorities: List[int], current) -> int:
    result = -1
    diff = MAX_PRIORITY
    for priority in priorities:
        current_diff = abs(priority - current)
        if current_diff > diff:
            break
        diff = current_diff
        result = priority
    return result
