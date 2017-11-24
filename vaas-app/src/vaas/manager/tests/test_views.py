from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from tastypie.models import ApiKey
from tastypie.test import ResourceTestCaseMixin
from vaas.cluster.models import LogicalCluster, VarnishServer, VclTemplateBlock, VclTemplate, Dc

User = get_user_model()


class BaseApiViewPermissionsTest(ResourceTestCaseMixin, TestCase):
    API_KEY_ADMIN = 'admin_123456'
    API_KEY_USER = 'user_123456'

    def create_user(self, username, email, password, is_staff, is_superuser):
        return User.objects.create(username=username, email=email, password=password, is_staff=is_staff,
                                   is_superuser=is_superuser)

    def create_api_key_for_user(self, user, api_key):
        tastypie_api_key = ApiKey.objects.create(user=user)
        tastypie_api_key.key = api_key
        tastypie_api_key.save()

    def setUp(self):
        super(BaseApiViewPermissionsTest, self).setUp()

        settings.SIGNALS = 'off'

        self.user_admin = self.create_user(username='admin_user',
                                           email='admin@mail.com',
                                           password='admin',
                                           is_staff=True,
                                           is_superuser=True
                                           )
        self.create_api_key_for_user(self.user_admin, self.API_KEY_ADMIN)

        self.normal_user = self.create_user(username='normal_user',
                                            email='user@mail.com',
                                            password='user',
                                            is_staff=True,
                                            is_superuser=False
                                            )
        self.create_api_key_for_user(self.normal_user, self.API_KEY_USER)


class TestApiViewPermissions(BaseApiViewPermissionsTest):
    LOGICAL_CLUSTER_RESOURCE = '/api/v0.1/logical_cluster/'

    def create_group(self, name):
        return Group.objects.create(name=name)

    def add_permission_for_group(self, group, permissions):
        group.permissions.set(permissions)

    def setUp(self):
        super(TestApiViewPermissions, self).setUp()

        self.cluster_admin_group = self.create_group('cluster_admin')
        self.cluster_admin_permissions = Permission.objects.all().filter(content_type__app_label__in=['cluster'])
        self.add_permission_for_group(self.cluster_admin_group, self.cluster_admin_permissions)

        self.manager_admin_group = self.create_group('manager_admin')
        self.manager_admin_permissions = Permission.objects.all().filter(content_type__app_label__in=['manager'])
        self.add_permission_for_group(self.manager_admin_group, self.manager_admin_permissions)

        self.normal_user.groups.add(self.manager_admin_group)

        self.cluster1 = LogicalCluster.objects.create(name="first cluster")

    def test_get_directors_unauthenticated(self):
        self.assertHttpUnauthorized(self.api_client.get(self.LOGICAL_CLUSTER_RESOURCE, format='json'))

    def test_user_with_superuser_get_logical_cluster_list(self):
        resp = self.api_client.get(self.LOGICAL_CLUSTER_RESOURCE, format='json',
                                   authentication=self.create_apikey(self.user_admin, self.API_KEY_ADMIN))
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)
        self.assertEqual(self.deserialize(resp)['objects'][0]['name'], self.cluster1.name)

    def test_user_without_proper_privileges_cant_post_logical_cluster_list(self):
        resp = self.api_client.post(self.LOGICAL_CLUSTER_RESOURCE, format='json', data={"name": "cluster1"},
                                    authentication=self.create_apikey(self.normal_user, self.API_KEY_USER))
        self.assertHttpUnauthorized(resp)

    def test_user_with_proper_privileges_get_logical_cluster_list(self):
        self.normal_user.groups.add(self.cluster_admin_group)
        resp = self.api_client.get(self.LOGICAL_CLUSTER_RESOURCE, format='json',
                                   authentication=self.create_apikey(self.normal_user, self.API_KEY_USER))
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)
        self.assertEqual(self.deserialize(resp)['objects'][0]['name'], self.cluster1.name)
