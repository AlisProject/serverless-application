import os
from unittest import TestCase
from unittest.mock import MagicMock, patch

import requests

from authorizer import Authorizer


class TestAuthorizer(TestCase):
    def setUp(self):
        os.environ['AUTHLETE_API_KEY'] = 'hoge'
        os.environ['AUTHLETE_API_SECRET'] = 'fuga'

    def tearDown(self):
        pass

    @patch('authorizer.Authorizer._Authorizer__introspect', MagicMock(return_value={'action': 'OK', 'subject': 'John'}))
    def test_main_ok(self):
        event = {
            'methodArn': 'arn:aws:execute-api:ap-northeast-1:000000000000:abcdefghij/*/GET/articles/images:batchGet',
            'authorizationToken': 'ABCDEFG'
        }

        result = Authorizer(event, {}).main()

        expected = {
            "principalId": 'John',
            "policyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": 'execute-api:Invoke',
                        "Effect": 'Allow',
                        "Resource": 'arn:aws:execute-api:ap-northeast-1:000000000000:abcdefghij/*/GET/articles/images:batchGet'
                    }
                ]
            }
        }
        self.assertEqual(result, expected)

    def test_main_deny_api_call(self):
        event = {
            'methodArn': 'arn:aws:execute-api:ap-northeast-1:000000000000:abcdefghij/*/GET/articles/images:batchGet',
            'authorizationToken': 'ABCDEFG'
        }

        expected = {
            "principalId": 'John',
            "policyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": 'execute-api:Invoke',
                        "Effect": 'Deny',
                        "Resource": 'arn:aws:execute-api:ap-northeast-1:000000000000:abcdefghij/*/GET/articles/images:batchGet'
                    }
                ]
            }
        }

        for action in ['BAD_REQUEST', 'FORBIDDEN', 'UNAUTHORIZED']:
            with patch('authorizer.Authorizer._Authorizer__introspect',
                       MagicMock(return_value={'action': action, 'subject': 'John'})):
                with self.subTest():
                    result = Authorizer(event, {}).main()
                    self.assertEqual(result, expected)

    @patch('authorizer.Authorizer._Authorizer__introspect',
           MagicMock(return_value={'action': 'OTHER', 'subject': 'John'}))
    def test_main_internal_server_error(self):
        event = {
            'methodArn': 'arn:aws:execute-api:ap-northeast-1:000000000000:abcdefghij/*/GET/articles/images:batchGet',
            'authorizationToken': 'ABCDEFG'
        }

        with self.assertRaises(Exception) as e:
            Authorizer(event, {}).main()

        self.assertEqual(e.exception.args[0], 'Internal Server Error')

    @patch('requests.post', MagicMock(side_effect=requests.exceptions.RequestException()))
    def test_introspect(self):
        event = {
            'methodArn': 'arn:aws:execute-api:ap-northeast-1:000000000000:abcdefghij/*/GET/articles/images:batchGet',
            'authorizationToken': 'ABCDEFG'
        }
        authorizer = Authorizer(event, {})
        scope = ['read', 'write']

        with self.assertRaises(Exception) as e:
            authorizer._Authorizer__introspect(scope)

        self.assertEqual(e.exception.args[0], 'Internal Server Error(RequestException)')

    def test_generate_policy(self):
        event = {
            'methodArn': 'arn:aws:execute-api:ap-northeast-1:000000000000:abcdefghij/*/GET/articles/images:batchGet',
            'authorizationToken': 'ABCDEFG'
        }
        authorizer = Authorizer(event, {})
        principal_id = 'hogehoge'
        effect = 'Allow'
        resource = event['methodArn']

        result = authorizer._Authorizer__generate_policy(principal_id, effect, resource)

        expected = {
            "principalId": 'hogehoge',
            "policyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": 'execute-api:Invoke',
                        "Effect": 'Allow',
                        "Resource": 'arn:aws:execute-api:ap-northeast-1:000000000000:abcdefghij/*/GET/articles/images:batchGet'
                    }
                ]
            }
        }

        self.assertEqual(result, expected)

    def test_extract_method_and_path(self):
        event = {
            'methodArn': 'arn:aws:execute-api:ap-northeast-1:000000000000:abcdefghij/*/GET/articles/images:batchGet',
            'authorizationToken': 'ABCDEFG'
        }
        authorizer = Authorizer(event, {})

        http_method, resource_path = authorizer._Authorizer__extract_method_and_path(event['methodArn'])
        self.assertEqual(http_method, 'GET')
        self.assertEqual(resource_path, 'articles/images:batchGet')

    def test_get_required_scopes(self):
        # http_method, resource_path, expected(scope)の順でテストケースを定義
        cases = [
            ['GET', 'me/unread_notification_managers', ['read']],
            ['PUT', 'me/unread_notification_managers', ['read']],
            ['POST', 'me/unread_notification_managers', ['read', 'write']],
            ['POST', 'me/users/fraud', ['read', 'write']]
        ]

        authorizer = Authorizer({}, {})

        for case in cases:
            with self.subTest():
                scope = authorizer._Authorizer__get_required_scopes(case[0], case[1])
                self.assertEqual(scope, case[2])
