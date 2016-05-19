# -*- coding: utf-8 -*-

from nose.tools import assert_false, assert_true

from vaas import settings
from vaas.cluster.models import Dc
from vaas.manager.admin import switch_backend_status
from vaas.manager.models import Backend, Director, Probe, TimeProfile


def test_should_switch_backend_status():
    settings.SIGNALS = 'off'
    dc = Dc.objects.create(symbol='dc1')
    probe = Probe.objects.create(name='test_probe', url='/status')
    director = Director.objects.create(
        name='first_service',
        router='req.url',
        route_expression='/first',
        probe=probe,
        time_profile=TimeProfile.objects.create(name='profile')
    )
    Backend.objects.create(address='127.0.1.1', port=80, dc=dc, director=director, enabled=True)
    Backend.objects.create(address='127.0.1.2', port=80, dc=dc, director=director, enabled=False)
    switch_backend_status(None, None, Backend.objects.all())

    objects = Backend.objects.order_by('address')
    assert_false(objects[0].enabled)
    assert_true(objects[1].enabled)
