import json
import logging
import os
from unittest import TestCase
from unittest.mock import patch, MagicMock

import requests
import responses

import settings
from me_applications_update import MeApplicationUpdate


class TestMeApplicationUpdate(TestCase):
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
            'body': {
                'name': 'あ' * 80,
                'description': 'A' * 180,
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

        responses.add(responses.POST,
                      settings.AUTHLETE_CLIENT_ENDPOINT + '/update/' + params['pathParameters']['client_id'],
                      json={"developer": "user01"}, status=200)
        # AuthleteUtilで呼ばれるAPI callをmockする
        responses.add(responses.GET, settings.AUTHLETE_CLIENT_ENDPOINT + '/get/' + params['pathParameters']['client_id'],
                      json={'developer': "user01"}, status=200)

        response = MeApplicationUpdate(params, {}).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), {"developer": "user01"})

    @patch('requests.post', MagicMock(side_effect=requests.exceptions.RequestException()))
    def test_main_with_exception(self):
        params = {
            'pathParameters': {
                'client_id': '123456789'
            },
            'body': {
                'name': 'あ' * 80,
                'description': 'A' * 180,
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

        responses.add(responses.POST,
                      settings.AUTHLETE_CLIENT_ENDPOINT + '/update/' + params['pathParameters']['client_id'],
                      json={"developer": "user01"}, status=200)
        # AuthleteUtilで呼ばれるAPI callをmockする
        responses.add(responses.GET,
                      settings.AUTHLETE_CLIENT_ENDPOINT + '/get/' + params['pathParameters']['client_id'],
                      json={'developer': "user01"}, status=200)

        response = MeApplicationUpdate(params, {}).main()
        self.assertEqual(response['statusCode'], 500)

    def test_validation_client_id_min(self):
        params = {
            'pathParameters': {
                'client_id': '0'
            },
            'body': {
                'name': 'あ' * 80,
                'description': 'A' * 180,
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

        response = MeApplicationUpdate(params, {}).main()
        self.assertEqual(response['statusCode'], 400)

    def test_validation_client_id_invalid_type(self):
        params = {
            'pathParameters': {
                'client_id': 'AAA'
            },
            'body': {
                'name': 'あ' * 80,
                'description': 'A' * 180,
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

        response = MeApplicationUpdate(params, {}).main()
        self.assertEqual(response['statusCode'], 400)

    def test_validation_name_max(self):
        params = {
            'pathParameters': {
                'client_id': '123456789'
            },
            'body': {
                'name': 'あ' * 81,
                'description': 'A' * 180,
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

        response = MeApplicationUpdate(params, {}).main()
        self.assertEqual(response['statusCode'], 400)

    def test_validation_description_max(self):
        params = {
            'pathParameters': {
                'client_id': '123456789'
            },
            'body': {
                'name': 'あ' * 80,
                'description': 'A' * 181,
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

        response = MeApplicationUpdate(params, {}).main()
        self.assertEqual(response['statusCode'], 400)

    def test_validation_redirect_urls_invalid_size(self):
        invalid_size = ['http://example.com/1', 'http://example.com/2', 'http://example.com/3', 'http://example.com/4',
                        'http://example.com/5', 'http://example.com/6']

        params = {
            'pathParameters': {
                'client_id': '123456789'
            },
            'body': {
                'name': 'あ' * 80,
                'description': 'A' * 180,
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

        response = MeApplicationUpdate(params, {}).main()
        self.assertEqual(response['statusCode'], 400)

    def test_validation_redirect_urls_invalid_type(self):
        base_url = 'http://example.com/'
        invalid_types = [
            'hogefugapiyo',  # URLの形式がおかしいパターン
            base_url + 'A' * (201-len(base_url))  # URLが200文字以上になるパターン
        ]

        for invalid_type in invalid_types:
            params = {
                'pathParameters': {
                    'client_id': '123456789'
                },
                'body': {
                    'name': 'あ' * 80,
                    'description': 'A' * 180,
                    'redirect_urls': [invalid_type]
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

            response = MeApplicationUpdate(params, {}).main()
            logging.fatal(response)
            self.assertEqual(response['statusCode'], 400)

    def test_validation_required_params(self):
        required_params = ['name', 'redirect_urls']

        for param in required_params:
            params = {
                'pathParameters': {
                    'client_id': '123456789'
                },
                'body': {
                    'name': 'あ' * 80,
                    'description': 'A' * 180,
                    'redirect_urls': ['http://example.com/1']
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

            response = MeApplicationUpdate(params, {}).main()
            logging.fatal(response)
            self.assertEqual(response['statusCode'], 400)

    def test_validation_without_client_id(self):
        params = {
            'pathParameters': {
            },
            'body': {
                'name': 'あ' * 80,
                'redirect_urls': ['http://example.com/1']
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

        response = MeApplicationUpdate(params, {}).main()
        self.assertEqual(response['statusCode'], 400)

    @responses.activate
    def test_validation_empty_description_ok(self):
        params = {
            'pathParameters': {
                'client_id': '123456789'
            },
            'body': {
                'name': 'あ' * 80,
                'redirect_urls': ['http://example.com/1']
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

        responses.add(responses.POST,
                      settings.AUTHLETE_CLIENT_ENDPOINT + '/update/' + params['pathParameters']['client_id'],
                      json={"developer": "user01"}, status=200)
        # AuthleteUtilで呼ばれるAPI callをmockする
        responses.add(responses.GET,
                      settings.AUTHLETE_CLIENT_ENDPOINT + '/get/' + params['pathParameters']['client_id'],
                      json={'developer': "user01"}, status=200)

        response = MeApplicationUpdate(params, {}).main()
        self.assertEqual(response['statusCode'], 200)
