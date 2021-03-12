# -*- coding: utf-8 -*-
import copy
import logging
import os
import hashlib
import time
import functools

from django.conf import settings
from django.db.models import Prefetch
from jinja2 import Environment, FileSystemLoader

from vaas.manager.models import Backend, Director
from vaas.router.models import Route
from vaas.cluster.models import VclTemplateBlock, Dc, VclVariable, LogicalCluster

VCL_TAGS = {
    '4.0': [
        ['VCL'],
        ['HEADERS', 'ACL', 'DIRECTORS', 'VAAS_STATUS', 'RECV', 'OTHER_FUNCTIONS', 'EMPTY_DIRECTOR_SYNTH', 'VCL_PIPE'],
        ['ROUTER', 'EXPLICITE_ROUTER', 'FLEXIBLE_ROUTER', 'DIRECTOR_{DIRECTOR}', 'DIRECTOR_INIT_{DIRECTOR}',
            'PROPER_PROTOCOL_REDIRECT', 'TEST_ROUTER', 'TEST_RESPONSE_SYNTH', 'USE_DIRECTOR_{DIRECTOR}'],
        ['SET_BACKEND_{DIRECTOR}', 'BACKEND_DEFINITION_LIST_{DIRECTOR}_{DC}', 'DIRECTOR_DEFINITION_{DIRECTOR}_{DC}',
            'SET_ROUTE_{ROUTE}'],
        ['BACKEND_LIST_{DIRECTOR}_{DC}', 'CALL_USE_DIRECTOR_{DIRECTOR}']
    ]
}

ROUTE_SETTINGS = {
    'req.url': {'priority': 2, 'suffix': '([\/\?].*)?$'},
    'req.http.host': {'priority': 1, 'suffix': ''}
}

env = Environment(
    trim_blocks=True, lstrip_blocks=True, auto_reload=False,
    loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates'))
)

TEMPLATE_CACHE = {}

processing_stats = {}


def init_processing():
    global processing_stats
    processing_stats = {}
    return processing_stats


