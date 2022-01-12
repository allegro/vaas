# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from unittest.mock import patch, mock_open
from nose.tools import assert_equals
from django.test import TestCase

from vaas.configuration.loader import YamlConfigLoader

USER_HOME_PATH = '/user/path/.vaas'
VAAS_APP_RESOURCES_PATH = '/vaas/app/resources'


class YamlConfigLoaderTest(TestCase):

    def file_exists_side_effect(self, arg):
        return arg in self.file_existence and self.file_existence[arg]

    def setUp(self):
        self.file_existence = {}

        exists_patcher = patch('os.path.exists')
        file_exists_mock = exists_patcher.start()
        file_exists_mock.side_effect = self.file_exists_side_effect

        expand_patcher = patch('os.path.expanduser')
        expanduser_mock = expand_patcher.start()
        expanduser_mock.return_value = USER_HOME_PATH

        abspath_patcher = patch('os.path.abspath')
        abspath_mock = abspath_patcher.start()
        abspath_mock.return_value = VAAS_APP_RESOURCES_PATH

        self.addCleanup(exists_patcher.stop)
        self.addCleanup(expand_patcher.stop)
        self.addCleanup(abspath_patcher.stop)

    def test_should_init_search_paths_with_user_and_resources_paths_if_user_path_exists(self):
        self.file_existence = {
            USER_HOME_PATH: True
        }
        directories = YamlConfigLoader().config_directories
        assert_equals(2, len(directories))
        assert_equals([USER_HOME_PATH, VAAS_APP_RESOURCES_PATH], directories)

    def test_should_determine_file_from_users_location_if_exists(self):
        expected_path = "{}/{}".format(USER_HOME_PATH, 'test.yaml')
        self.file_existence = {
            USER_HOME_PATH: True,
            expected_path: True
        }
        assert_equals(expected_path, YamlConfigLoader().determine_config_file('test.yaml'))

    def test_should_determine_file_from_resource_location_if_exists(self):
        expected_path = "{}/{}".format(VAAS_APP_RESOURCES_PATH, 'test.yaml')
        self.file_existence = {
            USER_HOME_PATH: False,
            expected_path: True
        }
        assert_equals(expected_path, YamlConfigLoader().determine_config_file('test.yaml'))

    def test_should_not_determine_file_if_not_exists_in_any_location(self):
        resource_path = "{}/{}".format(VAAS_APP_RESOURCES_PATH, 'test.yaml')
        self.file_existence = {
            USER_HOME_PATH: False,
            resource_path: False
        }
        assert_equals(None, YamlConfigLoader().determine_config_file('test.yaml'))

    @patch('builtins.open', mock_open(read_data="key1: value1\nkey2: value2"))
    def test_should_return_config_tree(self):
        expected_tree = {'key1': 'value1', 'key2': 'value2'}
        self.file_existence = {
            USER_HOME_PATH: False,
            "{}/{}".format(VAAS_APP_RESOURCES_PATH, 'test.yaml'): True
        }

        assert_equals(expected_tree, YamlConfigLoader().get_config_tree('test.yaml'))
