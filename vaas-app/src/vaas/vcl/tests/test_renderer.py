# -*- coding: utf-8 -*-

import os
from factory import DjangoModelFactory, LazyAttribute, Sequence, SubFactory
from mock import *
from nose.tools import *
from random import random
from django.test import TestCase
from vaas.vcl.renderer import Vcl, VclTagExpander, VclTagBuilder, VclRenderer, VclRendererInput
from vaas.manager.models import Director, Probe, Backend, TimeProfile
from vaas.cluster.models import VclTemplate, VclTemplateBlock, Dc, VarnishServer, LogicalCluster
from django.conf import settings

md5_mock = Mock()
md5_mock.hexdigest = Mock(return_value="ca5ef")


class VclTest(TestCase):
    @patch('vaas.vcl.renderer.hashlib.md5', Mock(return_value=md5_mock))
    def test_name_should_contain_version_based_on_digest(self):
        vcl = Vcl('some_content', 'new-vcl')
        assert_equals('new-vcl-vol.ca5ef', vcl.name)

    @patch('vaas.vcl.renderer.hashlib.md5', Mock(return_value=md5_mock))
    def test_should_compare_versions(self):
        vcl = Vcl('some_content', 'new-vcl')
        assert_true(vcl.compareVersion('other-vcl-vol.ca5ef'))


class VclTagExpanderTest(TestCase):
    def setUp(self):
        self.vcl_template3 = VclTemplate.objects.create(name='default-template', version='3.0')
        self.vcl_template4 = VclTemplate.objects.create(name='default-template-v4', version='4.0')
        VclTemplateBlock.objects.create(tag='ACL', content='## ACL custom content ##', template=self.vcl_template3)

    def test_tag_should_be_expanded_from_file_template(self):
        tag_expander = VclTagExpander('VCL', 'VCL', VclRendererInput())
        expected_v3 = '<HEADERS/>\n<ACL/>\n<DIRECTORS/>\n<RECV/>\n<OTHER_FUNCTIONS/>'
        expected_v4 = '''\
# Marker to tell the VCL compiler that this VCL has been adapted to the
# new 4.0 format.
vcl 4.0;

import std;
import directors;

<HEADERS/>
<ACL/>
<DIRECTORS/>
<RECV/>
<OTHER_FUNCTIONS/>'''

        assert_equals(expected_v3, tag_expander.expand(self.vcl_template3))
        assert_equals(expected_v4, tag_expander.expand(self.vcl_template4))

    def test_tag_should_be_expanded_from_database(self):
        tag_expander = VclTagExpander('ACL', 'ACL', VclRendererInput(), can_overwrite=True)
        assert_equals('## ACL custom content ##', tag_expander.expand(self.vcl_template3))


class DcFactory(DjangoModelFactory):

    class Meta:
        model = Dc

    name = Sequence(lambda t: "Town%d" % t)
    symbol = Sequence(lambda t: "dc%d" % t)


class LogicalClusterFactory(DjangoModelFactory):

    class Meta:
        model = LogicalCluster

    name = 'cluster1_siteA_test'


class DirectorFactory(DjangoModelFactory):

    class Meta:
        model = Director

    name = 'first_service'
    router = 'req.url'
    route_expression = '/first'
    mode = 'round-robin'
    hashing_policy = 'req.http.cookie'
    probe = Probe.objects.create(name='test_probe', url='/status')
    active_active = True
    time_profile = TimeProfile.objects.create(name='whatever')


class BackendFactory(DjangoModelFactory):
    class Meta:
        model = Backend

    address = '127.0.1.1'
    port = 80
    dc = SubFactory(DcFactory)
    director = SubFactory(DirectorFactory)
    inherit_time_profile = False


