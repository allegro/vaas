from django.test import TestCase
from vaas.router.models import Route
from vaas.manager.models import Director, Probe, TimeProfile
from vaas.cluster.models import LogicalCluster
from django.urls import reverse


class TestPrioritiesView(TestCase):

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

    def test_should_check_if_taken_priority_is_excluded_from_available_values(self):
        self.director1.cluster.add(self.cluster1)
        route = Route.objects.create(
            condition='some condition',
            priority=51,
            director=self.director1,
            action='pass',
        )
        route.clusters.add(self.cluster1)

        response = self.client.get(
            reverse('router:priorities', args=(self.director1.id, 0, 0)),
            {'clusters': self.cluster1.id}
        )
        self.assertEqual(response.status_code, 200)
        available_values = response.json()['values']
        self.assertTrue(route.priority not in available_values)

    def test_should_check_if_taken_priority_is_excluded_from_available_values_when_clusters_in_sync(self):
        self.director1.cluster.add(self.cluster1)
        route = Route.objects.create(
            condition='some condition',
            priority=51,
            director=self.director1,
            action='pass',
            clusters_in_sync=True
        )
        route.clusters.add(self.cluster2)

        response = self.client.get(
            reverse('router:priorities', args=(self.director1.id, 0, 0)),
            {'clusters': self.cluster1.id}
        )
        self.assertEqual(response.status_code, 200)
        available_values = response.json()['values']
        self.assertTrue(route.priority not in available_values)

    def test_should_check_if_taken_priority_excluded_for_director_cluster_when_clusters_in_sync(self):
        self.director1.cluster.add(self.cluster1)
        route = Route.objects.create(
            condition='some condition',
            priority=51,
            director=self.director1,
            action='pass',
            clusters_in_sync=True
        )
        route.clusters.add(self.cluster2)

        response = self.client.get(
            reverse('router:priorities', args=(self.director1.id, 0, 0)),
            {'clusters': self.cluster2.id}
        )
        self.assertEqual(response.status_code, 200)
        available_values = response.json()['values']
        self.assertTrue(route.priority in available_values)

    def test_should_check_if_priority_calculated_properly_when_disabling_clusters_in_sync(self):
        self.director1.cluster.add(self.cluster1)
        route_1 = Route.objects.create(
            condition='some condition',
            priority=51,
            director=self.director1,
            action='pass',
        )
        route_1.clusters.add(self.cluster2)

        route_2 = Route.objects.create(
            condition='some condition',
            priority=51,
            director=self.director1,
            action='pass',
            clusters_in_sync=True
        )
        route_2.clusters.add(self.cluster2)

        response = self.client.get(
            reverse('router:priorities', args=(self.director1.id, route_2.id, route_2.priority)),
            {'clusters': self.cluster2.id}
        )
        self.assertEqual(response.status_code, 200)
        available_values = response.json()['values']
        self.assertTrue(route_2.priority not in available_values)
