# -*- coding: utf-8 -*-

import os
from factory.django import DjangoModelFactory
from factory import Sequence, SubFactory
from unittest.mock import Mock, patch
from django.test import TestCase
from vaas.vcl.renderer import Vcl, VclVariableExpander, VclTagExpander, VclTagBuilder, VclRenderer, VclRendererInput
from vaas.manager.models import Director, Probe, Backend, TimeProfile
from vaas.router.models import Redirect, Route
from vaas.cluster.models import DomainMapping, VclTemplate, VclTemplateBlock, Dc, VarnishServer, LogicalCluster, \
    VclVariable
from django.conf import settings

md5_mock = Mock()
md5_mock.hexdigest = Mock(return_value="ca5ef")


class VclTest(TestCase):
    @patch('vaas.vcl.renderer.hashlib.md5', Mock(return_value=md5_mock))
    def test_name_should_contain_version_based_on_digest(self):
        vcl = Vcl('some_content', 'new-vcl')
        assert vcl.name == 'new-vcl-vol_ca5ef'

    @patch('vaas.vcl.renderer.hashlib.md5', Mock(return_value=md5_mock))
    def test_should_compare_versions(self):
        vcl = Vcl('some_content', 'new-vcl')
        assert vcl.compare_version('other-vcl-vol_ca5ef')


class VclTagExpanderTest(TestCase):
    def setUp(self):
        self.vcl_template4 = VclTemplate.objects.create(name='default-template-v4', version='4.0')
        VclTemplateBlock.objects.create(tag='ACL', content='## ACL custom content ##', template=self.vcl_template4)

    def test_tag_should_be_expanded_from_file_template(self):
        tag_expander = VclTagExpander('VCL', 'VCL', VclRendererInput())
        expected_v4 = '''\
# Marker to tell the VCL compiler that this VCL has been adapted to the
# new 4.0 format.
vcl 4.0;

import std;
import directors;

<HEADERS/>
<ACL/>
<DIRECTORS/>
<VAAS_STATUS/>
<RECV/>
<VCL_PIPE/>
<OTHER_FUNCTIONS/>
<EMPTY_DIRECTOR_SYNTH/>'''
        assert tag_expander.expand(self.vcl_template4) == expected_v4

    def test_tag_should_be_expanded_from_database(self):
        tag_expander = VclTagExpander('ACL', 'ACL', VclRendererInput(), can_overwrite=True)
        assert tag_expander.expand(self.vcl_template4) == '## ACL custom content ##'


class DcFactory(DjangoModelFactory):
    class Meta:
        model = Dc

    name = Sequence(lambda t: "Town%d" % t)
    symbol = Sequence(lambda t: "dc%d" % t)


class LogicalClusterFactory(DjangoModelFactory):
    class Meta:
        model = LogicalCluster

    name = 'cluster1_siteA_test'


class ProbeFactory(DjangoModelFactory):
    class Meta:
        model = Probe

    name = Sequence(lambda n: f'test_probe_{n}')
    url = '/status'


class TimeProfileFactory(DjangoModelFactory):
    class Meta:
        model = TimeProfile

    name = Sequence(lambda n: f"time_profile_{n}")


class DirectorFactory(DjangoModelFactory):
    class Meta:
        model = Director

    name = 'first_service'
    service_mesh_label = 'first_service'
    router = 'req.url'
    route_expression = '/first'
    protocol = 'https'
    mode = 'round-robin'
    hashing_policy = 'req.http.cookie'
    probe = SubFactory(ProbeFactory)
    active_active = True
    time_profile = SubFactory(TimeProfileFactory)
    reachable_via_service_mesh = False


class BackendFactory(DjangoModelFactory):
    class Meta:
        model = Backend

    address = '127.0.1.1'
    port = 80
    dc = SubFactory(DcFactory)
    director = SubFactory(DirectorFactory)
    inherit_time_profile = False
    weight = 1


