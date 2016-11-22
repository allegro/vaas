# -*- coding: utf-8 -*-

from django.test import TestCase

from vaas.manager.models import Probe
from vaas.manager.forms import DirectorModelForm


class DirectorModelFormTests(TestCase):
    def setUp(self):
        Probe.objects.all().delete()

    def test_should_sort_probe_choices_by_label(self):
        Probe.objects.create(name='beta_probe', url='/status')
        Probe.objects.create(name='gamma_probe', url='/status')
        Probe.objects.create(name='alpha_probe', url='/status')

        form = DirectorModelForm()

        all_choices = form.fields['probe'].choices
        labels = [value for key, value in all_choices][1:]
        self.assertEqual(labels, ['alpha_probe (/status)', 'beta_probe (/status)', 'gamma_probe (/status)'])
