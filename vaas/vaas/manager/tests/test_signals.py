# -*- coding: utf-8 -*-

from unittest.mock import Mock, call, patch, MagicMock
from django.conf import settings
from django.test import TestCase

from vaas.manager.models import Director, Backend, Probe, TimeProfile
from vaas.router.models import Route
from vaas.cluster.models import Dc, LogicalCluster, VarnishServer, VclTemplate, VclTemplateBlock
from vaas.manager.signals import switch_state_and_reload, regenerate_and_reload_vcl, vcl_update, model_update


class TestSignals(TestCase):

    def test_switch_state_and_reload_cluster_filter_for_backend(self):
        cluster1 = LogicalCluster.objects.create(name="first cluster")
        """
        Created, but not used, just to check if cluster filtering works.
        """
        LogicalCluster.objects.create(name="second cluster")
        dc1 = Dc.objects.create(symbol='dc3', name='First datacenter')
        probe = Probe.objects.create(name='default_probe', url='/ts.1')
        director1 = Director.objects.create(
            name='first_gamma',
            route_expression='/first',
            mode='random',
            probe=probe,
            time_profile=TimeProfile.objects.create(name='beta')
        )
        backend1 = Backend.objects.create(
            dc=dc1,
            director=director1,
            address='192.168.200.10',
            port=8080,
            weight=1
        )
        director1.cluster.add(cluster1)

        queryset = Backend.objects.all().filter(id=backend1.id)
        queryset.update = Mock()

        with patch(
                'vaas.manager.signals.regenerate_and_reload_vcl',
                return_value=None
        ) as regenerate_and_reload_vcl_mock:
            switch_state_and_reload(queryset, True)
            self.assertEqual([call(enabled=True)], queryset.update.call_args_list)
            self.assertEqual([call([cluster1])], regenerate_and_reload_vcl_mock.call_args_list)

    def test_should_not_reload_clusters_if_service_mesh_is_enabled_and_director_is_reachable_via_sm(self):
        cluster_with_sm = LogicalCluster.objects.create(name="cluster_with_sm", service_mesh_routing=True)
        cluster_without_sm = LogicalCluster.objects.create(name="cluster_without_sm", service_mesh_routing=False)
        dc1 = Dc.objects.create(symbol='dc3', name='First datacenter')
        probe = Probe.objects.create(name='default_probe', url='/ts.1')
        director_reachable_via_sm = Director.objects.create(
            name='first_gamma',
            route_expression='/first',
            mode='random',
            probe=probe,
            time_profile=TimeProfile.objects.create(name='beta'),
            reachable_via_service_mesh=True

        )
        backend1 = Backend.objects.create(
            dc=dc1,
            director=director_reachable_via_sm,
            address='192.168.200.10',
            port=8080,
            weight=1
        )
        director_reachable_via_sm.cluster.add(cluster_with_sm)
        director_reachable_via_sm.cluster.add(cluster_without_sm)

        queryset = Backend.objects.all().filter(id=backend1.id)
        queryset.update = Mock()

        with patch(
                'vaas.manager.signals.regenerate_and_reload_vcl',
                return_value=None
        ) as regenerate_and_reload_vcl_mock:
            switch_state_and_reload(queryset, True)
            self.assertEqual([call(enabled=True)], queryset.update.call_args_list)
            self.assertEqual([call([cluster_without_sm])], regenerate_and_reload_vcl_mock.call_args_list)

    def test_switch_state_and_reload_with_empty_list(self):
        queryset = MagicMock()
        queryset.update = Mock()
        with patch(
                'vaas.manager.signals.regenerate_and_reload_vcl',
                return_value=None
        ) as regenerate_and_reload_vcl_mock:
            switch_state_and_reload(queryset, True)
            self.assertEqual([call(enabled=True)],queryset.update.call_args_list)
            """
            shouldn't refresh any cluster, because of empty list
            """
            self.assertEqual([call([])], regenerate_and_reload_vcl_mock.call_args_list)

    def test_regenerate_and_reload_vcl_if_can_obtain_request(self):
        request = MagicMock(id=10)

        with patch('vaas.manager.signals.get_current_request', return_value=request):
            with patch(
                    'vaas.manager.signals.VclRefreshState.set_refresh',
                    return_value=None
            ) as vcl_refresh_mock:
                clusters = []
                regenerate_and_reload_vcl(clusters)
                self.assertEqual([call(request.id, [])], vcl_refresh_mock.call_args_list)

    def test_regenerate_and_reload_vcl_if_cannot_obtain_request(self):
        with patch('vaas.manager.signals.get_current_request', return_value=None):
            with patch(
                    'vaas.manager.signals.VclRefreshState.set_refresh',
                    return_value=None
            ) as vcl_refresh_mock:
                clusters = []
                regenerate_and_reload_vcl(clusters)
                self.assertEqual([], vcl_refresh_mock.call_args_list)

    def test_vcl_update_if_sender_allowed(self):
        settings.SIGNALS = 'on'

        probe1 = Probe.objects.create(name='test_beta_probe', url='/status')
        director1 = Director.objects.create(
            name='first_beta',
            router='req.url',
            route_expression='/first',
            probe=probe1,
            active_active=False,
            mode='round-robin',
            remove_path=False,
            time_profile=TimeProfile.objects.create(name='gamma')
        )

        with patch('vaas.manager.signals.regenerate_and_reload_vcl',
                   return_value=None) as regenerate_and_reload_vcl_mock:
            kwargs = {'instance': director1}
            vcl_update(Director, **kwargs)
            self.assertEqual([call([])], regenerate_and_reload_vcl_mock.call_args_list)

        settings.SIGNALS = 'off'

    def test_vcl_update_cluster_filter_for_director(self):
        settings.SIGNALS = 'on'

        cluster1 = LogicalCluster.objects.create(name="alpha cluster")
        """
        Created, but not used, just to check if cluster filtering works.
        """
        LogicalCluster.objects.create(name="beta cluster")

        probe1 = Probe.objects.create(name='test_alpha_probe', url='/status')
        director1 = Director.objects.create(
            name='first_alpha',
            router='req.url',
            route_expression='/first',
            probe=probe1,
            active_active=False,
            mode='round-robin',
            remove_path=False,
            time_profile=TimeProfile.objects.create(name='alpha')
        )
        director1.cluster.add(cluster1)

        with patch('vaas.manager.signals.regenerate_and_reload_vcl',
                   return_value=None) as regenerate_and_reload_vcl_mock:
            kwargs = {'instance': director1}
            vcl_update(Director, **kwargs)
            self.assertEqual([call([cluster1])], regenerate_and_reload_vcl_mock.call_args_list)

        settings.SIGNALS = 'off'

    def test_vcl_update_clusters_for_time_profile_change(self):
        settings.SIGNALS = 'on'

        cluster1 = LogicalCluster.objects.create(name="epsilon cluster")
        """
        Created, but not used, just to check if cluster filtering works.
        """
        LogicalCluster.objects.create(name="epsilon2 cluster")

        probe1 = Probe.objects.create(name='test_epsilon_probe', url='/status')
        time_profile = TimeProfile.objects.create(name='test_profile')
        director1 = Director.objects.create(
            name='first_service_epsilon',
            service='first service epsilon',
            router='req.url',
            route_expression='/first',
            probe=probe1,
            active_active=False,
            mode='round-robin',
            remove_path=False,
            time_profile=time_profile
        )
        director1.cluster.add(cluster1)

        with patch('vaas.manager.signals.regenerate_and_reload_vcl',
                   return_value=None) as regenerate_and_reload_vcl_mock:
            kwargs = {'instance': time_profile}
            vcl_update(TimeProfile, **kwargs)
            self.assertEqual([call([cluster1])], regenerate_and_reload_vcl_mock.call_args_list)

        settings.SIGNALS = 'off'

    def test_vcl_update_if_sender_not_allowed(self):
        settings.SIGNALS = 'on'
        with patch('vaas.manager.signals.regenerate_and_reload_vcl',
                   return_value=None) as regenerate_and_reload_vcl_mock:
            vcl_update(None)
            self.assertEqual([], regenerate_and_reload_vcl_mock.call_args_list)
        settings.SIGNALS = 'off'

    def test_vcl_update_cluster_filter_for_vcltemplate(self):
        settings.SIGNALS = 'on'

        cluster1 = LogicalCluster.objects.create(name="1 cluster")
        """
        Created, but not used, just to check if cluster filtering works.
        """
        LogicalCluster.objects.create(name="2 cluster")
        template = VclTemplate.objects.create()

        VarnishServer.objects.create(
            ip='127.0.0.1',
            port='6082',
            hostname='localhost-1',
            secret='secret-1',
            dc=Dc.objects.create(name='Tokyo', symbol='dc2'),
            cluster=cluster1,
            template=template
        )

        with patch('vaas.manager.signals.regenerate_and_reload_vcl',
                   return_value=None) as regenerate_and_reload_vcl_mock:
            kwargs = {'instance': template}
            vcl_update(VclTemplate, **kwargs)
            self.assertEqual([call([cluster1])], regenerate_and_reload_vcl_mock.call_args_list)

        settings.SIGNALS = 'off'

    def test_backend_change_should_trigger_vcl_change_for_clusters_where_service_mesh_is_disabled(self):
        settings.SIGNALS = 'on'
        cluster_with_sm = LogicalCluster.objects.create(name="cluster_with_sm", service_mesh_routing=True)
        cluster_without_sm = LogicalCluster.objects.create(name="cluster_without_sm", service_mesh_routing=False)

        dc1 = Dc.objects.create(symbol='dc3', name='First datacenter')
        probe = Probe.objects.create(name='default_probe', url='/ts.1')
        director_reachable_via_sm = Director.objects.create(
            name='first_gamma',
            route_expression='/first',
            mode='random',
            probe=probe,
            time_profile=TimeProfile.objects.create(name='beta'),
            reachable_via_service_mesh=True

        )
        backend1 = Backend.objects.create(
            dc=dc1,
            director=director_reachable_via_sm,
            address='192.168.200.10',
            port=8080,
            weight=1
        )
        director_reachable_via_sm.cluster.add(cluster_with_sm)
        director_reachable_via_sm.cluster.add(cluster_without_sm)

        with patch('vaas.manager.signals.regenerate_and_reload_vcl',
                   return_value=None) as regenerate_and_reload_vcl_mock:
            kwargs = {'instance': backend1}
            vcl_update(Backend, **kwargs)
            self.assertEqual([call([cluster_without_sm])], regenerate_and_reload_vcl_mock.call_args_list)

        settings.SIGNALS = 'off'

    def test_vcl_update_cluster_filter_for_vcltemplateblock(self):
        settings.SIGNALS = 'on'

        cluster1 = LogicalCluster.objects.create(name="3 cluster")
        """
        Created, but not used, just to check if cluster filtering works.
        """
        LogicalCluster.objects.create(name="4 cluster")
        template = VclTemplate.objects.create(name="template")
        template_block = VclTemplateBlock.objects.create(template=template)

        VarnishServer.objects.create(
            ip='127.0.0.2',
            port='6082',
            hostname='localhost-1',
            secret='secret-1',
            dc=Dc.objects.create(name='Tokyo', symbol='dc4'),
            cluster=cluster1,
            template=template
        )

        with patch('vaas.manager.signals.regenerate_and_reload_vcl',
                   return_value=None) as regenerate_and_reload_vcl_mock:
            kwargs = {'instance': template_block}
            vcl_update(VclTemplateBlock, **kwargs)
            self.assertEqual([call([cluster1])], regenerate_and_reload_vcl_mock.call_args_list)

        settings.SIGNALS = 'off'

    def test_vcl_update_cluster_filter_for_director_via_related_manager(self):
        settings.SIGNALS = 'on'

        cluster1 = LogicalCluster.objects.create(name="cluster1")
        """
        Created, but not used, just to check if cluster filtering works.
        """
        LogicalCluster.objects.create(name="cluster2")

        probe1 = Probe.objects.create(name='test_director1_probe', url='/status')
        director1 = Director.objects.create(
            name='director1',
            router='req.url',
            route_expression='/first',
            probe=probe1,
            active_active=False,
            mode='round-robin',
            remove_path=False,
            time_profile=TimeProfile.objects.create(name='timeprofile')
        )
        director1.cluster.add(cluster1)

        with patch('vaas.manager.signals.regenerate_and_reload_vcl',
                   return_value=None) as regenerate_and_reload_vcl_mock:
            kwargs = {'instance': director1, 'action': 'post_add'}
            model_update(**kwargs)
            self.assertEqual([call([cluster1])], regenerate_and_reload_vcl_mock.call_args_list)

        settings.SIGNALS = 'off'

    def test_vcl_update_only_changed_clusters_for_director(self):
        settings.SIGNALS = 'on'

        cluster3 = LogicalCluster.objects.create(name="cluster3")
        cluster4 = LogicalCluster.objects.create(name="cluster4")
        cluster5 = LogicalCluster.objects.create(name="cluster5")

        probe1 = Probe.objects.create(name='test_director2_probe', url='/status')
        director2 = Director.objects.create(
            name='director2',
            router='req.url',
            route_expression='/first',
            probe=probe1,
            active_active=False,
            mode='round-robin',
            remove_path=False,
            time_profile=TimeProfile.objects.create(name='timeprofile2')
        )
        director2.cluster.add(cluster3, cluster4)
        director2.save()

        director2.old_clusters = [cluster3, cluster4]
        director2.new_clusters = [cluster4, cluster5]
        director2.new_data = {'cluster': object()}

        with patch('vaas.manager.signals.regenerate_and_reload_vcl',
                   return_value=None) as regenerate_and_reload_vcl_mock:
            director2.cluster.remove(cluster3)
            self.assertEqual([call([cluster3])], regenerate_and_reload_vcl_mock.call_args_list)

        with patch('vaas.manager.signals.regenerate_and_reload_vcl',
                   return_value=None) as regenerate_and_reload_vcl_mock:
            director2.cluster.add(cluster5)
            self.assertEqual([call([cluster5])],regenerate_and_reload_vcl_mock.call_args_list)

        # should update all clusters when change metadata is not set

        director2.cluster.clear()
        director2.cluster.add(cluster3, cluster4)
        director2.save()
        del director2.new_clusters
        del director2.old_clusters

        with patch('vaas.manager.signals.regenerate_and_reload_vcl',
                   return_value=None) as regenerate_and_reload_vcl_mock:
            director2.cluster.remove(cluster3)
            self.assertEqual([call([cluster3, cluster4])], regenerate_and_reload_vcl_mock.call_args_list)

        with patch('vaas.manager.signals.regenerate_and_reload_vcl',
                   return_value=None) as regenerate_and_reload_vcl_mock:
            director2.cluster.add(cluster5)
            self.assertEqual([call([cluster4, cluster5])], regenerate_and_reload_vcl_mock.call_args_list)

        settings.SIGNALS = 'off'

    def test_vcl_update_when_director_will_be_deleted(self):
        settings.SIGNALS = 'on'

        cluster1 = LogicalCluster.objects.create(name="cluster_director")

        probe1 = Probe.objects.create(name='test_director3_probe', url='/status')
        director3 = Director.objects.create(
            name='director3',
            router='req.url',
            route_expression='/first',
            probe=probe1,
            active_active=False,
            mode='round-robin',
            remove_path=False,
            time_profile=TimeProfile.objects.create(name='timeprofile3')
        )
        director3.cluster.add(cluster1)

        with patch('vaas.manager.signals.regenerate_and_reload_vcl',
                   return_value=None) as regenerate_and_reload_vcl_mock:
            director3.delete()
            # We check that regenerate_and_reload_vcl was run in pre_save and post_save signal
            self.assertEqual([call([cluster1]), call([])], regenerate_and_reload_vcl_mock.call_args_list)

    def test_vcl_update_when_route_will_be_deleted(self):
        settings.SIGNALS = 'on'

        cluster1 = LogicalCluster.objects.create(name="cluster_route")

        probe1 = Probe.objects.create(name='test_director4_probe', url='/status')
        director4 = Director.objects.create(
            name='director4',
            router='req.url',
            route_expression='/first',
            probe=probe1,
            active_active=False,
            mode='round-robin',
            remove_path=False,
            time_profile=TimeProfile.objects.create(name='timeprofile4')
        )
        route1 = Route.objects.create(
            condition='some condition',
            priority=51,
            director=director4,
            action='pass',
        )
        route1.clusters.add(cluster1)

        with patch('vaas.manager.signals.regenerate_and_reload_vcl',
                   return_value=None) as regenerate_and_reload_vcl_mock:
            route1.delete()
            # We check that regenerate_and_reload_vcl was run in pre_save and post_save signal
            self.assertEqual([call([cluster1]), call([])], regenerate_and_reload_vcl_mock.call_args_list)

    def test_vcl_update_when_route_with_director_cluster_sync_deleted(self):
        settings.SIGNALS = 'on'

        cluster_route = LogicalCluster.objects.create(name="cluster_route")
        cluster_director = LogicalCluster.objects.create(name="cluster_director")

        probe1 = Probe.objects.create(name='test_director4_probe_1', url='/status')
        director4 = Director.objects.create(
            name='director4',
            router='req.url',
            route_expression='/first',
            probe=probe1,
            active_active=False,
            mode='round-robin',
            remove_path=False,
            time_profile=TimeProfile.objects.create(name='timeprofile4')
        )
        director4.cluster.add(cluster_director)

        route1 = Route.objects.create(
            condition='some condition',
            priority=51,
            director=director4,
            action='pass',
            clusters_in_sync=True,
        )
        route1.clusters.add(cluster_route)

        with patch('vaas.manager.signals.regenerate_and_reload_vcl',
                   return_value=None) as regenerate_and_reload_vcl_mock:
            route1.delete()
            # We check that regenerate_and_reload_vcl was run in pre_save and post_save signal
            self.assertEqual([call([cluster_director]), call([cluster_director])], regenerate_and_reload_vcl_mock.call_args_list)

    def test_vcl_update_when_route_with_director_cluster_sync_enabled_or_disabled_existing_route(self):
        settings.SIGNALS = 'on'

        cluster_route = LogicalCluster.objects.create(name="cluster_route")
        cluster_director = LogicalCluster.objects.create(name="cluster_director")

        probe1 = Probe.objects.create(name='test_director4_probe_1', url='/status')
        director4 = Director.objects.create(
            name='director4',
            router='req.url',
            route_expression='/first',
            probe=probe1,
            active_active=False,
            mode='round-robin',
            remove_path=False,
            time_profile=TimeProfile.objects.create(name='timeprofile4')
        )
        director4.cluster.add(cluster_director)

        route1 = Route.objects.create(
            condition='some condition',
            priority=51,
            director=director4,
            action='pass',
            clusters_in_sync=False,
        )
        route1.clusters.add(cluster_route)
        route1.save()

        with patch('vaas.manager.signals.regenerate_and_reload_vcl',
                   return_value=None) as regenerate_and_reload_vcl_mock:
            route1.clusters_in_sync = True
            route1.save()
            # We check that regenerate_and_reload_vcl was run in pre_save and post_save signal
            self.assertEqual([call([cluster_route]), call([cluster_director])], regenerate_and_reload_vcl_mock.call_args_list)

        with patch('vaas.manager.signals.regenerate_and_reload_vcl',
                   return_value=None) as regenerate_and_reload_vcl_mock:
            route1.clusters_in_sync = False
            route1.save()
            # We check that regenerate_and_reload_vcl was run in pre_save and post_save signal
            self.assertEqual([call([cluster_director]), call([cluster_route])], regenerate_and_reload_vcl_mock.call_args_list)
