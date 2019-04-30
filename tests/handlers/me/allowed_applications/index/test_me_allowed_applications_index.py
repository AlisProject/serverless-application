import os
import json
from unittest import TestCase
from unittest.mock import patch, MagicMock

import requests
import responses

import settings
from me_allowed_applications_index import MeAllowedApplicationsIndex


class TestMeAllowedApplicationsIndex(TestCase):
    def setUp(self):
        os.environ['AUTHLETE_API_KEY'] = 'XXXXXXXXXXXXXXXXX'
        os.environ['AUTHLETE_API_SECRET'] = 'YYYYYYYYYYYYYY'

    def tearDown(self):
        pass

    @responses.activate
    def test_main_ok(self):
        params = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'user01'
                    }
                }
            }
        }

        responses.add(responses.GET,
                      settings.AUTHLETE_CLIENT_ENDPOINT + '/authorization/get/list',
                      json={
                          'statusCode': 200,
                          'clients':
                              [{"clientId": 12345678901234, "clientName": "test", "clientType": "CONFIDENTIAL"}]},
                      status=200)
        response = MeAllowedApplicationsIndex(params, {}).main()
        self.assertEqual(response['statusCode'], 200)
        result = json.loads(response['body'])
        self.assertEqual(result[0]['clientId'], 12345678901234)

    @patch('requests.get', MagicMock(side_effect=requests.exceptions.RequestException()))
    def test_main_with_exception(self):
        params = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'user01'
                    }
                }
            }
        }

        response = MeAllowedApplicationsIndex(params, {}).main()
        self.assertEqual(response['statusCode'], 500)
