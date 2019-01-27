import json
import os
from unittest import TestCase
from unittest.mock import patch, MagicMock

import requests
import responses

import settings
from me_applications_delete import MeApplicationDelete


class TestMeApplicationDelete(TestCase):
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
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'user01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        responses.add(responses.DELETE,
                      settings.AUTHLETE_CLIENT_ENDPOINT + '/delete/' + params['pathParameters']['client_id'],
                      json={"developer": "user01"}, status=200)
        # AuthleteUtilで呼ばれるAPI callをmockする
        responses.add(responses.GET,
                      settings.AUTHLETE_CLIENT_ENDPOINT + '/get/' + params['pathParameters']['client_id'],
                      json={'developer': "user01"}, status=200)

        response = MeApplicationDelete(params, {}).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), {"developer": "user01"})

    @responses.activate
    def test_main_ng_not_accessible(self):
        params = {
            'pathParameters': {
                'client_id': '123456789'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'user01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        responses.add(responses.DELETE,
                      settings.AUTHLETE_CLIENT_ENDPOINT + '/delete/' + params['pathParameters']['client_id'],
                      json={"developer": "user02"}, status=200)
        # AuthleteUtilで呼ばれるAPI callをmockする
        responses.add(responses.GET,
                      settings.AUTHLETE_CLIENT_ENDPOINT + '/get/' + params['pathParameters']['client_id'],
                      json={'developer': "user01"}, status=200)

        response = MeApplicationDelete(params, {}).main()

        self.assertEqual(response['statusCode'], 403)

    @patch('requests.delete', MagicMock(side_effect=requests.exceptions.RequestException()))
    def test_main_with_exception(self):
        params = {
            'pathParameters': {
                'client_id': '123456789'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'user01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        responses.add(responses.DELETE,
                      settings.AUTHLETE_CLIENT_ENDPOINT + '/delete/' + params['pathParameters']['client_id'],
                      json={"developer": "user01"}, status=200)
        # AuthleteUtilで呼ばれるAPI callをmockする
        responses.add(responses.GET,
                      settings.AUTHLETE_CLIENT_ENDPOINT + '/get/' + params['pathParameters']['client_id'],
                      json={'developer': "user01"}, status=200)

        response = MeApplicationDelete(params, {}).main()
        self.assertEqual(response['statusCode'], 500)

    def test_validation_client_id_min(self):
        params = {
            'pathParameters': {
                'client_id': '0'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'user01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        response = MeApplicationDelete(params, {}).main()
        self.assertEqual(response['statusCode'], 400)

    def test_validation_client_id_invalid_type(self):
        params = {
            'pathParameters': {
                'client_id': 'AAA'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'user01',
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        response = MeApplicationDelete(params, {}).main()
        self.assertEqual(response['statusCode'], 400)
