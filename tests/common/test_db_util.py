import os

import settings
from boto3.dynamodb.conditions import Key
from db_util import DBUtil
from jsonschema import ValidationError
from tests_util import TestsUtil
from unittest import TestCase
from record_not_found_error import RecordNotFoundError
from not_authorized_error import NotAuthorizedError


class TestDBUtil(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

        # create article_info_table
        cls.article_info_table_items = [
            {
                'article_id': 'testid000001',
                'status': 'public',
                'user_id': 'user0001',
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'testid000002',
                'status': 'draft',
                'user_id': 'user0002',
                'sort_key': 1520150272000000,
                'price': 100,
                'version': 2
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], cls.article_info_table_items)

        # create users_table
        cls.users_table_items = [
            {
                'user_id': 'test01',
                'user_display_name': 'test_display_name01',
                'self_introduction': 'test_introduction01'
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['USERS_TABLE_NAME'], cls.users_table_items)

        cls.comment_items = [
            {
                'comment_id': 'comment00001',
                'article_id': 'testid000001',
                'user_id': 'commentuser01',
                'text': 'hogefugapiyo',
                'created_at': 1520150272,
                'sort_key': 1520150272000000
            },
            {
                'comment_id': 'comment00002',
                'parent_id': 'comment00001',
                'replyed_user_id': 'commentuser02',
                'article_id': 'testid000001',
                'user_id': 'test_user',
                'text': 'hogefugapiyo',
                'created_at': 1520150272,
                'sort_key': 1520150272000000
            },
            {
                'comment_id': 'comment00003',
                'article_id': 'testid000002',
                'user_id': 'commentuser03',
                'text': 'hogefugapiyo',
                'created_at': 1520150272,
                'sort_key': 1520150272000000
            },
            {
                'comment_id': 'comment00004',
                'parent_id': 'comment00003',
                'replyed_user_id': 'commentuser02',
                'article_id': 'testid000002',
                'user_id': 'commentuser04',
                'text': 'hogefugapiyo',
                'created_at': 1520150272,
                'sort_key': 1520150272000000
            }

        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['COMMENT_TABLE_NAME'], cls.comment_items)

        article_pv_user_items = [
            {
                'article_id': 'article01',
                'user_id': 'one_day_before_user1',
                'article_user_id': 'article_user_1',
                'target_date': '2018-05-01',
                'created_at': 1520035200,
                'sort_key': 1520035200000000
            },
            {
                'article_id': 'one_day_before_article',
                'user_id': 'one_day_before_user1',
                'article_user_id': 'article_user_1',
                'target_date': '2018-05-01',
                'created_at': 1520035200,
                'sort_key': 1520035200000000
            },
            {
                'article_id': 'article01',
                'user_id': 'a1_user1',
                'article_user_id': 'article_user_1',
                'target_date': '2018-05-01',
                'created_at': 1520121600,
                'sort_key': 1520121600000000
            },
            {
                'article_id': 'article01',
                'user_id': 'a1_user2',
                'article_user_id': 'article_user_1',
                'target_date': '2018-05-01',
                'created_at': 1520125200,
                'sort_key': 1520125200000000
            },
            {
                'article_id': 'article02',
                'user_id': 'a1_user2',
                'article_user_id': 'article_user_2',
                'target_date': '2018-05-02',
                'created_at': 1520125200,
                'sort_key': 1520125200000000
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_PV_USER_TABLE_NAME'], article_pv_user_items)

        topic_items = [
            {'name': 'crypto', 'order': 1, 'index_hash_key': settings.TOPIC_INDEX_HASH_KEY},
            {'name': 'fashion', 'order': 2, 'index_hash_key': settings.TOPIC_INDEX_HASH_KEY},
            {'name': 'food', 'order': 3, 'index_hash_key': settings.TOPIC_INDEX_HASH_KEY}
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['TOPIC_TABLE_NAME'], topic_items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def test_exists_article_ok(self):
        result = DBUtil.exists_article(
            self.dynamodb,
            self.article_info_table_items[0]['article_id']
        )
        self.assertTrue(result)

    def test_exists_article_ok_exists_user(self):
        result = DBUtil.exists_article(
            self.dynamodb,
            self.article_info_table_items[0]['article_id'],
            user_id=self.article_info_table_items[0]['user_id'],
        )
        self.assertTrue(result)

    def test_exists_article_ok_exists_status(self):
        result = DBUtil.exists_article(
            self.dynamodb,
            self.article_info_table_items[0]['article_id'],
            status=self.article_info_table_items[0]['status']
        )
        self.assertTrue(result)

    def test_exists_article_ok_exists_user_and_status(self):
        result = DBUtil.exists_article(
            self.dynamodb,
            self.article_info_table_items[0]['article_id'],
            user_id=self.article_info_table_items[0]['user_id'],
            status=self.article_info_table_items[0]['status']
        )
        self.assertTrue(result)

    def test_exists_article_ng_not_exists_user_id(self):
        result = DBUtil.exists_article(
            self.dynamodb,
            self.article_info_table_items[0]['article_id'],
            user_id='hogefugapiyo',
        )
        self.assertFalse(result)

    def test_exists_article_ng_not_exists_article_id(self):
        result = DBUtil.exists_article(
            self.dynamodb,
            'hogefugapiyo',
            user_id=self.article_info_table_items[0]['user_id'],
        )
        self.assertFalse(result)

    def test_exists_article_ng_not_exists_status(self):
        result = DBUtil.exists_article(
            self.dynamodb,
            self.article_info_table_items[0]['article_id'],
            user_id=self.article_info_table_items[0]['user_id'],
            status='draft'
        )
        self.assertFalse(result)

    def test_validate_article_existence_ok(self):
        result = DBUtil.validate_article_existence(
            self.dynamodb,
            self.article_info_table_items[0]['article_id']
        )
        self.assertTrue(result)

    def test_validate_article_existence_ok_exists_user(self):
        result = DBUtil.validate_article_existence(
            self.dynamodb,
            self.article_info_table_items[0]['article_id'],
            user_id=self.article_info_table_items[0]['user_id'],
        )
        self.assertTrue(result)

    def test_validate_article_existence_ok_exists_status(self):
        result = DBUtil.validate_article_existence(
            self.dynamodb,
            self.article_info_table_items[0]['article_id'],
            status=self.article_info_table_items[0]['status']
        )
        self.assertTrue(result)

    def test_validate_article_existence_ok_exists_user_and_status(self):
        result = DBUtil.validate_article_existence(
            self.dynamodb,
            self.article_info_table_items[0]['article_id'],
            user_id=self.article_info_table_items[0]['user_id'],
            status=self.article_info_table_items[0]['status']
        )
        self.assertTrue(result)

    def test_validate_article_existence_ok_exists_user_and_version1(self):
        result = DBUtil.validate_article_existence(
            self.dynamodb,
            self.article_info_table_items[0]['article_id'],
            user_id=self.article_info_table_items[0]['user_id'],
            version=1
        )
        self.assertTrue(result)

    def test_validate_article_existence_ok_exists_user_and_version2(self):
        result = DBUtil.validate_article_existence(
            self.dynamodb,
            self.article_info_table_items[1]['article_id'],
            user_id=self.article_info_table_items[1]['user_id'],
            version=2
        )
        self.assertTrue(result)

    def test_validate_article_existence_ok_exists_user_and_status_and_is_purchased(self):
        result = DBUtil.validate_article_existence(
            self.dynamodb,
            self.article_info_table_items[1]['article_id'],
            user_id=self.article_info_table_items[1]['user_id'],
            status=self.article_info_table_items[1]['status'],
            is_purchased=True
        )
        self.assertTrue(result)

    def test_validate_article_existence_ng_not_exists_user_id(self):
        with self.assertRaises(NotAuthorizedError):
            DBUtil.validate_article_existence(
                self.dynamodb,
                self.article_info_table_items[0]['article_id'],
                user_id='hogefugapiyo',
            )

    def test_validate_article_existence_ng_not_validate_article_existence_id(self):
        with self.assertRaises(RecordNotFoundError):
            DBUtil.validate_article_existence(
                self.dynamodb,
                'hogefugapiyo',
                user_id=self.article_info_table_items[0]['user_id'],
            )

    def test_validate_article_existence_ng_not_exists_status(self):
        with self.assertRaises(RecordNotFoundError):
            DBUtil.validate_article_existence(
                self.dynamodb,
                self.article_info_table_items[0]['article_id'],
                user_id=self.article_info_table_items[0]['user_id'],
                status='draft'
            )

    def test_validate_article_existence_ng_not_exists_version1(self):
        with self.assertRaises(RecordNotFoundError):
            DBUtil.validate_article_existence(
                self.dynamodb,
                self.article_info_table_items[1]['article_id'],
                user_id=self.article_info_table_items[1]['user_id'],
                version=1
            )

    def test_validate_article_existence_ng_not_exists_version2(self):
        with self.assertRaises(RecordNotFoundError):
            DBUtil.validate_article_existence(
                self.dynamodb,
                self.article_info_table_items[0]['article_id'],
                user_id=self.article_info_table_items[0]['user_id'],
                version=2
            )

    def test_validate_article_existence_ng_not_exists_is_purchased(self):
        with self.assertRaises(RecordNotFoundError):
            DBUtil.validate_article_existence(
                self.dynamodb,
                self.article_info_table_items[0]['article_id'],
                user_id=self.article_info_table_items[0]['user_id'],
                is_purchased=True
            )

    def test_validate_user_existence_ok(self):
        result = DBUtil.validate_user_existence(
            self.dynamodb,
            self.users_table_items[0]['user_id']
        )
        self.assertTrue(result)

    def test_validate_user_existence_ng_not_exists_user_id(self):
        with self.assertRaises(RecordNotFoundError):
            DBUtil.validate_user_existence(
                self.dynamodb,
                'piyopiyo'
            )

    def test_validate_user_existence_in_thread_ok(self):
        for user_id in [self.comment_items[0]['user_id'], self.comment_items[1]['user_id']]:
            result = DBUtil.validate_user_existence_in_thread(
                self.dynamodb,
                user_id,
                self.comment_items[0]['comment_id']
            )
            self.assertTrue(result)

    def test_validate_user_existence_in_thread_with_user_id_in_other_thread(self):
        for user_id in [self.comment_items[2]['user_id'], self.comment_items[3]['user_id']]:
            with self.assertRaises(ValidationError):
                DBUtil.validate_user_existence_in_thread(
                    self.dynamodb,
                    user_id,
                    self.comment_items[0]['comment_id']
                )

    def test_validate_user_existence_in_thread_with_not_exist_id(self):
        with self.assertRaises(ValidationError):
            DBUtil.validate_user_existence_in_thread(
                self.dynamodb,
                'not_exist_id',
                self.comment_items[0]['comment_id']
            )

    def test_comment_existence_ok(self):
        result = DBUtil.comment_existence(
            self.dynamodb,
            self.comment_items[0]['comment_id']
        )
        self.assertTrue(result)

    def test_comment_existence_ng_not_exists_comment_id(self):
        result = DBUtil.comment_existence(
            self.dynamodb,
            'piyopiyo'
        )
        self.assertFalse(result)

    def test_validate_comment_existence_ok(self):
        result = DBUtil.validate_comment_existence(
            self.dynamodb,
            self.comment_items[0]['comment_id']
        )
        self.assertTrue(result)

    def test_validate_comment_existence_ng_not_exists_comment_id(self):
        with self.assertRaises(RecordNotFoundError):
            DBUtil.validate_comment_existence(
                self.dynamodb,
                'piyopiyo'
            )

    def test_validate_parent_comment_existence_ok(self):
        result = DBUtil.validate_parent_comment_existence(
            self.dynamodb,
            self.comment_items[0]['comment_id']
        )
        self.assertTrue(result)

    def test_validate_parent_comment_existence_ng_not_exists_comment_id(self):
        with self.assertRaises(RecordNotFoundError):
            DBUtil.validate_parent_comment_existence(
                self.dynamodb,
                'piyopiyo'
            )

    def test_validate_parent_comment_existence_ng_with_child_comment(self):
        with self.assertRaises(RecordNotFoundError):
            DBUtil.validate_parent_comment_existence(
                self.dynamodb,
                self.comment_items[1]['comment_id']
            )

    def test_get_validated_comment_existence_ok(self):
        result = DBUtil.get_validated_comment(
            self.dynamodb,
            self.comment_items[0]['comment_id']
        )
        self.assertEqual(result, self.comment_items[0])

    def test_get_validated_comment_ng_not_exists_comment_id(self):
        with self.assertRaises(RecordNotFoundError):
            DBUtil.get_validated_comment(
                self.dynamodb,
                'piyopiyo'
            )

    def test_items_values_empty_to_none_ok(self):
        values = {
            'test': 'test',
            'empty': ''
        }
        DBUtil.items_values_empty_to_none(values)

        self.assertEqual(values['test'], 'test')
        self.assertEqual(values['empty'], None)

    def test_query_all_items_with_limit(self):
        article_pv_user_table = self.dynamodb.Table(os.environ['ARTICLE_PV_USER_TABLE_NAME'])
        # ユースケースとしては1MBを超え、レスポンスにLastEvaluatedKeyが付与されて返ってくる場合だが
        # Limitを付与した際も同じレスポンスなのでLimitで代用している
        query_params = {
            'IndexName': 'target_date-sort_key-index',
            'KeyConditionExpression': Key('target_date').eq('2018-05-01'),
            'Limit': 1
        }

        response = DBUtil.query_all_items(article_pv_user_table, query_params)

        self.assertEqual(len(response), 4)

    def test_query_all_items_with_no_limit(self):
        article_pv_user_table = self.dynamodb.Table(os.environ['ARTICLE_PV_USER_TABLE_NAME'])
        query_params = {
            'IndexName': 'target_date-sort_key-index',
            'KeyConditionExpression': Key('target_date').eq('2018-05-01')
        }

        response = DBUtil.query_all_items(article_pv_user_table, query_params)

        self.assertEqual(len(response), 4)

    def test_validate_topic_ok(self):
        self.assertTrue(DBUtil.validate_topic(self.dynamodb, 'crypto'))

    def test_validate_topic_ng(self):
        with self.assertRaises(ValidationError):
            DBUtil.validate_topic(self.dynamodb, 'BTC')