def collect_processing(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        global processing_stats
        start = time.time()
        r = func(*args, **kwargs)
        name = func.__name__
        if name not in processing_stats:
            processing_stats[name] = {'time': 0, 'calls': 0}
        processing_stats[name]['calls'] += 1
        processing_stats[name]['time'] += time.time() - start
        return r
    return wrapper


class Vcl(object):
    def __init__(self, content, name='default'):
        self.version = hashlib.md5(str(content).encode('utf-8')).hexdigest()[:5]
        self.name = "{}-vol_{}".format(name, self.version)
        self.content = content.replace('##VCL_VERSION##', self.version)

    def compareVersion(self, otherName):
        return otherName[-5:] == self.name[-5:]

    def __eq__(self, other):
        return hashlib.md5(str(self).encode('utf-8')).hexdigest() == hashlib.md5(str(other).encode('utf-8')).hexdigest()

    def __str__(self):
        return self.content + '\n'

    def __unicode__(self):
        return self.content + '\n'


class VclVariableExpander(object):
    def __init__(self, cluster_id, variables):
        self.cluster_id = cluster_id
        self.variables = variables
        self.logger = logging.getLogger('vaas')

    def expand_variables(self, content):

        for variable in self.variables:
            if self.cluster_id == variable.cluster_id:
                vcl_variable_key = "#{{{}}}".format(variable.key)
                content = content.replace(vcl_variable_key, variable.value)

        return content


class VclTagExpander(object):
    def __init__(self, tag, template, input, parameters=None, can_overwrite=False):
        self.tag = tag
        self.input = input
        self.template = template
        self.can_overwrite = can_overwrite
        self.parameters = parameters
        if parameters is None:
            self.parameters = {}

    @collect_processing
    def expand(self, vcl_template):
        db_content = self.get_db_tag_content(vcl_template)
        if not db_content:
            template = self._get_template(vcl_template)
            return self._render(template)

        return db_content

    @collect_processing
    def _get_template(self, vcl_template):
        path = 'vcl_blocks/' + vcl_template.version + '/' + self.template + '.tvcl'
        if path not in TEMPLATE_CACHE:
            TEMPLATE_CACHE[path] = env.get_template(path)
        return TEMPLATE_CACHE[path]

    @collect_processing
    def _render(self, template):
        return template.render(self.parameters)

    @collect_processing
    def get_db_tag_content(self, vcl_template):
        if self.can_overwrite is True:
            vcl_template_blocks = list(filter(
                lambda block: block.template == vcl_template and block.tag == self.tag, self.input.template_blocks
            ))
            if len(vcl_template_blocks) == 1:
                return vcl_template_blocks[0].content
        return ""

    def __str__(self):
        return '<' + self.tag + '/>'

    def __unicode__(self):
        return '<' + self.tag + '/>'


class VclDirector(object):
    def __init__(self, director, dc, backends, current_dc):
        self.director = director
        self.dc = dc
        self.backends = backends
        self.current_dc = current_dc

    def is_active(self):
        return self.dc.symbol == self.current_dc.symbol


class VclTagBuilder(object):
    def __init__(self, varnish, input_data):
        self.input = input_data
        self.varnish = varnish
        cluster_directors = self.prepare_cluster_directors()
        vcl_directors, active_directors = self.prepare_vcl_directors(varnish, cluster_directors)
        self.placeholders = {
            'dc': self.input.dcs,
            'vcl_director': vcl_directors,
            'probe': self.prepare_probe(vcl_directors),
            'active_director': active_directors,
            'routes': self.prepare_route(self.varnish, cluster_directors),
            'cluster_directors': cluster_directors,
        }

    @collect_processing
    def prepare_route(self, varnish, cluster_directors):
        routes = []
        for route in self.input.routes:
            if route.director.enabled is True:
                for cluster in route.cluster_ids:
                    if varnish.cluster_id == cluster.id:
                        for cluster_director in cluster_directors:
                            if cluster_director.id == route.director.id:
                                routes.append(route)
                                break
        return routes

    @collect_processing
    def prepare_cluster_directors(self):
        result = []
        for director in self.input.directors:
            for cluster in director.cluster_ids:
                if cluster.id == self.varnish.cluster_id and director.enabled is True:
                    result.append(director)

        return result

    @collect_processing
    def prepare_vcl_directors(self, varnish, cluster_directors):
        vcl_directors = []
        active_directors = []
        for director in cluster_directors:
            director.suffix = ROUTE_SETTINGS[director.router]['suffix']
            append = False
            for dc in self.input.dcs:
                backends = self.input.distributed_backends
                if varnish.is_canary:
                    backends = self.input.distributed_canary_backends
                if (dc.symbol == varnish.dc.symbol or director.active_active) \
                        and len(backends[dc.id][director.id]) > 0:
                        vcl_directors.append(VclDirector(director, dc, backends[dc.id][director.id], varnish.dc))
                        append = True
            if append:
                active_directors.append(director)

        return vcl_directors, active_directors

    @collect_processing
    def prepare_probe(self, vcl_directors):
        result = []
        for vcl_director in vcl_directors:
            if vcl_director.director.probe not in result:
                result.append(vcl_director.director.probe)

        return result

    @collect_processing
    def get_expanded_tags(self, tag_name):
        result = []
        applied_rules = False
        if tag_name.endswith('{DIRECTOR}_{DC}'):
            applied_rules = True
            for vcl_director in self.placeholders['vcl_director']:
                result.append(
                    VclTagExpander(
                        tag_name.replace('{DIRECTOR}', str(vcl_director.director))
                        .replace('{DC}', str(vcl_director.dc)),
                        self.get_tag_template_name(tag_name),
                        self.input,
                        parameters={'vcl_director': vcl_director}
                    )
                )

        if tag_name.endswith('{DIRECTOR}'):
            applied_rules = True
            for director in self.placeholders['cluster_directors']:
                filtered_vcl_directors = filter(
                    lambda vcl_director: vcl_director.director.id == director.id, self.placeholders['vcl_director']
                )
                result.append(
                    VclTagExpander(
                        tag_name.replace('{DIRECTOR}', str(director)),
                        self.get_tag_template_name(tag_name),
                        self.input,
                        parameters={
                            'vcl_directors': sorted(
                                filtered_vcl_directors, key=lambda vcl_director: not vcl_director.is_active()
                            ),
                            'director': director
                        }
                    )
                )

        if tag_name.endswith('{ROUTE}'):
            applied_rules = True
            for route in self.placeholders['routes']:
                result.append(
                    VclTagExpander(
                        tag_name.replace('{ROUTE}', str(route.id)),
                        self.get_tag_template_name(tag_name),
                        self.input,
                        parameters={
                            'route': route
                        }
                    )
                )

        if not applied_rules:
            return [self.decorate_single_tag(tag_name)]

        return result

    def get_tag_template_name(self, tag_name):
        return tag_name.replace('_{DIRECTOR}', '').replace('_{DC}', '').replace('_{PROBE}', '').replace('_{ROUTE}', '')

    def decorate_single_tag(self, tag_name):
        vcl_tag = VclTagExpander(tag_name, self.get_tag_template_name(tag_name), self.input, can_overwrite=True)
        if tag_name == 'VAAS_STATUS':
            vcl_tag.parameters['server'] = self.varnish
            vcl_tag.parameters['allow_metrics_header'] = settings.ALLOW_METRICS_HEADER
        elif tag_name in ('ROUTER', 'EXPLICITE_ROUTER', 'DIRECTORS'):
            vcl_tag.parameters['vcl_directors'] = self.placeholders['vcl_director']
            vcl_tag.parameters['directors'] = self.placeholders['active_director']
            vcl_tag.parameters['probes'] = self.placeholders['probe']
            vcl_tag.parameters['cluster_directors'] = self.placeholders['cluster_directors']
        elif tag_name == 'FLEXIBLE_ROUTER':
            vcl_tag.parameters['routes'] = self.placeholders['routes']
        elif tag_name == 'TEST_ROUTER':
            vcl_tag.parameters['validation_header'] = settings.VALIDATION_HEADER

        return vcl_tag


class VclRendererInput(object):
    def __init__(self):
        self.fetch_render_data()

    @collect_processing
    def fetch_render_data(self):
        """Prefetch data needed by renderer."""
        self.directors = list(Director.objects.all().prefetch_related(
            'probe',
            'time_profile',
            Prefetch('cluster', queryset=LogicalCluster.objects.only('pk'), to_attr='cluster_ids')
        ))
        self.directors.sort(key=lambda director: ROUTE_SETTINGS[director.router]['priority'])
        self.routes = list(Route.objects.all().prefetch_related(
            'director',
            Prefetch('clusters', queryset=LogicalCluster.objects.only('pk'), to_attr='cluster_ids')
        ))
        self.routes.sort(key=lambda route: "{:03d}-{}".format(route.priority, route.director.name))
        self.dcs = list(Dc.objects.all())
        self.template_blocks = list(VclTemplateBlock.objects.all().prefetch_related('template'))
        self.vcl_variables = list(VclVariable.objects.all())
        backends = list(Backend.objects.filter(enabled=True).prefetch_related('director', 'dc'))
        canary_backend_ids = list(
            Backend.objects.values_list('id', flat=True).filter(tags__name='canary').prefetch_related('director', 'dc')
        )
        self.distributed_backends = self.distribute_backends(backends)
        self.distributed_canary_backends = self.prepare_canary_backends(canary_backend_ids, backends)

    @collect_processing
    def distribute_backends(self, backends):
        """Distribute backend list to two dimensional dictionary."""
        distributed_backends = self.prepare_backend_dictionary()

        for backend in backends:
            if backend.enabled is True:
                distributed_backends[backend.dc.id][backend.director.id].append(backend)

        return distributed_backends

    @collect_processing
    def prepare_canary_backends(self, canary_backend_ids, backends):
        distributed_canary_backends = self.prepare_backend_dictionary()
        director_backends = {}

        for director in self.directors:
            director_backends[director.id] = []

        for backend in backends:
            director_backends[backend.director.id].append(backend)

        for director_id, backend_list in director_backends.items():
            canary_backends = [
                b for b in backend_list if b.enabled and b.id in canary_backend_ids
            ]
            for canary_backend in canary_backends:
                backend = copy.copy(canary_backend)
                if backend.weight == 0:
                    backend.weight = 1
                distributed_canary_backends[canary_backend.dc.id][canary_backend.director.id].append(backend)
            if len(canary_backends) == 0:
                for backend in backend_list:
                    if backend.enabled is True:
                        distributed_canary_backends[backend.dc.id][backend.director.id].append(backend)
        return distributed_canary_backends

    @collect_processing
    def prepare_backend_dictionary(self):
        backend_dictionary = {}
        for dc in self.dcs:
            backend_dictionary[dc.id] = {}
            for director in self.directors:
                backend_dictionary[dc.id][director.id] = []
        return backend_dictionary


class VclRenderer(object):
    def render(self, varnish, version, input):
        try:
            start = time.time()
            vcl_tag_builder = VclTagBuilder(varnish, input)
            logging.getLogger('vaas').debug(
                "[%s] vcl tag builder prepare time: %f" % (varnish.ip, time.time() - start)
            )

            content = varnish.template.content
            for vcl_tags_level in VCL_TAGS[varnish.template.version]:
                for tag_name in vcl_tags_level:
                    for vcl_tag in vcl_tag_builder.get_expanded_tags(tag_name):
                        content = content.replace(str(vcl_tag), vcl_tag.expand(varnish.template))

            content = VclVariableExpander(varnish.cluster_id, input.vcl_variables).expand_variables(content)

            """
            Comment not expanded parameterized tags
            """
            for vcl_tags_level in VCL_TAGS[varnish.template.version]:
                for tag_name in vcl_tags_level:
                    if '{' in tag_name:
                        tag_prefix = '<' + tag_name[0: tag_name.find("{")]
                        content = content.replace(tag_prefix, '#' + tag_prefix)

            content = content.replace("\r", '')
            vcl = Vcl(content, name=str(varnish.template.name + '-' + version))
            logging.getLogger('vaas').debug(
                "[%s] vcl '%s' rendering time: %f" % (varnish.ip, vcl.name, time.time() - start)
            )
            return vcl
        except:
            logging.getLogger('vaas').exception('Cannot render template')
            raise
