from django.test import TestCase
from vaas.router.models import Route
from vaas.router.forms import RouteModelForm
from vaas.manager.models import Director, Probe, TimeProfile
from vaas.cluster.models import LogicalCluster


class MyTests(TestCase):
    def setUp(self):
        self.probe = Probe.objects.create(name='default_probe', url='/ts.1')
        self.cluster1 = LogicalCluster.objects.create(name="first cluster")
        self.cluster2 = LogicalCluster.objects.create(name="second cluster")
        self.director1 = Director.objects.create(
            name='first_gamma',
            route_expression='/first',
            mode='random',
            probe=self.probe,
            time_profile=TimeProfile.objects.create(name='beta')
        )
        self.director2 = Director.objects.create(
            name='second_gamma',
            route_expression='/second',
            mode='random',
            probe=self.probe,
            time_profile=TimeProfile.objects.create(name='alfa')
        )

    def test_should_validate_form_successfully(self):
        route1 = Route.objects.create(
            condition='some condition',
            priority=51,
            director=self.director1,
            action='pass',
        )
        route1.clusters.add(self.cluster1)

        form_data = {
            'condition_0': 'req.url',
            'action': 'pass',
            'condition_1': '~',
            'condition_2': '/test',
            'priority': '50',
            'action': 'pass',
            'clusters': [self.cluster1.pk],
            'director': self.director1.pk,
        }

        form = RouteModelForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_should_validate_form_with_conflict_error(self):
        route1 = Route.objects.create(
            condition='some condition',
            priority=51,
            director=self.director1,
            action='pass',
        )
        route1.clusters.add(self.cluster1)

        form_data = {
            'condition_0': 'req.url',
            'action': 'pass',
            'condition_1': '~',
            'condition_2': '/test',
            'priority': '51',
            'action': 'pass',
            'clusters': [self.cluster1.pk],
            'director': self.director1.pk,
        }

        form = RouteModelForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_should_save_updated_form_shouldnt_conflict_with_self(self):
        form_data = {
            'condition_0': 'req.url',
            'action': 'pass',
            'condition_1': '~',
            'condition_2': '/test',
            'priority': '50',
            'action': 'pass',
            'clusters': [self.cluster1.pk],
            'director': self.director1.pk,
        }

        form = RouteModelForm(data=form_data)
        self.assertTrue(form.is_valid())
        obj = form.save()
        form = RouteModelForm(instance=obj, data=form_data)
        self.assertTrue(form.is_valid())

    def test_should_conflict_on_update_form_with_other_entry(self):
        route1 = Route.objects.create(
            condition='some condition',
            priority=51,
            director=self.director1,
            action='pass',
        )
        route1.clusters.add(self.cluster1)

        form_data = {
            'condition_0': 'req.url',
            'action': 'pass',
            'condition_1': '~',
            'condition_2': '/test',
            'priority': '50',
            'action': 'pass',
            'clusters': [self.cluster1.pk],
            'director': self.director1.pk,
        }

        form = RouteModelForm(data=form_data)
        self.assertTrue(form.is_valid())
        obj = form.save()
        form_data['priority'] = '51'
        form = RouteModelForm(instance=obj, data=form_data)
        self.assertFalse(form.is_valid())