class VclTagBuilderTest(TestCase):

    def setUp(self):
        settings.SIGNALS = 'off'
        self.dc2 = DcFactory.create(name='Tokyo', symbol="dc2")
        self.dc1 = DcFactory.create(name="Bilbao", symbol="dc1")
        cluster1 = LogicalClusterFactory.create(
            id=1, name='cluster1_siteA_test', labels_list='["example.com", "env:prod"]'
        )
        cluster2 = LogicalClusterFactory.create(id=2, name='cluster2_siteB_test', labels_list='["env:prod"]')
        cluster3_with_mesh_service = LogicalClusterFactory.create(
            id=3, name='cluster3_siteB_test_with_mesh_service', service_mesh_routing=True, labels_list='["cluster3"]'
        )
        cluster4_with_mesh_and_standard_service = LogicalClusterFactory.create(
            id=4,
            name='cluster4_siteB_test_with_mesh_and_standard_service',
            service_mesh_routing=True,
            labels_list='["cluster4"]'
        )
        self.example_domain_mapping = DomainMapping.objects.create(
            domain='example.com', mappings_list='["example.{env}.com", "example.{env}.org"]', type='dynamic'
        )
        self.example_domain_mapping.clusters.add(cluster1)
        self.external_domain_mapping = DomainMapping.objects.create(
            domain='external.com', mappings_list='["example-external.com"]', type='static'
        )
        self.external_domain_mapping.clusters.add(cluster1)
        time_profile = TimeProfile.objects.create(
            name='generic', max_connections=1, connect_timeout=0.5, first_byte_timeout=0.1, between_bytes_timeout=1
        )
        non_active_active_routed_by_path = DirectorFactory.create(
            name='first_service',
            route_expression='/first',
            active_active=False,
            mode='round-robin',
            protocol='https',
            remove_path=False,
            time_profile=time_profile
        )

        active_active_remove_path = DirectorFactory.create(
            name='second_service',
            mode='random',
            route_expression='/second',
            remove_path=True
        )
        active_active_routed_by_domain = DirectorFactory.create(
            name='third_service',
            mode='random',
            router='req.http.host',
            route_expression='third.service.org'
        )
        active_active_with_too_long_name = DirectorFactory.create(
            name='fourth_director_which_has_a_ridiculously_long_name',
            mode='random',
            router='req.http.host',
            route_expression='unusual.name.org'
        )
        active_active_absent_in_second_cluster = DirectorFactory.create(
            name='fifth_director_only_cluster1_siteA_test',
            route_expression='/fifth'
        )
        active_active_hashing_by_cookie = DirectorFactory.create(
            name='sixth_director_hashing_by_cookie',
            route_expression='/sixth',
            mode='hash',
            hashing_policy='req.http.cookie'
        )
        active_active_hashing_by_url = DirectorFactory.create(
            name='seventh_director_hashing_by_url',
            route_expression='/seventh',
            mode='hash',
            hashing_policy='req.url'
        )
        active_active_with_start_as_healthy_probe = DirectorFactory.create(
            name='eighth_service',
            mode='round-robin',
            route_expression='/eighth',
            probe=Probe.objects.create(name='test_probe_start_as_healthy', url='/status', start_as_healthy=True)
        )
        active_active_without_backends = DirectorFactory.create(
            name='ningth_director_without_backends',
            route_expression='/ningth',
            mode='hash',
            hashing_policy='req.url'
        )
        self.active_active_with_mesh_service_support = DirectorFactory.create(
            name='director_with_mesh_service_support',
            service_mesh_label='mesh_service_support',
            route_expression='/mesh_service/support',
            mode='hash',
            hashing_policy='req.url',
            reachable_via_service_mesh=True
        )
        self.active_active_in_forth_hybrid_cluster = DirectorFactory.create(
            name='ten_director_in_forth_hyrid_cluster',
            route_expression='/ten'
        )
        self.active_active_with_mesh_service_support_and_service_tag = DirectorFactory.create(
            name='director_with_mesh_service_support_and_service_tag',
            service_mesh_label='mesh_service_support_with_service_tag',
            route_expression='/mesh_service_service_tag/support',
            mode='hash',
            hashing_policy='req.url',
            service_tag='service-tag-1',
            reachable_via_service_mesh=True
        )
        """ connect directors to clusters """
        non_active_active_routed_by_path.cluster.add(1, 2)
        active_active_remove_path.cluster.add(1, 2)
        active_active_routed_by_domain.cluster.add(1, 2)
        active_active_with_too_long_name.cluster.add(1, 2)
        active_active_absent_in_second_cluster.cluster.add(1)
        active_active_hashing_by_cookie.cluster.add(1, 2)
        active_active_hashing_by_url.cluster.add(1, 2)
        active_active_with_start_as_healthy_probe.cluster.add(1, 2)
        active_active_without_backends.cluster.add(1, 2)
        self.active_active_with_mesh_service_support.cluster.add(3, 4)
        self.active_active_with_mesh_service_support_and_service_tag.cluster.add(3)
        self.active_active_in_forth_hybrid_cluster.cluster.add(4)

        BackendFactory.create(
            address='127.0.1.1', dc=self.dc2, director=non_active_active_routed_by_path, inherit_time_profile=True)
        BackendFactory.create(address='127.0.2.1', dc=self.dc2, director=active_active_remove_path)
        BackendFactory.create(address='127.4.2.1', dc=self.dc1, director=active_active_remove_path)
        BackendFactory.create(address='127.8.2.1', dc=self.dc1, director=active_active_routed_by_domain)
        BackendFactory.create(address='127.9.255.254', port=65535, dc=self.dc1,
                              director=active_active_with_too_long_name)
        BackendFactory.create(address='127.9.2.1', dc=self.dc1, director=active_active_absent_in_second_cluster)
        BackendFactory.create(address='127.10.2.1', dc=self.dc1, director=active_active_hashing_by_cookie)
        BackendFactory.create(address='127.11.2.1', dc=self.dc1, director=active_active_hashing_by_url)
        canary_backend = BackendFactory.create(
            address='127.4.2.2', dc=self.dc1, director=active_active_remove_path, weight=0
        )
        BackendFactory.create(address='127.11.3.1', dc=self.dc1, director=active_active_with_start_as_healthy_probe)
        canary_backend.tags.add('canary')
        BackendFactory.create(address='127.11.4.1', dc=self.dc1, director=self.active_active_in_forth_hybrid_cluster)

        template_v4_with_tag = VclTemplate.objects.create(name='new', content='<VCL/>\n## #{vcl_variable} ##',
                                                          version='4.0')
        template_v4 = VclTemplate.objects.create(name='new-v4', content='<VCL/>', version='4.0')

        VclVariable.objects.create(key='vcl_variable', value='vcl_variable_content', cluster=cluster1)
        VclVariable.objects.create(key='MESH_IP', value='127.0.0.1', cluster=cluster3_with_mesh_service)
        VclVariable.objects.create(key='MESH_PORT', value='30001', cluster=cluster3_with_mesh_service)
        VclVariable.objects.create(key='MESH_IP', value='127.0.0.1', cluster=cluster4_with_mesh_and_standard_service)
        VclVariable.objects.create(key='MESH_PORT', value='30001', cluster=cluster4_with_mesh_and_standard_service)

        route = Route.objects.create(
            condition=r'req.url ~ "^\/flexible"',
            director=non_active_active_routed_by_path,
            priority=1,
            action='pass'
        )
        route.clusters.add(cluster2)

        Redirect.objects.create(
            src_domain=self.example_domain_mapping,
            condition='req.url ~ "/source"',
            destination='http://example.com/destination',
            action=301,
            priority=250,
            preserve_query_params=False,
            required_custom_header=False
        )

        Redirect.objects.create(
            src_domain=self.example_domain_mapping,
            condition='req.url ~ "/source"',
            destination='http://example.com/new_destination',
            action=301,
            priority=210,
            preserve_query_params=False,
            required_custom_header=False
        )

        Redirect.objects.create(
            src_domain=self.external_domain_mapping,
            condition='req.url ~ "/external"',
            destination='http://external.com/external_destination',
            action=301,
            priority=260,
            preserve_query_params=False,
            required_custom_header=False
        )

        self.varnish = VarnishServer.objects.create(ip='127.0.0.1', dc=self.dc2, template=template_v4_with_tag,
                                                    cluster=cluster1)
        self.varnish_dc1 = VarnishServer.objects.create(ip='127.4.0.1', dc=self.dc1, template=template_v4_with_tag,
                                                        cluster=cluster1)
        self.varnish4 = VarnishServer.objects.create(ip='127.0.0.2', dc=self.dc2, template=template_v4,
                                                     cluster=cluster2)
        self.varnish4_canary = VarnishServer.objects.create(
            ip='127.0.0.3', dc=self.dc2, template=template_v4_with_tag, cluster=cluster1, is_canary=True
        )
        self.varnish4_canary = VarnishServer.objects.create(
            ip='127.0.0.4', dc=self.dc2, template=template_v4, cluster=cluster2, is_canary=True
        )
        self.varnish5_with_mesh_service = VarnishServer.objects.create(
            ip='127.0.0.5', dc=self.dc2, template=template_v4, cluster=cluster3_with_mesh_service, is_canary=True
        )
        self.varnish6_with_mesh_and_standard_service = VarnishServer.objects.create(
            ip='127.0.0.6',
            dc=self.dc2,
            template=template_v4,
            cluster=cluster4_with_mesh_and_standard_service,
            is_canary=True
        )

    @staticmethod
    def assert_vcl_tag(vcl_tag, expected_director, expected_dc):
        assert vcl_tag.tag == 'BACKEND_DEFINITION_LIST_%s_%s' % (expected_director, expected_dc)
        assert vcl_tag.parameters['vcl_director'].director.name == expected_director
        assert vcl_tag.parameters['vcl_director'].dc.symbol == expected_dc

    @staticmethod
    def assert_vcl_tag_list_contains_directors_list(tag_list, expected_directors):
        tag_list_directors = []
        for tag in tag_list:
            tag_list_directors.append(tag.director.name)

        for director in expected_directors:
            assert director in tag_list_directors

    def test_should_build_tag_names_based_on_directors_and_dc(self):
        vcl_tag_builder = VclTagBuilder(self.varnish, VclRendererInput())
        tags = vcl_tag_builder.get_expanded_tags('BACKEND_DEFINITION_LIST_{DIRECTOR}_{DC}')
        self.assert_vcl_tag(tags[0], 'third_service', 'dc1')
        self.assert_vcl_tag(tags[1], 'fourth_director_which_has_a_ridiculously_long_name', 'dc1')
        self.assert_vcl_tag(tags[2], 'first_service', 'dc2')
        self.assert_vcl_tag(tags[3], 'second_service', 'dc2')
        self.assert_vcl_tag(tags[4], 'second_service', 'dc1')
        self.assert_vcl_tag(tags[5], 'fifth_director_only_cluster1_siteA_test', 'dc1')

    def test_should_decorate_directors_tag_with_enabled_directors_in_current_dc(self):
        vcl_tag_builder_for_dc2 = VclTagBuilder(self.varnish, VclRendererInput())
        vcl_tag_builder_for_dc1 = VclTagBuilder(self.varnish_dc1, VclRendererInput())

        expected_dc2_directors = [
            'first_service',
            'second_service',
            'third_service',
            'fifth_director_only_cluster1_siteA_test',
            'fourth_director_which_has_a_ridiculously_long_name'
        ]
        expected_dc1_directors = [
            'second_service',
            'third_service',
            'fifth_director_only_cluster1_siteA_test',
            'fourth_director_which_has_a_ridiculously_long_name'
        ]

        self.assert_vcl_tag_list_contains_directors_list(
            vcl_tag_builder_for_dc2.get_expanded_tags('DIRECTORS')[0].parameters['vcl_directors'],
            expected_dc2_directors)

        self.assert_vcl_tag_list_contains_directors_list(
            vcl_tag_builder_for_dc1.get_expanded_tags('DIRECTORS')[0].parameters['vcl_directors'],
            expected_dc1_directors)

    def test_should_decorate_directors_tag_with_enabled_directors_in_current_cluster(self):
        vcl_tag_builder_for_dc2 = VclTagBuilder(self.varnish4, VclRendererInput())

        expected_dc2_second_cluster_directors = [
            'first_service',
            'second_service',
            'third_service',
            'fourth_director_which_has_a_ridiculously_long_name'
        ]

        self.assert_vcl_tag_list_contains_directors_list(
            vcl_tag_builder_for_dc2.get_expanded_tags('DIRECTORS')[0].parameters['vcl_directors'],
            expected_dc2_second_cluster_directors)

    def test_should_decorate_directors_tag_with_example_active_active_director(self):
        active_active_director = 'second_service'
        expected_datacenters = ['dc2', 'dc1']

        vcl_tag_builder = VclTagBuilder(self.varnish, VclRendererInput())

        active_director_datacenters = []
        for vcl_director in vcl_tag_builder.get_expanded_tags('DIRECTORS')[0].parameters['vcl_directors']:
            if vcl_director.director.name == active_active_director:
                active_director_datacenters.append(vcl_director.dc.symbol)

        assert expected_datacenters == active_director_datacenters

    def test_should_decorate_set_backend_tag_with_ordered_director_list_in_first_dc(self):
        active_active_director = 'second_service'
        expected_datacenters = ['dc2', 'dc1']

        vcl_tag_builder = VclTagBuilder(self.varnish, VclRendererInput())
        active_director_datacenters = []
        for tag in vcl_tag_builder.get_expanded_tags('SET_BACKEND_{DIRECTOR}'):
            if tag.parameters['director'].name == active_active_director:
                for vcl_director in tag.parameters['vcl_directors']:
                    active_director_datacenters.append(vcl_director.dc.symbol)
                break

        assert expected_datacenters == active_director_datacenters

    def test_should_decorate_set_backend_tag_with_ordered_director_list_in_second_dc(self):
        active_active_director = 'second_service'
        expected_datacenters = ['dc1', 'dc2']

        vcl_tag_builder = VclTagBuilder(self.varnish_dc1, VclRendererInput())
        active_director_datacenters = []
        for tag in vcl_tag_builder.get_expanded_tags('SET_BACKEND_{DIRECTOR}'):
            if tag.parameters['director'].name == active_active_director:
                for vcl_director in tag.parameters['vcl_directors']:
                    active_director_datacenters.append(vcl_director.dc.symbol)
                break

        assert expected_datacenters == active_director_datacenters

    def test_should_decorate_set_backend_tag_with_fallback_service_in_dc1(self):

        fallback_director = 'fifth_director_only_cluster1_siteA_test'
        expected_datacenters = ['dc1']

        vcl_tag_builder = VclTagBuilder(self.varnish, VclRendererInput())
        active_director_datacenters = []
        for tag in vcl_tag_builder.get_expanded_tags('SET_BACKEND_{DIRECTOR}'):
            if tag.parameters['director'].name == fallback_director:
                for vcl_director in tag.parameters['vcl_directors']:
                    active_director_datacenters.append(vcl_director.dc.symbol)
                break

        assert expected_datacenters == active_director_datacenters

    def test_should_decorate_flexible_router_tag_with_properly_mapped_destination_domain(self):
        vcl_tag_builder = VclTagBuilder(self.varnish, VclRendererInput())
        tag = vcl_tag_builder.get_expanded_tags('FLEXIBLE_ROUTER').pop()
        assert {'example.prod.com', 'example-external.com', 'example.prod.org'} == \
               set(tag.parameters['redirects'].keys())
        assert 'example.com' == tag.parameters['redirects']['example.prod.com'][1].src_domain.domain
        assert 'example.com' == tag.parameters['redirects']['example.prod.org'][1].src_domain.domain
        assert 'http://example.prod.com/destination' == \
               tag.parameters['redirects']['example.prod.com'][1].destination
        assert 'http://example.prod.org/destination' == \
               tag.parameters['redirects']['example.prod.org'][1].destination
        assert 'http://example-external.com/external_destination' == \
               tag.parameters['redirects']['example-external.com'][0].destination

    def test_should_sort_redirects_by_priority(self):
        vcl_tag_builder = VclTagBuilder(self.varnish, VclRendererInput())
        tag = vcl_tag_builder.get_expanded_tags('FLEXIBLE_ROUTER').pop()
        assert {'example.prod.com', 'example-external.com', 'example.prod.org'} == \
               set(tag.parameters['redirects'].keys())
        assert '2/example.prod.com' == tag.parameters['redirects']['example.prod.com'][0].id
        assert '1/example.prod.com' == tag.parameters['redirects']['example.prod.com'][1].id
        assert '2/example.prod.org' == tag.parameters['redirects']['example.prod.org'][0].id
        assert '3/example-external.com' == tag.parameters['redirects']['example-external.com'][0].id


