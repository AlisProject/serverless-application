import os
from unittest import TestCase
from unittest.mock import MagicMock, patch

import requests
import responses

import settings
from authlete_util import AuthleteUtil
from record_not_found_error import RecordNotFoundError


class TestAuthleteUtil(TestCase):
    def setUp(self):
        os.environ['AUTHLETE_API_KEY'] = 'XXXXXXXXXXXXXXXXX'
        os.environ['AUTHLETE_API_SECRET'] = 'YYYYYYYYYYYYYY'

    @responses.activate
    def test_is_accessible_client_ok_true(self):
        client_id = 123456789
        user_id = 'user01'

        responses.add(responses.GET, settings.AUTHLETE_CLIENT_ENDPOINT + '/get/' + str(client_id),
                      json={'developer': user_id}, status=200)

        result = AuthleteUtil.is_accessible_client(client_id, user_id)
        self.assertEqual(result, True)

    @responses.activate
    def test_is_accessible_client_ok_false(self):
        client_id = 123456789
        user_id = 'user01'

        responses.add(responses.GET, settings.AUTHLETE_CLIENT_ENDPOINT + '/get/' + str(client_id),
                      json={'developer': user_id}, status=200)

        result = AuthleteUtil.is_accessible_client(client_id, 'user02')
        self.assertEqual(result, False)

    @responses.activate
    def test_is_accessible_client_404(self):
        client_id = 123456789
        user_id = 'user01'

        responses.add(responses.GET, settings.AUTHLETE_CLIENT_ENDPOINT + '/get/' + str(client_id),
                      json={}, status=404)

        with self.assertRaises(RecordNotFoundError):
            AuthleteUtil.is_accessible_client(client_id, user_id)

    @patch('requests.get', MagicMock(side_effect=requests.exceptions.RequestException()))
    def test_is_accessible_client_with_exception(self):
        client_id = 123456789
        user_id = 'user01'

        with self.assertRaises(Exception):
            AuthleteUtil.is_accessible_client(client_id, user_id)

    def test_verify_valid_response(self):
        cases = [
            {
                'status_code': 200,
                'request_client_id': None,
                'exception': None
            },
            {
                'status_code': 200,
                'request_client_id': '12345',
                'exception': False
            },
            {
                'status_code': 404,
                'request_client_id': None,
                'exception': Exception
            },
            {
                'status_code': 404,
                'request_client_id': '12345',
                'exception': RecordNotFoundError
            },
            {
                'status_code': 500,
                'request_client_id': None,
                'exception': Exception
            },
            {
                'status_code': 500,
                'request_client_id': '12345',
                'exception': Exception
            }
        ]

        for case in cases:
            with self.subTest():
                response = requests.Response
                response.status_code = case['status_code']

                if case['exception'] is Exception:
                    with self.assertRaises(Exception):
                        AuthleteUtil.verify_valid_response(response, case['request_client_id'])

                if case['exception'] is RecordNotFoundError:
                    with self.assertRaises(RecordNotFoundError):
                        AuthleteUtil.verify_valid_response(response, case['request_client_id'])

                if not case['exception']:
                    try:
                        AuthleteUtil.verify_valid_response(response, case['request_client_id'])
                    except Exception as err:
                        self.fail(err)
