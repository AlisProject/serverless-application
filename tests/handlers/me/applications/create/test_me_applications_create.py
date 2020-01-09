import json
import logging
import os
from unittest import TestCase
from unittest.mock import patch, MagicMock

import requests
import responses

import settings
from me_applications_create import MeApplicationsCreate


class TestMeApplicationsCreate(TestCase):
    def setUp(self):
        os.environ['AUTHLETE_API_KEY'] = 'XXXXXXXXXXXXXXXXX'
        os.environ['AUTHLETE_API_SECRET'] = 'YYYYYYYYYYYYYY'

    def tearDown(self):
        pass

    @responses.activate
    def test_main_ok_type_web(self):
        params = {
            'body': {
                'name': 'あ' * 80,
                'description': 'A' * 180,
                'application_type': 'WEB',
                'redirect_urls': ['http://example.com/1', 'http://example.com/2',
                                  'http://example.com/3', 'http://example.com/4', 'http://example.com/5']
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

        params['body'] = json.dumps(params['body'])

        responses.add(responses.POST, settings.AUTHLETE_CLIENT_ENDPOINT + '/create',
                      json={"developer": "matsumatsu20"}, status=200)

        response = MeApplicationsCreate(params, {}).main()

        logging.fatal(response)

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), {"developer": "matsumatsu20"})
        self.assertEqual('CONFIDENTIAL', json.loads(responses.calls[0].request.body).get('clientType'))
        self.assertEqual('CLIENT_SECRET_BASIC', json.loads(responses.calls[0].request.body).get('tokenAuthMethod'))

    @responses.activate
    def test_main_ok_type_native(self):
        params = {
            'body': {
                'name': 'あ' * 80,
                'description': 'A' * 180,
                'application_type': 'NATIVE',
                'redirect_urls': ['http://example.com/1', 'http://example.com/2',
                                  'http://example.com/3', 'http://example.com/4', 'http://example.com/5']
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

        params['body'] = json.dumps(params['body'])

        responses.add(responses.POST, settings.AUTHLETE_CLIENT_ENDPOINT + '/create',
                      json={"developer": "matsumatsu20"}, status=200)

        response = MeApplicationsCreate(params, {}).main()

        logging.fatal(response)

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), {"developer": "matsumatsu20"})
        self.assertEqual('PUBLIC', json.loads(responses.calls[0].request.body).get('clientType'))
        self.assertEqual('NONE', json.loads(responses.calls[0].request.body).get('tokenAuthMethod'))

    @patch('requests.post', MagicMock(side_effect=requests.exceptions.RequestException()))
    def test_main_with_exception(self):
        params = {
            'body': {
                'name': 'あ' * 80,
                'description': 'A' * 180,
                'application_type': 'WEB',
                'redirect_urls': ['http://example.com']
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

        params['body'] = json.dumps(params['body'])

        response = MeApplicationsCreate(params, {}).main()
        self.assertEqual(response['statusCode'], 500)

    def test_validation_name_max(self):
        params = {
            'body': {
                'name': 'あ' * 81,
                'description': 'A' * 180,
                'application_type': 'WEB',
                'redirect_urls': ['http://example.com']
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

        params['body'] = json.dumps(params['body'])

        response = MeApplicationsCreate(params, {}).main()
        self.assertEqual(response['statusCode'], 400)

    def test_validation_description_max(self):
        params = {
            'body': {
                'name': 'あ' * 80,
                'description': 'A' * 181,
                'application_type': 'WEB',
                'redirect_urls': ['http://example.com']
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

        params['body'] = json.dumps(params['body'])

        response = MeApplicationsCreate(params, {}).main()
        self.assertEqual(response['statusCode'], 400)

    @responses.activate
    def test_validation_application_type_with_valid_type(self):
        valid_name = ['WEB', 'NATIVE']

        for name in valid_name:
            params = {
                'body': {
                    'name': 'あ' * 80,
                    'description': 'A' * 180,
                    'application_type': name,
                    'redirect_urls': ['http://example.com']
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

            params['body'] = json.dumps(params['body'])

            responses.add(responses.POST, settings.AUTHLETE_CLIENT_ENDPOINT + '/create',
                          json={"developer": "matsumatsu20"}, status=200)

            response = MeApplicationsCreate(params, {}).main()
            self.assertEqual(response['statusCode'], 200)

    def test_validation_application_type_with_invalid_type(self):
        invalid_name = ['AAA', 10]

        for name in invalid_name:
            params = {
                'body': {
                    'name': 'あ' * 80,
                    'description': 'A' * 180,
                    'application_type': name,
                    'redirect_urls': ['http://example.com']
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

            params['body'] = json.dumps(params['body'])

            response = MeApplicationsCreate(params, {}).main()
            self.assertEqual(response['statusCode'], 400)

    def test_validation_redirect_urls_invalid_size(self):
        invalid_size = ['http://example.com/1', 'http://example.com/2', 'http://example.com/3', 'http://example.com/4',
                        'http://example.com/5', 'http://example.com/6']

        params = {
            'body': {
                'name': 'あ' * 80,
                'description': 'A' * 180,
                'application_type': 'WEB',
                'redirect_urls': invalid_size
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

        params['body'] = json.dumps(params['body'])

        response = MeApplicationsCreate(params, {}).main()
        self.assertEqual(response['statusCode'], 400)

    def test_validation_redirect_urls_invalid_type(self):
        base_url = 'http://example.com/'
        invalid_types = [
            'hogefugapiyo',  # URLの形式がおかしいパターン
            base_url + 'A' * (201-len(base_url))  # URLが200文字以上になるパターン
        ]

        for type in invalid_types:

            params = {
                'body': {
                    'name': 'あ' * 80,
                    'description': 'A' * 180,
                    'application_type': 'WEB',
                    'redirect_urls': [type]
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

            params['body'] = json.dumps(params['body'])

            response = MeApplicationsCreate(params, {}).main()
            logging.fatal(response)
            self.assertEqual(response['statusCode'], 400)

    def test_validation_required_params(self):
        required_params = ['name', 'application_type', 'redirect_urls']

        for param in required_params:
            params = {
                'body': {
                    'name': 'あ' * 80,
                    'description': 'A' * 180,
                    'application_type': 'WEB',
                    'redirect_urls': ['http://example.com/1', 'http://example.com/2',
                                      'http://example.com/3', 'http://example.com/4', 'http://example.com/5']
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

            del params['body'][param]
            params['body'] = json.dumps(params['body'])

            response = MeApplicationsCreate(params, {}).main()
            logging.fatal(response)
            self.assertEqual(response['statusCode'], 400)

    @responses.activate
    def test_validation_empty_description_ok(self):
        params = {
            'body': {
                'name': 'あ' * 80,
                'application_type': 'WEB',
                'redirect_urls': ['http://example.com']
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

        params['body'] = json.dumps(params['body'])

        responses.add(responses.POST, settings.AUTHLETE_CLIENT_ENDPOINT + '/create',
                      json={"developer": "matsumatsu20"}, status=200)

        response = MeApplicationsCreate(params, {}).main()
        self.assertEqual(response['statusCode'], 200)