class VclRendererInputTest(TestCase):
    def setUp(self):
        settings.SIGNALS = 'off'
        dc2 = DcFactory.create(name='Tokyo', symbol='dc2')
        dc1 = DcFactory.create(name='Bilbao', symbol='dc1')
        self.first_director = DirectorFactory.create(
            name='first_service', route_expression='/first'
        )
        self.second_director = DirectorFactory.create(
            name='second_service', router='req.http.host', route_expression='second.service.*'
        )
        self.backend_dc2_first = BackendFactory.create(
            address='127.0.1.1', dc=dc2, director=self.first_director
        )
        self.backend_dc1_first = BackendFactory.create(
            address='127.8.2.1', dc=dc1, director=self.first_director
        )
        self.backend_dc2_second = BackendFactory.create(
            address='127.0.2.1', dc=dc2, director=self.second_director
        )
        BackendFactory.create(address='127.0.2.2', dc=dc2, director=self.second_director, enabled=False)

    def test_should_distribute_backends(self):
        expected_distributed_backends = {
            1: {
                1: [self.backend_dc2_first], 2: [self.backend_dc2_second]
            },
            2: {
                1: [self.backend_dc1_first], 2: []
            }
        }
        vcl_renderer_input = VclRendererInput()
        assert expected_distributed_backends == vcl_renderer_input.distributed_backends

    def test_should_sort_directors_by_router_priority(self):
        expected_directors_order = [self.second_director, self.first_director]

        vcl_renderer_input = VclRendererInput()
        assert expected_directors_order == vcl_renderer_input.directors


