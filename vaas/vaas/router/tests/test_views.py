from django.test import TestCase
from vaas.router.models import Route, Redirect
from vaas.manager.models import Director, Probe, TimeProfile
from vaas.cluster.models import LogicalCluster, DomainMapping
from django.urls import reverse

from vaas.router.views import _choose_closest


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
        self.domain_mapping = DomainMapping.objects.create(domain="example.com")

    def test_should_exclude_chosen_priority_from_available_values_if_is_already_occupied(self):
        self.director1.cluster.add(self.cluster1)
        route = Route.objects.create(
            condition='some condition',
            priority=51,
            director=self.director1,
            action='pass',
        )
        route.clusters.add(self.cluster1)

        response = self.client.get(
            reverse('router:route_priorities', args=(self.director1.id, 0, 0)),
            {'clusters': self.cluster1.id}
        )
        self.assertEqual(response.status_code, 200)
        available_values = response.json()['values']
        self.assertTrue(route.priority not in available_values)

    def test_should_exclude_priority_and_suggest_another_if_is_already_occupied_by_route_with_clusters_in_sync(self):
        self.director1.cluster.add(self.cluster1)
        route = Route.objects.create(
            condition='some condition',
            priority=51,
            director=self.director1,
            action='pass',
            clusters_in_sync=True
        )
        # priority=51 should not be available for cluster1 which is related to above route indirectly
        # by assigned director
        response = self.client.get(
            reverse('router:route_priorities', args=(self.director1.id, 0, route.priority)),
            {'clusters': self.cluster1.id}
        )
        self.assertEqual(response.status_code, 200)
        available_values = response.json()['values']
        self.assertTrue(route.priority not in available_values)
        self.assertNotEqual(route.priority, response.json()['choose'])

    def test_should_not_excluded_priority_for_unrelated_cluster(self):
        self.director1.cluster.add(self.cluster1)
        route = Route.objects.create(
            condition='some condition',
            priority=51,
            director=self.director1,
            action='pass',
            clusters_in_sync=True
        )
        # priority=51 should be available for cluster2 which is not related to above route
        response = self.client.get(
            reverse('router:route_priorities', args=(self.director1.id, 0, route.priority)),
            {'clusters': self.cluster2.id}
        )
        self.assertEqual(response.status_code, 200)
        available_values = response.json()['values']
        self.assertTrue(route.priority in available_values)
        self.assertEqual(route.priority, response.json()['choose'])

    def test_should_suggest_new_priority_on_off_cluster_in_sync_if_current_one_is_occupied_by_another_route(self):
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
        # when switching off cluster_in_sync for route_2 availability should be checked for connected cluster2
        # in such case there is conflict with route_1 and new prio should be suggested
        response = self.client.get(
            reverse('router:route_priorities', args=(self.director1.id, route_2.id, route_2.priority)),
            {'clusters': self.cluster2.id}
        )
        self.assertEqual(response.status_code, 200)
        available_values = response.json()['values']
        self.assertTrue(route_2.priority not in available_values)
        self.assertNotEqual(route_2.priority, response.json()['choose'])

    def test_should_suggest_new_priority_for_new_redirect_if_chosen_is_already_occupied(self):
        redirect = Redirect.objects.create(
            src_domain=self.domain_mapping,
            priority=51,
            action=301,
        )
        response = self.client.get(reverse('router:redirect_priorities', args=('example.com', 0, redirect.priority)))
        self.assertEqual(response.status_code, 200)
        available_values = response.json()['values']
        self.assertTrue(redirect.priority not in available_values)
        self.assertNotEqual(redirect.priority, response.json()['choose'])

    def test_should_not_suggest_new_priority_for_editing_redirect_if_chosen_equal_to_saved_in_db(self):
        redirect = Redirect.objects.create(
            src_domain=self.domain_mapping,
            priority=51,
            action=301,
        )
        response = self.client.get(reverse(
            'router:redirect_priorities', args=('example.com', redirect.id, redirect.priority))
        )
        self.assertEqual(response.status_code, 200)
        available_values = response.json()['values']
        self.assertTrue(redirect.priority in available_values)
        self.assertEqual(redirect.priority, response.json()['choose'])

    def test_should_provide_closest_priority(self):
        priorities = [2, 3, 6, 7]
        self.assertEqual(6, _choose_closest(priorities, 5))
        self.assertEqual(3, _choose_closest(priorities, 4))
        self.assertEqual(7, _choose_closest(priorities, 10))
        self.assertEqual(2, _choose_closest(priorities, 1))
