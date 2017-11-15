from mock import *
from nose.tools import *
from django.test import TestCase
from django.conf import settings

from vaas.validators import VclVariableValidatorError, vcl_variable_validator
from vaas.cluster.models import VarnishServer, VclVariable, LogicalCluster, VclTemplate


class VclVariableValidatorTest(TestCase):

    def setUp(self):
        settings.SIGNALS = 'off'
        self.cluster1 = LogicalCluster.objects.create(
            pk=1, name='cluster1'
        )
        self.cluster2 = LogicalCluster.objects.create(
            pk=2, name='cluster2'
        )
        self.vcl_template = VclTemplate.objects.create(
            pk=1, content="##{var1}\n##{var2}\n##{var3}"
        )
        self.varnish1 = VarnishServer.objects.create(
            port=6081, ip='1.2.3.4', dc_id=1, template_id=1, cluster_id=1, pk=1
        )
        self.varnish2 = VarnishServer.objects.create(
            port=6081, ip='5.6.7.8', dc_id=1, template_id=1, cluster_id=2, pk=2
        )
        self.varnish3 = VarnishServer.objects.create(
            port=6081, ip='10.11.12.13', dc_id=1, template_id=1, cluster_id=2, pk=3
        )
        self.vcl_variable = VclVariable.objects.create(
            pk=1, key='var3', value='var3_value', cluster_id=1
        )

    def test_should_raise_vcl_validator_error(self):

        assert_raises(VclVariableValidatorError, vcl_variable_validator, self.vcl_template.content, 1, VclVariable, VarnishServer)

    def test_should_not_raise_vcl_validator_error_if_no_placeholders(self):
        pass

    def test_should_not_raise_vcl_validator_error_if_no_clusters(self):
        pass

    def should_not_raise_vcl_validator_error_if_all_variables_found(self):
        pass