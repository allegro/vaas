# -*- coding: utf-8 -*-
from unittest.mock import Mock, patch

from django.test import TestCase

from vaas.cluster.api import CommandInputValidation


class CommandInputValidationTest(TestCase):

    def test_should_return_error_if_varnish_ids_does_not_contain_integers(self):
        bundle = Mock(data={'varnish_ids': [1, 'not-int']})
        command_validation = CommandInputValidation()
        errors = command_validation.is_valid(bundle, None)
        self.assertDictEqual({'varnish_ids': 'Unexpected type, identifiers have got to be an integer'}, errors)

    @patch('vaas.cluster.api.VarnishServer.objects.filter', Mock(return_value=Mock(count=Mock(return_value=2))))
    def test_should_return_error_if_varnish_ids_contains_id_that_does_not_exist_in_db(self):
        bundle = Mock(data={'varnish_ids': [1, 2, 3]})
        command_validation = CommandInputValidation()
        errors = command_validation.is_valid(bundle, None)
        self.assertDictEqual({'varnish_ids': 'Some of provided varnish identifiers does not exists'}, errors)

    @patch('vaas.cluster.api.VarnishServer.objects.filter', Mock(return_value=Mock(count=Mock(return_value=2))))
    @patch('vaas.cluster.api.AsyncResult', Mock(return_value=Mock(args=[[2, 3]])))
    def test_should_return_error_if_already_ordered_task_had_different_parameters(self):
        bundle = Mock(data={'varnish_ids': [1, 2], 'pk': 'task-uuid'})
        command_validation = CommandInputValidation()
        errors = command_validation.is_valid(bundle, None)
        self.assertDictEqual(
            {'__all__': 'Command: task-uuid has been already ordered with another varnish_ids set'}, errors)

    @patch('vaas.cluster.api.VarnishServer.objects.filter', Mock(return_value=Mock(count=Mock(return_value=2))))
    @patch('vaas.cluster.api.AsyncResult', Mock(return_value=Mock(args=[[2, 3]])))
    def test_should_return_no_error_if_already_ordered_task_had_the_same_uniq_set_of_parameters(self):
        bundle = Mock(data={'varnish_ids': ['3', 2, 2], 'pk': 'task-uuid'})
        command_validation = CommandInputValidation()
        errors = command_validation.is_valid(bundle, None)
        self.assertDictEqual({}, errors)
