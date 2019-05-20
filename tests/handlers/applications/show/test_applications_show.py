import json
import os
from unittest import TestCase
from unittest.mock import patch, MagicMock

import requests
import responses

import settings
from applications_show import ApplicationShow


class TestMeApplicationShow(TestCase):
    def setUp(self):
        os.environ['AUTHLETE_API_KEY'] = 'XXXXXXXXXXXXXXXXX'
        os.environ['AUTHLETE_API_SECRET'] = 'YYYYYYYYYYYYYY'

    def tearDown(self):
        pass

    @responses.activate
    def test_main_ok(self):
        params = {
            'pathParameters': {
                'client_id': '123456789'
            }
        }

        responses.add(responses.GET,
                      settings.AUTHLETE_CLIENT_ENDPOINT + '/get/' + params['pathParameters']['client_id'],
                      json={
                          'clientName': 'client_name',
                          'description': 'description_string',
                          'hoge': 'hoge'
                      }, status=200)

        response = ApplicationShow(params, {}).main()
        expected = {
            'clientName': 'client_name',
            'description': 'description_string'
        }

        self.assertEqual(200, response['statusCode'])
        self.assertEqual(expected, json.loads(response['body']))

    @responses.activate
    def test_main_ok_not_exists_description(self):
        params = {
            'pathParameters': {
                'client_id': '123456789'
            }
        }

        responses.add(responses.GET,
                      settings.AUTHLETE_CLIENT_ENDPOINT + '/get/' + params['pathParameters']['client_id'],
                      json={
                          'clientName': 'client_name',
                          'hoge': 'hoge'
                      }, status=200)

        response = ApplicationShow(params, {}).main()
        expected = {
            'clientName': 'client_name',
            'description': None
        }

        self.assertEqual(200, response['statusCode'])
        self.assertEqual(expected, json.loads(response['body']))

    @patch('requests.get', MagicMock(side_effect=requests.exceptions.RequestException()))
    def test_main_with_exception(self):
        params = {
            'pathParameters': {
                'client_id': '123456789'
            }
        }

        responses.add(responses.GET,
                      settings.AUTHLETE_CLIENT_ENDPOINT + '/get/' + params['pathParameters']['client_id'],
                      json={"developer": "user01"}, status=200)

        response = ApplicationShow(params, {}).main()
        self.assertEqual(response['statusCode'], 500)

    def test_validation_client_id_min(self):
        params = {
            'pathParameters': {
                'client_id': '0'
            }
        }

        response = ApplicationShow(params, {}).main()
        self.assertEqual(response['statusCode'], 400)

    def test_validation_client_id_invalid_type(self):
        params = {
            'pathParameters': {
                'client_id': 'AAA'
            }
        }

        response = ApplicationShow(params, {}).main()
        self.assertEqual(response['statusCode'], 400)
