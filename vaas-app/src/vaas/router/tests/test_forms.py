from django.test import TestCase
from vaas.router.models import Route
from vaas.router.forms import RouteModelForm
from vaas.manager.models import Director, Probe, TimeProfile
from vaas.cluster.models import  LogicalCluster

class MyTests(TestCase):
    def test_forms(self):
        probe = Probe.objects.create(name='default_probe', url='/ts.1')
        director1 = Director.objects.create(
            name='first_gamma',
            route_expression='/first',
            mode='random',
            probe=probe,
            time_profile=TimeProfile.objects.create(name='beta')
        )
        cluster1 = LogicalCluster.objects.create(name="second cluster")

        form_data = {
            'condition_0': 'req.url',
            'action': 'pass',
            'condition_1': '~',
            'condition_2': '/test',
            'priority': '50',
            'action':'pass',
            'clusters': [cluster1.pk],
            'director': director1.pk,
        }

        route1 = Route.objects.create(
            condition='some condition',
            priority=50,
            director=director1,
            action='pass',
        )
        route1.clusters.add(cluster1)

        form = RouteModelForm(data=form_data)
        self.assertTrue(form.is_valid())

