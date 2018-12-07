import json
import os
from unittest import TestCase

from tests_util import TestsUtil
from me_info_first_experiences_update import MeInfoFirstExperiencesUpdate


class TestMeInfoFirstExperiencesUpdate(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    def setUp(self):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(self.dynamodb)

        self.user_first_experience_items = [
            {
                'user_id': 'TEST01',
                'is_liked_article': False,
                'is_tipped_article': False,
                'is_got_token': False,
                'is_created_article': False
            },
            {
                'user_id': 'TEST02',
                'is_liked_article': True,
                'is_tipped_article': False,
                'is_got_token': False,
                'is_created_article': False
            }
        ]
        self.user_first_experience_table = self.dynamodb.Table(os.environ['USER_FIRST_EXPERIENCE_TABLE_NAME'])
        TestsUtil.create_table(self.dynamodb, os.environ['USER_FIRST_EXPERIENCE_TABLE_NAME'],
                               self.user_first_experience_items)

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def test_main_ok(self):
        target_data = self.user_first_experience_items[0]

        expected = {
            'user_id': 'TEST01',
            'is_liked_article': False,
            'is_tipped_article': False,
            'is_got_token': False,
            'is_created_article': False
        }

        # 特定のユーザーに対して全パターンのテストを行う
        test_targets = ['is_liked_article', 'is_tipped_article', 'is_got_token', 'is_created_article']
        for target in test_targets:
            params = {
                'body': {
                    'user_first_experience': target
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'cognito:username': target_data['user_id']
                        }
                    }
                }
            }
            params['body'] = json.dumps(params['body'])

            response = MeInfoFirstExperiencesUpdate(event=params, context={}, dynamodb=self.dynamodb).main()
            # expectedの状態を変更する
            expected[target] = True

            actual = self.user_first_experience_table.get_item(Key={'user_id': target_data['user_id']})['Item']
            self.assertEqual(expected, actual)
            self.assertEqual(response['statusCode'], 200)

    def test_main_ok_already_true(self):
        target_data = self.user_first_experience_items[1]
        params = {
            'body': {
                'user_first_experience': 'is_liked_article'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_data['user_id']
                    }
                }
            }
        }
        params['body'] = json.dumps(params['body'])

        response = MeInfoFirstExperiencesUpdate(event=params, context={}, dynamodb=self.dynamodb).main()

        actual = self.user_first_experience_table.get_item(Key={'user_id': target_data['user_id']})['Item']
        expected = {
            'user_id': 'TEST02',
            'is_liked_article': True,
            'is_tipped_article': False,
            'is_got_token': False,
            'is_created_article': False
        }

        self.assertEqual(expected, actual)
        self.assertEqual(response['statusCode'], 200)

    def test_main_ok_new_user(self):
        params = {
            'body': {
                'user_first_experience': 'is_liked_article'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'new_user'
                    }
                }
            }
        }
        params['body'] = json.dumps(params['body'])

        response = MeInfoFirstExperiencesUpdate(event=params, context={}, dynamodb=self.dynamodb).main()

        actual = self.user_first_experience_table.get_item(Key={'user_id': 'new_user'})['Item']
        expected = {
            'user_id': 'new_user',
            'is_liked_article': True,
        }

        self.assertEqual(expected, actual)
        self.assertEqual(response['statusCode'], 200)

    def test_main_with_invalid_enum(self):
        target_data = self.user_first_experience_items[0]
        params = {
            'body': {
                'user_first_experience': 'hogefugapiyo'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_data['user_id']
                    }
                }
            }
        }
        params['body'] = json.dumps(params['body'])

        response = MeInfoFirstExperiencesUpdate(event=params, context={}, dynamodb=self.dynamodb).main()
        self.assertEqual(response['statusCode'], 400)

    def test_main_with_no_user_first_experience(self):
        target_data = self.user_first_experience_items[0]
        params = {
            'body': {},
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_data['user_id']
                    }
                }
            }
        }
        params['body'] = json.dumps(params['body'])

        response = MeInfoFirstExperiencesUpdate(event=params, context={}, dynamodb=self.dynamodb).main()
        self.assertEqual(response['statusCode'], 400)

    def test_main_with_no_body(self):
        target_data = self.user_first_experience_items[0]
        params = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_data['user_id']
                    }
                }
            }
        }
        response = MeInfoFirstExperiencesUpdate(event=params, context={}, dynamodb=self.dynamodb).main()
        self.assertEqual(response['statusCode'], 400)
