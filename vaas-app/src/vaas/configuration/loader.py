# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import os
import yaml


class YamlConfigLoader(object):

    def __init__(self):
        self.config_directories = []
        if os.path.exists(os.path.expanduser('~/.vaas/')):
            self.config_directories.append(os.path.expanduser('~/.vaas/'))
        self.config_directories.append(os.path.abspath(os.path.dirname(__file__) + '/../resources/'))

    def determine_config_file(self, config_file):
        for config_dir in self.config_directories:
            config_absolute_path = "{}/{}".format(config_dir, config_file)
            if os.path.exists(config_absolute_path):
                return config_absolute_path

        return None

    def get_config_tree(self, config_file):
        config_full_path = self.determine_config_file(config_file)
        if config_full_path:
            with open(config_full_path) as file_stream:
                return yaml.load(file_stream.read())

        return {}
