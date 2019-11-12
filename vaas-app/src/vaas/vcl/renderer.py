# -*- coding: utf-8 -*-
import copy
import logging
import os
import hashlib
import time
import re

from jinja2 import Environment, FileSystemLoader
from vaas.manager.models import Backend, Director
from vaas.router.models import Route
from vaas.cluster.models import VclTemplateBlock, Dc, VclVariable

VCL_TAGS = {
    '4.0': [
        ['VCL'],
        ['HEADERS', 'ACL', 'DIRECTORS', 'VAAS_STATUS', 'RECV', 'OTHER_FUNCTIONS', 'EMPTY_DIRECTOR_SYNTH'],
        ['ROUTER', 'EXPLICITE_ROUTER', 'FLEXIBLE_ROUTER', 'DIRECTOR_{DIRECTOR}', 'DIRECTOR_INIT_{DIRECTOR}',
            'PROPER_PROTOCOL_REDIRECT'],
        ['SET_BACKEND_{DIRECTOR}', 'BACKEND_DEFINITION_LIST_{DIRECTOR}_{DC}', 'DIRECTOR_DEFINITION_{DIRECTOR}_{DC}',
            'SET_ROUTE_{ROUTE}'],
        ['BACKEND_LIST_{DIRECTOR}_{DC}']
    ]
}

ROUTE_SETTINGS = {
    'req.url': {'priority': 2, 'suffix': '([\/\?].*)?$'},
    'req.http.host': {'priority': 1, 'suffix': ''}
}

