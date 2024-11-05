# -*- coding: utf-8 -*-
import json
from unittest.mock import Mock, patch

from nose.tools import assert_equals

from vaas.cluster.mapping import MappingProvider
from vaas.cluster.models import LogicalCluster, DomainMapping


@patch('vaas.cluster.models.DomainMapping.clusters')
def test_should_return_sorted_static_domains_connected_by_db_relation(clusters_mock):
    # given static mapping related with logical cluster
    static_mappings = [
        DomainMapping(id=1, type="static", domain="b-static.example.com"),
        DomainMapping(id=2, type="static", domain="a-static.example.com"),
    ]
    cluster = LogicalCluster(id=100)
    clusters_mock.all = Mock(return_value=[cluster])

    # when looking for related mappings for cluster
    provider = MappingProvider(static_mappings)
    domains = provider.provide_related_domains(cluster)

    # then static domain mappings should be returned
    assert_equals(["a-static.example.com", "b-static.example.com"], domains)


@patch('vaas.cluster.models.LogicalCluster.domainmapping_set', Mock(filter=Mock(return_value=[])))
def test_should_return_dynamic_domains_matched_by_common_labels():
    # given dynamic mapping unrelated with logical cluster
    dynamic_mappings = [
        DomainMapping(
            id=1, type="dynamic", domain="b-dynamic.example.com", mappings_list='["{label-one}.example.com"]'
        ),
        DomainMapping(
            id=2, type="dynamic", domain="a-dynamic.example.com", mappings_list='["{label-two}.example.com"]'
        ),
        DomainMapping(
            id=3, type="dynamic", domain="c-dynamic.example.com", mappings_list='["{no-label}.example.com"]'
        ),
    ]
    # and cluster that has labels used as a placeholders in above mappings
    cluster = LogicalCluster(labels_list=json.dumps(["label-one:b", "label-two:a", "label-whatever:c"]))

    # when looking for related mappings for cluster
    provider = MappingProvider(dynamic_mappings)
    domains = provider.provide_related_domains(cluster)

    # then dynamic domain mappings should be returned
    assert_equals(["a-dynamic.example.com", "b-dynamic.example.com"], domains)


@patch('vaas.cluster.models.LogicalCluster.domainmapping_set', Mock(filter=Mock(return_value=[])))
def test_should_return_single_dynamic_domain_even_if_more_than_one_mapping_is_satisfied():
    # given dynamic mapping unrelated with logical cluster
    dynamic_mappings = [
        DomainMapping(
            id=1,
            type="dynamic",
            domain="multiple-dynamic.example.com",
            mappings_list='["{label-one}.example.com", "{label-two}.example.com"]'
        ),
    ]
    # and cluster that has labels used as a placeholders in above mappings
    cluster = LogicalCluster(labels_list=json.dumps(["label-one:b", "label-two:a", "label-whatever:c"]))

    # when looking for related mappings for cluster
    provider = MappingProvider(dynamic_mappings)
    domains = provider.provide_related_domains(cluster)

    # then single dynamic domain mapping should be returned
    assert_equals(["multiple-dynamic.example.com"], domains)
