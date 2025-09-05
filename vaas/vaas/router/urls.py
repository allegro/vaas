# -*- coding: utf-8 -*-

from django.urls import path

from vaas.router.views import allowed_redirect_priorities, allowed_route_priorities, add_condition

urlpatterns = [
    path(
        'route/priorities/<int:director_id>/<int:route_id>/<int:current>/',
        allowed_route_priorities,
        name='route_priorities'
    ),
    path(
        'redirect/priorities/<str:domain>/<int:redirect_id>/<int:current>/',
        allowed_redirect_priorities,
        name='redirect_priorities'
    ),
    path(
        "add_condition/",
        add_condition,
        name="add_condition"
    ),
]
