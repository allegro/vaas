# -*- coding: utf-8 -*-

import logging
import os
import hashlib
import time

from jinja2 import Environment, FileSystemLoader
from vaas.manager.models import Backend, Director
from vaas.cluster.models import VclTemplateBlock, Dc


VCL_TAGS = {
    '3.0': [
        ['VCL'],
        ['HEADERS', 'ACL', 'DIRECTORS', 'RECV', 'OTHER_FUNCTIONS'],
        ['ROUTER', 'DIRECTOR_{DIRECTOR}'],
        ['SET_BACKEND_{DIRECTOR}', 'BACKEND_DEFINITION_LIST_{DIRECTOR}_{DC}', 'DIRECTOR_DEFINITION_{DIRECTOR}_{DC}'],
        ['BACKEND_LIST_{DIRECTOR}_{DC}']
    ],
    '4.0': [
        ['VCL'],
        ['HEADERS', 'ACL', 'DIRECTORS', 'RECV', 'OTHER_FUNCTIONS'],
        ['ROUTER', 'DIRECTOR_{DIRECTOR}', 'DIRECTOR_INIT_{DIRECTOR}'],
        ['SET_BACKEND_{DIRECTOR}', 'BACKEND_DEFINITION_LIST_{DIRECTOR}_{DC}', 'DIRECTOR_DEFINITION_{DIRECTOR}_{DC}'],
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
        self.content = content
        self.name = name + '-vol.' + hashlib.md5(str(self)).hexdigest()[:5]

    def compareVersion(self, otherName):
        return otherName[-5:] == self.name[-5:]

    def __eq__(self, other):
        return hashlib.md5(str(self)).hexdigest() == hashlib.md5(str(other)).hexdigest()

    def __str__(self):
        return self.content + '\n'

    def __unicode__(self):
        return self.content + '\n'


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
            vcl_template_blocks = filter(
                lambda block: block.template == vcl_template and block.tag == self.tag, self.input.template_blocks
            )
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
    def __init__(self, varnish, input):
        self.input = input
        self.varnish = varnish
        vcl_directors = self.prepare_vcl_directors(varnish)
        self.placeholders = {
            'dc': self.input.dcs,
            'vcl_director': vcl_directors,
            'probe': self.prepare_probe(vcl_directors),
            'active_director': self.prepare_active_directors(self.input.directors, vcl_directors)
        }

    def prepare_active_directors(self, directors, vcl_directors):
        result = []
        for director in directors:
            if len(filter(lambda vcl_director: vcl_director.director.id == director.id, vcl_directors)) > 0:
                result.append(director)
        return result

    def prepare_vcl_directors(self, varnish):
        vcl_directors = []
        for director in self.input.directors:
            if director.enabled is True and varnish.cluster in director.cluster.all():
                director.suffix = ROUTE_SETTINGS[director.router]['suffix']
                for dc in self.input.dcs:
                    if (dc.symbol == varnish.dc.symbol or director.active_active) \
                            and len(self.input.distributed_backends[dc.id][director.id]) > 0:
                        vcl_directors.append(VclDirector(
                            director, dc, self.input.distributed_backends[dc.id][director.id], varnish.dc)
                        )

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

        if not applied_rules:
            return [self.decorate_single_tag(tag_name)]

        return result

    def get_tag_template_name(self, tag_name):
        return tag_name.replace('_{DIRECTOR}', '').replace('_{DC}', '').replace('_{PROBE}', '')

    def decorate_single_tag(self, tag_name):
        vcl_tag = VclTagExpander(tag_name, self.get_tag_template_name(tag_name), self.input, can_overwrite=True)
        if tag_name in ['ROUTER', 'DIRECTORS']:
            vcl_tag.parameters['vcl_directors'] = self.placeholders['vcl_director']
            vcl_tag.parameters['directors'] = self.placeholders['active_director']
            vcl_tag.parameters['probes'] = self.placeholders['probe']
        return vcl_tag


class VclRendererInput(object):
    def __init__(self):
        """Prefetch data needed by renderer."""
        self.directors = list(Director.objects.all().prefetch_related('probe', 'cluster', 'time_profile'))
        self.directors.sort(key=lambda director: ROUTE_SETTINGS[director.router]['priority'])
        self.dcs = list(Dc.objects.all())
        self.template_blocks = list(VclTemplateBlock.objects.all().prefetch_related('template'))
        self.distributed_backends = self.distribute_backends(
            list(Backend.objects.all().prefetch_related('director', 'dc'))
        )

    def distribute_backends(self, backends):
        """Distribute backend list to two dimensional dictionary."""
        distributed_backends = {}
        for dc in self.dcs:
            distributed_backends[dc.id] = {}
            for director in self.directors:
                distributed_backends[dc.id][director.id] = []

        for backend in backends:
            if backend.enabled is True:
                distributed_backends[backend.dc.id][backend.director.id].append(backend)

        return distributed_backends


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
