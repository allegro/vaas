from mock import patch, Mock
from vaas.cluster.models import LogicalCluster, VarnishServer, VclTemplateBlock, VclTemplate, Dc

from vaas.manager.tests.test_views import BaseApiViewPermissionsTest


class TestPurgerApiViewPermissions(BaseApiViewPermissionsTest):
    PURGER_RESOURCE = '/api/v0.1/purger/'

    API_KEY_NON_STAFF_USER = 'non_staff_user_12345'

    def setUp(self):
        super(TestPurgerApiViewPermissions, self).setUp()

        self.user_non_staff = self.create_user(username='user_non_staff',
                                               email='user_non_staff@mail.com',
                                               password='user',
                                               is_staff=False,
                                               is_superuser=False
                                               )
        self.create_api_key_for_user(self.user_non_staff, self.API_KEY_NON_STAFF_USER)

        cluster1 = LogicalCluster.objects.create(name="first_cluster")

        dc1 = Dc.objects.create(name="Bilbao", symbol="dc1")
        template_v4 = VclTemplate.objects.create(name='new-v4', content='<VCL/>', version='4.0')
        self.varnish = VarnishServer.objects.create(ip='127.0.0.1', hostname='server1', dc=dc1, status='enabled',
                                                    template=template_v4, cluster=cluster1)

        self.purger_data = {"url": "http://example.com/contact", "clusters": "first_cluster"}

    def test_get_directors_unauthenticated(self):
        self.assertHttpUnauthorized(self.api_client.post(self.PURGER_RESOURCE, format='json', data=self.purger_data))

    @patch('vaas.purger.purger.HTTPConnection.getresponse', Mock(return_value=Mock(status=200)))
    @patch('http.client.HTTPConnection.request')
    def test_user_with_staff_status_can_purge_url(self, response_mock):
        resp = self.api_client.post(self.PURGER_RESOURCE, format='json', data=self.purger_data,
                                    authentication=self.create_apikey(self.normal_user, self.API_KEY_USER))
        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)['success'], {
            '{}'.format(self.varnish.ip): 'varnish http response code: 200, url={}'.format(self.purger_data['url'])
        })

    @patch('vaas.purger.purger.HTTPConnection.getresponse', Mock(return_value=Mock(status=200)))
    @patch('http.client.HTTPConnection.request')
    def test_user_without_staff_status_can_not_purge_url(self, response_mock):
        self.assertHttpUnauthorized(self.api_client.post(self.PURGER_RESOURCE, format='json', data=self.purger_data,
                                                         authentication=self.create_apikey(self.user_non_staff,
                                                                                           self.API_KEY_NON_STAFF_USER)))
