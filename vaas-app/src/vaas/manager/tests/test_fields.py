# -*- coding: utf-8 -*-

from decimal import Decimal

from django.forms import model_to_dict
from nose.tools import assert_equals
from django.test import TestCase
from django.db import models

from vaas.cluster.models import Dc, LogicalCluster
from vaas.manager.fields import NormalizedDecimalField, generate_choices, make_backend_name
from vaas.manager.models import Backend, Director, Probe, TimeProfile


def create_backend(id, director_name, dc_symbol, address, port):
    dc = Dc.objects.create(name='hellish dc', symbol=dc_symbol)
    probe = Probe.objects.create(name='test_probe', url='/status')
    time_profile = TimeProfile.objects.create(name='alpha_{}'.format(id))
    director = Director.objects.create(
        name=director_name,
        router='req.url',
        route_expression='/first',
        probe=probe,
        time_profile=time_profile
    )
    return Backend.objects.create(id=id, address=address, port=port, dc=dc, director=director)


def test_generate_choices():
    div = Decimal(5)
    expected_choices = [
        (Decimal(0 / div), '0.00'),
        (Decimal(1 / div), '0.20'),
        (Decimal(2 / div), '0.40'),
        (Decimal(3 / div), '0.60'),
        (Decimal(4 / div), '0.80'),
        (Decimal(5 / div), '1.00')
    ]
    assert_equals(expected_choices, generate_choices(0, 6, 5))


def test_should_make_backend_name_which_contain_all_relevant_parts():
    backend = create_backend(10, 'awesomeService', 'dc666', '127.0.20.30', 8080)
    expectedBackendName = "awesomeService_10_dc666_20_30_8080"
    assert_equals(expectedBackendName, make_backend_name(backend))


def test_should_cut_director_if_more_relevant_parts_are_longer_than_maximum_length():
    backend = create_backend(
        11, 'beta_awesomeService', 'dc_longname_11111111111111111111111111111111111111', '127.0.20.30', 8080
    )
    expectedBackendName = "11_dc_longname_11111111111111111111111111111111111111_20_30_8080"
    assert_equals(expectedBackendName, make_backend_name(backend))


def test_should_shorten_director_name_if_director_and_more_relevant_parts_are_longer_than_maximum_length():
    backend = create_backend(
        12, 'awesomeService_alpha', 'dc_longname_111111111111111111111111111111', '127.0.20.30', 8080
    )
    expectedBackendName = "awesome_12_dc_longname_111111111111111111111111111111_20_30_8080"
    assert_equals(expectedBackendName, make_backend_name(backend))


class NormalizedDecimalFieldTest(TestCase):
    def test_should_normalize_values_from_object(self):
        sample_values = [(0, 0.00), (2.5, 2.50), (5, 5.00), (7.5, 7.50), (10, 10.00), (100, 100.00)]

        class SampleModel(models.Model):
            normalized_field = NormalizedDecimalField(default='1', decimal_places=2, max_digits=4)

            class Meta:
                app_label = 'sample_model'

        sample_model = SampleModel()
        for value, database_value in sample_values:
            sample_model.normalized_field = Decimal(database_value)
            dictionary = model_to_dict(sample_model)
            assert_equals(str(value), str(dictionary['normalized_field']))
