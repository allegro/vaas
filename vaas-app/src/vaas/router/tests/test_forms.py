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
            envoy_service_name='first_gamma',
            route_expression='/first',
            mode='random',
            probe=self.probe,
            time_profile=TimeProfile.objects.create(name='beta')
        )
        self.director2 = Director.objects.create(
            name='second_gamma',
            envoy_service_name='second_gamma',
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
            'condition_0_0': 'req.url',
            'action': 'pass',
            'condition_0_1': '~',
            'condition_0_2': '/test',
            'priority': '50',
            'action': 'pass',
            'clusters': [self.cluster1.pk],
            'director': self.director1.pk,
        }

        form = RouteModelForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual('req.url ~ "/test"', form.cleaned_data['condition'])

    def test_should_validate_form_with_complex_condition_successfully(self):
        route1 = Route.objects.create(
            condition='some condition',
            priority=51,
            director=self.director1,
            action='pass',
        )
        route1.clusters.add(self.cluster1)

        form_data = {
            'condition_0_0': 'req.url',
            'condition_0_1': '~',
            'condition_0_2': '/test',
            'condition_1_0': 'req.http.Host',
            'condition_1_1': '==',
            'condition_1_2': 'example.com',
            'action': 'pass',
            'priority': '50',
            'action': 'pass',
            'clusters': [self.cluster1.pk],
            'director': self.director1.pk,
        }

        form = RouteModelForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual('req.url ~ "/test" && req.http.Host == "example.com"', form.cleaned_data['condition'])

    def test_should_validate_form_with_conflict_error(self):
        route1 = Route.objects.create(
            condition='some condition',
            priority=51,
            director=self.director1,
            action='pass',
        )
        route1.clusters.add(self.cluster1)

        form_data = {
            'condition_0_0': 'req.url',
            'action': 'pass',
            'condition_0_1': '~',
            'condition_0_2': '/test',
            'priority': '51',
            'action': 'pass',
            'clusters': [self.cluster1.pk],
            'director': self.director1.pk,
        }

        form = RouteModelForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_should_save_updated_form_shouldnt_conflict_with_self(self):
        form_data = {
            'condition_0_0': 'req.url',
            'action': 'pass',
            'condition_0_1': '~',
            'condition_0_2': '/test',
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
            'action': 'pass',
            'condition_0_0': 'req.url',
            'condition_0_1': '~',
            'condition_0_2': '/test',
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

    def test_should_validate_form_with_conflict_error_when_other_entry_with_cluster_sync(self):
        self.director1.cluster.add(self.cluster2)
        route1 = Route.objects.create(
            condition='some condition',
            priority=51,
            director=self.director1,
            action='pass',
            clusters_in_sync=True,
        )
        route1.clusters.add(self.cluster1)

        form_data = {
            'action': 'pass',
            'condition_0_0': 'req.url',
            'condition_0_1': '~',
            'condition_0_2': '/test',
            'priority': '51',
            'action': 'pass',
            'clusters': [self.cluster2.pk],
            'director': self.director1.pk,
        }

        form = RouteModelForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_should_validate_form_with_conflict_error_when_update_and_disable_cluster_sync(self):
        self.director1.cluster.add(self.cluster2)
        route1 = Route.objects.create(
            condition='some condition"',
            priority=51,
            director=self.director1,
            action='pass',
        )
        route1.clusters.add(self.cluster1)

        form_data = {
            'action': 'pass',
            'condition_0_0': 'req.url',
            'condition_0_1': '~',
            'condition_0_2': '/test',
            'priority': '51',
            'action': 'pass',
            'clusters': [self.cluster1.pk],
            'director': self.director1.pk,
            'clusters_in_sync': True,
        }

        form = RouteModelForm(data=form_data)
        self.assertTrue(form.is_valid())
        obj = form.save()
        form_data['clusters_in_sync'] = False
        form = RouteModelForm(instance=obj, data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors,
                         {'__all__': ['This combination of director, cluster and priority already exists']})

    def test_should_validate_form_with_conflict_error_when_update_and_enable_cluster_sync(self):
        self.director1.cluster.add(self.cluster1)
        route1 = Route.objects.create(
            condition='some condition"',
            priority=51,
            director=self.director1,
            action='pass',
        )
        route1.clusters.add(self.cluster1)

        form_data = {
            'action': 'pass',
            'condition_0_0': 'req.url',
            'condition_0_1': '~',
            'condition_0_2': '/test',
            'priority': '51',
            'action': 'pass',
            'clusters': [self.cluster2.pk],
            'director': self.director1.pk,
            'clusters_in_sync': False,
        }

        form = RouteModelForm(data=form_data)
        self.assertTrue(form.is_valid())
        obj = form.save()
        form_data['clusters_in_sync'] = True
        form = RouteModelForm(instance=obj, data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors,
                         {'__all__': ['This combination of director, cluster and priority already exists']})

    def test_should_check_if_route_clusters_untouched_when_enable_cluster_sync(self):
        self.director1.cluster.add(self.cluster1)
        route1 = Route.objects.create(
            condition='some condition"',
            priority=51,
            director=self.director1,
            action='pass',
        )
        route1.clusters.add(self.cluster1)

        form_data = {
            'action': 'pass',
            'condition_0_0': 'req.url',
            'condition_0_1': '~',
            'condition_0_2': '/test',
            'priority': '50',
            'action': 'pass',
            'clusters': [self.cluster2.pk],
            'director': self.director1.pk,
            'clusters_in_sync': False,
        }

        form = RouteModelForm(data=form_data)
        self.assertTrue(form.is_valid())
        obj = form.save()
        form_data['clusters'] = [self.cluster1.pk]
        form_data['clusters_in_sync'] = True
        form = RouteModelForm(instance=obj, data=form_data)
        self.assertTrue(form.is_valid())
        print(form.cleaned_data['clusters'])
        self.assertEqual(list(form.cleaned_data['clusters']), [self.cluster2])