env = Environment(
    trim_blocks=True, lstrip_blocks=True, loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates'))
)


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
    def __init__(self, cluster, variables):
        self.cluster = cluster
        self.variables = variables
        self.logger = logging.getLogger('vaas')

    def expand_variables(self, content):

        for variable in self.variables:
            if self.cluster.pk == variable.cluster.pk:
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

    def expand(self, vcl_template):
        db_content = self.get_db_tag_content(vcl_template)
        if not db_content:
            template = env.get_template('vcl_blocks/' + vcl_template.version + '/' + self.template + '.tvcl')
            return template.render(self.parameters)

        return db_content

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
        vcl_directors = self.prepare_vcl_directors(varnish)
        self.placeholders = {
            'dc': self.input.dcs,
            'vcl_director': vcl_directors,
            'probe': self.prepare_probe(vcl_directors),
            'active_director': self.prepare_active_directors(self.input.directors, vcl_directors),
            'routes': self.prepare_route(self.varnish, vcl_directors)
        }

        logging.getLogger('vaas').debug(
            "XXX {}".format(self.placeholders['routes'])
        )

    def prepare_active_directors(self, directors, vcl_directors):
        result = []
        for director in directors:
            if len(list(filter(lambda vcl_director: vcl_director.director.id == director.id, vcl_directors))) > 0:
                result.append(director)
        return result

    def prepare_route(self, varnish, vcl_directors):
        logging.getLogger('vaas').debug("WWW {}".format(vcl_directors))
        routes = []
        for route in self.input.routes:
            if route.director.enabled is True:
                for cluster in route.clusters.all():
                    if varnish.cluster.id == cluster.id:
                        logging.getLogger('vaas').debug("YYY")
                        for vcl_director in vcl_directors:
                            logging.getLogger('vaas').debug("SSS {}: {}".format(vcl_director.director.id, route.director.id))
                            if vcl_director.director.id == route.director.id:
                                routes.append(route)
                                break
        return routes

    def prepare_vcl_directors(self, varnish):
        vcl_directors = []
        for director in self.input.directors:
            if director.enabled is True and varnish.cluster in director.cluster.all():
                director.suffix = ROUTE_SETTINGS[director.router]['suffix']
                for dc in self.input.dcs:
                    backends = self.input.distributed_backends
                    if varnish.is_canary:
                        backends = self.input.distributed_canary_backends
                    if (dc.symbol == varnish.dc.symbol or director.active_active) \
                            and len(backends[dc.id][director.id]) > 0:
                            vcl_directors.append(VclDirector(director, dc, backends[dc.id][director.id], varnish.dc))

        return vcl_directors

    def prepare_probe(self, vcl_directors):
        result = []
        for vcl_director in vcl_directors:
            if vcl_director.director.probe not in result:
                result.append(vcl_director.director.probe)

        return result

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
            for director in self.placeholders['active_director']:
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
                filtered_vcl_directors = filter(
                    lambda vcl_director: vcl_director.director.id == route.director.id,
                    self.placeholders['vcl_director']
                )
                result.append(
                    VclTagExpander(
                        tag_name.replace('{ROUTE}', str(route.id)),
                        self.get_tag_template_name(tag_name),
                        self.input,
                        parameters={
                            'vcl_directors': sorted(
                                filtered_vcl_directors, key=lambda vcl_director: not vcl_director.is_active()
                            ),
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
        elif tag_name in ('ROUTER', 'EXPLICITE_ROUTER', 'DIRECTORS'):
            vcl_tag.parameters['vcl_directors'] = self.placeholders['vcl_director']
            vcl_tag.parameters['directors'] = self.placeholders['active_director']
            vcl_tag.parameters['probes'] = self.placeholders['probe']
        elif tag_name == 'FLEXIBLE_ROUTER':
            vcl_tag.parameters['routes'] = self.placeholders['routes']

        return vcl_tag


class VclRendererInput(object):
    def __init__(self):
        """Prefetch data needed by renderer."""
        self.directors = list(Director.objects.all().prefetch_related('probe', 'cluster', 'time_profile'))
        self.directors.sort(key=lambda director: ROUTE_SETTINGS[director.router]['priority'])
        self.routes = list(Route.objects.all().prefetch_related('director', 'clusters'))
        self.routes.sort(key=lambda route: "{:03d}-{}".format(route.priority, route.director.name))
        self.dcs = list(Dc.objects.all())
        self.template_blocks = list(VclTemplateBlock.objects.all().prefetch_related('template'))
        self.vcl_variables = list(VclVariable.objects.all().prefetch_related('cluster'))
        backends = list(Backend.objects.all().prefetch_related('director', 'dc', 'tags'))
        self.distributed_backends = self.distribute_backends(backends)
        self.distributed_canary_backends = self.prepare_canary_backends(backends)

    def distribute_backends(self, backends):
        """Distribute backend list to two dimensional dictionary."""
        distributed_backends = self.prepare_backend_dictionary()

        for backend in backends:
            if backend.enabled is True:
                distributed_backends[backend.dc.id][backend.director.id].append(backend)

        return distributed_backends

    def prepare_canary_backends(self, backends):
        distributed_canary_backends = self.prepare_backend_dictionary()
        director_backends = {}

        for director in self.directors:
            director_backends[director.id] = []

        for backend in backends:
            director_backends[backend.director.id].append(backend)

        for director_id, backend_list in director_backends.items():
            canary_backends = [
                b for b in backend_list if b.enabled and b.tags.all().filter(name__in=['canary'])
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

    def prepare_backend_dictionary(self):
        backend_dictionary = {}
        for dc in self.dcs:
            backend_dictionary[dc.id] = {}
            for director in self.directors:
                backend_dictionary[dc.id][director.id] = []
        return backend_dictionary


class VclRenderer(object):
    def render(self, varnish, version, input):
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

        content = VclVariableExpander(varnish.cluster, input.vcl_variables).expand_variables(content)

        """
        If can not expand SET_BACKEND_director_name tag, replace this with synth html response which
        contains information about empty director, or director with disabled all backends.
        Replace only if rendered vcl contains empty director synth.
        """
        for vcl_tags_level in VCL_TAGS[varnish.template.version]:
            for tag_name in vcl_tags_level:
                if 'SET_BACKEND_{DIRECTOR}' in tag_name and varnish.template.version == '4.0':
                    content = re.sub(
                        r'<SET_BACKEND_([^\/]+)/>',
                        r'return(synth(404, "<!--Director \1 has no backends or is disabled-->"));',
                        content
                    )

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