class VclRendererTest(TestCase):
    setUp = VclTagBuilderTest.__dict__['setUp']

    def _assert_vcl_content(self, expected_file, actual_content):
        with open(os.path.join(os.path.dirname(__file__), expected_file), 'r') as f:
            expected_content = f.read()
        self.maxDiff = None
        assert expected_content == actual_content

    def test_should_prepare_default_vcl_version4(self):
        vcl_renderer = VclRenderer()
        vcl = vcl_renderer.render(self.varnish4, '1', VclRendererInput())

        assert 'new-v4-1' == vcl.name[:-10]
        self._assert_vcl_content('expected-vcl-4.0.vcl', vcl.content)

    def test_should_prepare_vcl_based_on_passed_content(self):
        vcl_renderer = VclRenderer()
        expected_content = 'sample-content'
        vcl = vcl_renderer.render(self.varnish4, '1', VclRendererInput(), expected_content)

        assert 'new-v4-1' == vcl.name[:-10]
        assert expected_content == vcl.content

    def test_should_prepare_default_vcl_version4_with_canary_backend(self):
        vcl_renderer = VclRenderer()
        vcl = vcl_renderer.render(self.varnish4_canary, '1', VclRendererInput())

        assert 'new-v4-1' == vcl.name[:-10]
        self._assert_vcl_content('expected-vcl-4.0-canary.vcl', vcl.content)

    def test_should_comment_unused_tags(self):
        vcl_renderer = VclRenderer()
        vcl_template_with_unused_director = VclTemplate.objects.create(
            name='template-with-unused-director',
            content='<DIRECTOR_first_service/>\n<DIRECTOR_disabled_service/>\n<CALL_USE_DIRECTOR_unknown_director/>',
            version='4.0'
        )
        expected_content = '''\
## START director first_service ###
probe first_service_test_probe_1 {
    .url = "/status";
    .expected_response = 200;
    .interval = 3s;
    .timeout = 1.0s;
    .window = 5;
    .threshold = 3;
}

backend first_service_1_dc2_1_1_80 {
    .host = "127.0.1.1";
    .port = "80";
    .max_connections = 1;
    .connect_timeout = 0.50s;
    .first_byte_timeout = 0.10s;
    .between_bytes_timeout = 1.00s;
    .probe = first_service_test_probe_1;
}

## END director first_service ###
#<DIRECTOR_disabled_service/>
#<CALL_USE_DIRECTOR_unknown_director/>\
'''

        self.varnish.template = vcl_template_with_unused_director
        vcl = vcl_renderer.render(self.varnish, '1', VclRendererInput())
        print("Actual content:\n", vcl.content)
        print("Expected content:\n", expected_content)


        assert expected_content == vcl.content

    def test_should_replace_empty_or_disabled_director_with_information_in_error_response_varnish4(self):
        vcl_renderer = VclRenderer()
        vcl_template_with_unused_director = VclTemplate.objects.create(
            name='template-with-unused-director',
            content='<SET_BACKEND_ningth_director_without_backends/>',
            version='4.0'
        )
        expected_content = '''\
        call use_director_ningth_director_without_backends;\
'''

        self.varnish.template = vcl_template_with_unused_director
        vcl = vcl_renderer.render(self.varnish, '1', VclRendererInput())

        assert expected_content == vcl.content

    def test_should_prepare_default_vcl_version5_with_mesh_service(self):
        vcl_renderer = VclRenderer()
        vcl = vcl_renderer.render(self.varnish5_with_mesh_service, '1', VclRendererInput())

        assert 'new-v4-1' == vcl.name[:-10]
        self._assert_vcl_content('expected-vcl-4.0-with-mesh_service.vcl', vcl.content)

    def test_should_prepare_default_vcl_version5_with_mesh_service_with_attached_backend(self):
        vcl_renderer = VclRenderer()
        BackendFactory.create(address='127.11.2.10', dc=self.dc2, director=self.active_active_with_mesh_service_support)
        vcl = vcl_renderer.render(self.varnish5_with_mesh_service, '1', VclRendererInput())

        assert 'new-v4-1' == vcl.name[:-10]
        self._assert_vcl_content('expected-vcl-4.0-with-mesh_service.vcl', vcl.content)

    def test_should_prepare_default_vcl_varnish_with_mesh_and_standard_service(self):
        vcl_renderer = VclRenderer()
        vcl = vcl_renderer.render(self.varnish6_with_mesh_and_standard_service, '1', VclRendererInput())

        assert 'new-v4-1' == vcl.name[:-10]
        self._assert_vcl_content('expected-vcl-4.0-with-mesh-and-standard-service.vcl', vcl.content)


