import os
from unittest import TestCase
from unittest.mock import patch, MagicMock

import requests
import responses

import settings
from me_allowd_app_index import MeAllowdAppIndex


class TestMeAllowdAppIndex(TestCase):
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

        responses.add(responses.GET, settings.AUTHLETE_CLIENT_ENDPOINT + '/authorization/get/list',
                      json={'statusCode': 200, 'body': ''}, status=200)
        response = MeAllowdAppIndex(params, {}).main()
        self.assertEqual(response['statusCode'], 200)

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

        response = MeAllowdAppIndex(params, {}).main()
        self.assertEqual(response['statusCode'], 500)