class VclTagBuilderTest(TestCase):

    def setUp(self):
        settings.SIGNALS = 'off'
        dc2 = DcFactory.create(name='Tokyo', symbol="dc2")
        dc1 = DcFactory.create(name="Bilbao", symbol="dc1")
        cluster1 = LogicalClusterFactory.create(id=1, name='cluster1_siteA_test')
        cluster2 = LogicalClusterFactory.create(id=2, name='cluster2_siteB_test')
        time_profile = TimeProfile.objects.create(
            name='generic', max_connections=1, connect_timeout=0.5, first_byte_timeout=0.1, between_bytes_timeout=1
        )
        non_active_active_routed_by_path = DirectorFactory.create(
            name='first_service',
            route_expression='/first',
            active_active=False,
            mode='round-robin',
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
        """ connect directors to clusters """
        non_active_active_routed_by_path.cluster.add(1, 2)
        active_active_remove_path.cluster.add(1, 2)
        active_active_routed_by_domain.cluster.add(1, 2)
        active_active_with_too_long_name.cluster.add(1, 2)
        active_active_absent_in_second_cluster.cluster.add(1)
        active_active_hashing_by_cookie.cluster.add(1, 2)
        active_active_hashing_by_url.cluster.add(1, 2)

        BackendFactory.create(
            address='127.0.1.1', dc=dc2, director=non_active_active_routed_by_path, inherit_time_profile=True)
        BackendFactory.create(address='127.0.2.1', dc=dc2, director=active_active_remove_path)
        BackendFactory.create(address='127.4.2.1', dc=dc1, director=active_active_remove_path)
        BackendFactory.create(address='127.8.2.1', dc=dc1, director=active_active_routed_by_domain)
        BackendFactory.create(address='127.9.255.254', port=65535, dc=dc1, director=active_active_with_too_long_name)
        BackendFactory.create(address='127.9.2.1', dc=dc1, director=active_active_absent_in_second_cluster)
        BackendFactory.create(address='127.10.2.1', dc=dc1, director=active_active_hashing_by_cookie)
        BackendFactory.create(address='127.11.2.1', dc=dc1, director=active_active_hashing_by_url)

        template_v3 = VclTemplate.objects.create(name='new', content='<VCL/>', version='3.0')
        template_v4 = VclTemplate.objects.create(name='new-v4', content='<VCL/>', version='4.0')

        self.varnish = VarnishServer.objects.create(ip='127.0.0.1', dc=dc2, template=template_v3, cluster=cluster1)
        self.varnish_dc1 = VarnishServer.objects.create(ip='127.4.0.1', dc=dc1, template=template_v3, cluster=cluster1)
        self.varnish4 = VarnishServer.objects.create(ip='127.0.0.2', dc=dc2, template=template_v4, cluster=cluster2)

    @staticmethod
    def assert_vcl_tag(vcl_tag, expected_director, expected_dc):
        assert_equals('BACKEND_DEFINITION_LIST_%s_%s' % (expected_director, expected_dc), vcl_tag.tag)
        assert_equals(expected_director, vcl_tag.parameters['vcl_director'].director.name)
        assert_equals(expected_dc, vcl_tag.parameters['vcl_director'].dc.symbol)

    @staticmethod
    def assert_vcl_tag_list_contains_directors_list(tag_list, expected_directors):
        tag_list_directors = []
        for tag in tag_list:
            tag_list_directors.append(tag.director.name)

        for director in expected_directors:
            assert_in(director, tag_list_directors)

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

        assert_list_equal(expected_datacenters, active_director_datacenters)

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

        assert_list_equal(expected_datacenters, active_director_datacenters)

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

        assert_list_equal(expected_datacenters, active_director_datacenters)

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

        assert_list_equal(expected_datacenters, active_director_datacenters)


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
        assert_equals(expected_distributed_backends, vcl_renderer_input.distributed_backends)

    def test_should_sort_directors_by_router_priority(self):
        expected_directors_order = [self.second_director, self.first_director]

        vcl_renderer_input = VclRendererInput()
        assert_equals(expected_directors_order, vcl_renderer_input.directors)


class VclRendererTest(TestCase):
    setUp = VclTagBuilderTest.__dict__['setUp']

    def test_should_prepare_default_vcl_version3(self):
        vcl_renderer = VclRenderer()
        vcl = vcl_renderer.render(self.varnish, '1', VclRendererInput())
        with open(os.path.join(os.path.dirname(__file__)) + os.sep + 'expected-vcl-3.0.vcl', 'r') as f:
            expected_content = f.read()

        assert_equals('new-1', vcl.name[:-10])
        assert_equals(expected_content, vcl.content)

    def test_should_prepare_default_vcl_version4(self):
        vcl_renderer = VclRenderer()
        vcl = vcl_renderer.render(self.varnish4, '1', VclRendererInput())
        with open(os.path.join(os.path.dirname(__file__)) + os.sep + 'expected-vcl-4.0.vcl', 'r') as f:
            expected_content = f.read()

        assert_equals('new-v4-1', vcl.name[:-10])
        assert_equals(expected_content, vcl.content)

    def test_should_comment_unused_tags(self):
        vcl_renderer = VclRenderer()
        vcl_template_with_unused_director = VclTemplate.objects.create(
            name='template-with-unused-director',
            content='<DIRECTOR_first_service/>\n<DIRECTOR_disabled_service/>',
            version='3.0'
        )
        expected_content = '''\
## START director first_service ###
probe first_service_test_probe_1 {
    .url = "/status";
    .expected_response = 200;
    .interval = 3s;
    .timeout = 1s;
    .window = 5;
    .threshold = 3;
}

backend first_service_1_dc2_1_1_80 {
    .host = "127.0.1.1";
    .port = "80";
    .max_connections = 1;
    .connect_timeout = 0.5s;
    .first_byte_timeout = 0.1s;
    .between_bytes_timeout = 1s;
    .probe = first_service_test_probe_1;
}

director first_service_dc2 round-robin {
    {
      .backend = first_service_1_dc2_1_1_80;
    }

}
## END director first_service ###
#<DIRECTOR_disabled_service/>\
'''

        self.varnish.template = vcl_template_with_unused_director
        vcl = vcl_renderer.render(self.varnish, '1', VclRendererInput())

        assert_equals(expected_content, vcl.content)
