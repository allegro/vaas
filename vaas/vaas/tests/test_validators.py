from django.test import TestCase
from django.conf import settings

from vaas.validators import VclVariableValidatorError, vcl_variable_validator
from vaas.cluster.models import VarnishServer, VclVariable, LogicalCluster, VclTemplate, Dc


class VclVariableValidatorTest(TestCase):

    def setUp(self):
        settings.SIGNALS = 'off'
        self.cluster1 = LogicalCluster.objects.create(
            pk=1, name='cluster1'
        )
        self.cluster2 = LogicalCluster.objects.create(
            pk=2, name='cluster2'
        )
        self.vcl_template1 = VclTemplate.objects.create(
            pk=1, content="## #{var1}\n", name='template1'
        )
        self.vcl_template2 = VclTemplate.objects.create(
            pk=2, content="<VCL/>", name='template2'
        )
        self.vcl_template3 = VclTemplate.objects.create(
            pk=3, content="## #{var1} ##\n## #{var2} ##", name='template3'
        )
        self.dc1 = Dc.objects.create(pk=1, name="Bilbao", symbol="dc1")
        self.varnish1 = VarnishServer.objects.create(
            port=6081, ip='1.2.3.4', dc_id=1, template_id=1, cluster_id=1, pk=1
        )
        self.varnish2 = VarnishServer.objects.create(
            port=6081, ip='5.6.7.8', dc_id=1, template_id=2, cluster_id=2, pk=2
        )
        self.varnish3 = VarnishServer.objects.create(
            port=6081, ip='10.11.12.13', dc_id=1, template_id=3, cluster_id=2, pk=3
        )
        self.vcl_variable1 = VclVariable.objects.create(
            pk=1, key='var1', value='var1_value', cluster_id=2
        )
        self.vcl_variable2 = VclVariable.objects.create(
            pk=2, key='var2', value='var2_value', cluster_id=2
        )
        self.vcl_variable3 = VclVariable.objects.create(
            pk=3, key='var3', value='var3_value', cluster_id=1
        )

    def test_should_raise_vcl_validator_error_if_variables_missing(self):
        with self.assertRaises(VclVariableValidatorError):
            vcl_variable_validator(
                self.vcl_template1.content,
                1,
                VclVariable,
                VarnishServer
            )

    def test_should_not_raise_vcl_validator_error_if_no_placeholders(self):
        ret_val = vcl_variable_validator(
            self.vcl_template2.content,
            self.vcl_template2.pk,
            VclVariable,
            VarnishServer
        )
        self.assertIsNone(ret_val)

    def test_should_substitute_all_variables_found(self):
        ret_val = vcl_variable_validator(
            self.vcl_template3.content,
            self.vcl_template3.pk,
            VclVariable,
            VarnishServer
        )
        self.assertIsNone(ret_val)