class VclVariableExpanderTest(TestCase):

    def setUp(self):
        self.cluster = Mock()
        self.cluster.id = 1
        self.cluster_2 = Mock()
        self.cluster_2.id = 2

        self.variable = Mock()
        self.variable.key = 'vcl_variable'
        self.variable.value = 'vcl_variable_value'
        self.variable.cluster_id = 1

        self.variable_2 = Mock()
        self.variable_2.key = 'vcl_variable_2'
        self.variable_2.value = 'vcl_variable_2_value'
        self.variable_2.cluster_id = 2

        self.variables = [self.variable, self.variable_2]

    def test_should_expand_variable_in_appropriate_cluster(self):
        content = VclVariableExpander(self.cluster.id, self.variables, {}).expand_variables(
            '''\
<VCL/>
## #{vcl_variable} ##
## #{vcl_variable_2} ##
'''
        )
        expected_content = '''\
<VCL/>
## vcl_variable_value ##
## #{vcl_variable_2} ##
'''

        assert content == expected_content

    def test_should_expand_variable_with_default_value_only_as_fallback(self):
        default_values = {'vcl_not_defined_variable': 'vcl_fallback_value'}
        content = VclVariableExpander(
            self.cluster.id, self.variables, default_values
        ).expand_variables(
            '''\
<VCL/>
## #{vcl_not_defined_variable} ##
## #{vcl_variable} ##
## #{vcl_variable_2} ##
'''
        )
        expected_content = '''\
<VCL/>
## vcl_fallback_value ##
## vcl_variable_value ##
## #{vcl_variable_2} ##
'''

        assert content == expected_content
