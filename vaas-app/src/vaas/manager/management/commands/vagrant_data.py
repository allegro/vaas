import datetime
from django.core.management.base import BaseCommand, CommandError
from vaas.cluster.cluster import VarnishCluster
from vaas.cluster.models import Dc, VclTemplate, VarnishServer, LogicalCluster
from vaas.manager.models import Backend, Probe, Director
from tastypie.models import ApiKey
from django.core.management import call_command
from django.contrib.auth.models import User
from django.db import DEFAULT_DB_ALIAS as database


class Command(BaseCommand):
    def handle(self, *args, **options):
        call_command('syncdb', interactive=False)
        call_command('flush', interactive=False)
        user = User.objects.db_manager(database).create_superuser('admin', 'admin@vaas.pl', 'admin')
        ApiKey.objects.create(user=user, key="vagrant_api_key")

        dc1 = Dc.objects.create(symbol='dc1', name='First datacenter')
        template3 = VclTemplate.objects.create(name='vagrant_template_3', content='<VCL/>', version='3.0')
        template4 = VclTemplate.objects.create(name='vagrant_template_4', content='<VCL/>', version='4.0')
        probe = Probe.objects.create(name='default_probe', url='/ts.1')
        first_director = Director.objects.create(
            name='first_service', route_expression='/first', mode='random', probe=probe
        )
        second_director = Director.objects.create(
            name='second_service', router='req.http.host', route_expression='second.*', mode='round-robin', probe=probe
        )
        Backend.objects.create(dc=dc1, director=first_director, address='192.168.200.10', port=8080, weight=1)
        Backend.objects.create(dc=dc1, director=first_director, address='192.168.200.11', port=8081, weight=1)
        Backend.objects.create(dc=dc1, director=first_director, address='192.168.200.12', port=8082, weight=2)
        Backend.objects.create(dc=dc1, director=second_director, address='192.168.200.13', port=8083, weight=3)
        Backend.objects.create(dc=dc1, director=second_director, address='192.168.200.14', port=8084, weight=4)
        Backend.objects.create(dc=dc1, director=second_director, address='192.168.200.15', port=8085, weight=5)

        cluster1_siteA_test = LogicalCluster.objects.create(name='cluster1_siteA_test')
        cluster2_siteB_test = LogicalCluster.objects.create(name='cluster2_siteB_test')
        # Created in database, but not assigned:
        LogicalCluster.objects.create(name='cluster3_siteA_dev')
        LogicalCluster.objects.create(name='cluster4_siteC_prod')
        # Link directors with newly created clusters.
        # Numbers in brackets represent cluster ids in the database.
        first_director.cluster.add(1)
        second_director.cluster.add(2)

        VarnishServer.objects.create(
            ip='192.168.200.10',
            port=6082,
            hostname='varnish-3',
            dc=dc1,
            template=template3,
            cluster_weight=1,
            secret='edcf6c52-6f93-4d0d-82b9-cd74239146b0',
            enabled=True,
            cluster=cluster1_siteA_test
        )
        VarnishServer.objects.create(
            ip='192.168.200.11',
            port=6082,
            hostname='varnish-4',
            dc=dc1,
            template=template4,
            cluster_weight=1,
            secret='edcf6c52-6f93-4d0d-82b9-cd74239146b0',
            enabled=True,
            cluster=cluster2_siteB_test
        )

        VarnishCluster().load_vcl(datetime.datetime.now().isoformat(), [cluster1_siteA_test, cluster2_siteB_test])
