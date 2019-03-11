import os
import boto3
import json
from unittest import TestCase
from users_info_show import UsersInfoShow
from tests_util import TestsUtil


class TestUsersArticlesPublic(TestCase):
    dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:4569/')

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

        # create users_table
        cls.users_table_items = [
            {
                'user_id': 'test01',
                'user_display_name': 'test_display_name01',
                'self_introduction': 'test_introduction01',
                'icon_image_url': 'test_icon01'
            },
            {
                'user_id': 'test02',
                'user_display_name': None,
                'self_introduction': None,
                'icon_image_url': None

            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['USERS_TABLE_NAME'], cls.users_table_items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def assert_bad_request(self, params):
        function = UsersInfoShow(params, {}, dynamodb=self.dynamodb)
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    def test_main_ok(self):
        target_user_item = self.users_table_items[0]
        params = {
            'pathParameters': {
                'user_id': target_user_item['user_id']
            }
        }

        response = UsersInfoShow(params, {}, dynamodb=self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), target_user_item)

    def test_main_ok_exists_none_data_item(self):
        target_user_item = self.users_table_items[1]
        params = {
            'pathParameters': {
                'user_id': target_user_item['user_id']
            }
        }

        response = UsersInfoShow(params, {}, dynamodb=self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), target_user_item)

    def test_main_ng_not_exists_user(self):
        params = {
            'pathParameters': {
                'user_id': 'hogera'
            }
        }

        response = UsersInfoShow(params, {}, dynamodb=self.dynamodb).main()

        self.assertEqual(response['statusCode'], 404)

    def test_validation_with_no_user_id_param(self):
        params = {
            'pathParameters': {
            }
        }

        self.assert_bad_request(params)

    def test_validation_user_id_min(self):
        params = {
            'pathParameters': {
                'user_id': 'AA'
            }
        }

        self.assert_bad_request(params)

    def test_validation_user_id_max(self):
        params = {
            'pathParameters': {
                'user_id': 'A' * 51
            }
        }

        self.assert_bad_request(params)
