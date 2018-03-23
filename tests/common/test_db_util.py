import boto3
import os
from db_util import DBUtil
from tests_util import TestsUtil
from unittest import TestCase
from record_not_found_error import RecordNotFoundError
from not_authorized_error import NotAuthorizedError


class TestDBUtil(TestCase):
    dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:4569/')

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
                'sort_key': 1520150272000000
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_INFO_TABLE_NAME'], cls.article_info_table_items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def test_exists_public_article_ok(self):
        result = DBUtil.exists_public_article(self.dynamodb, self.article_info_table_items[0]['article_id'])
        self.assertTrue(result)

    def test_exists_public_article_ng_status_draft(self):
        result = DBUtil.exists_public_article(self.dynamodb, self.article_info_table_items[1]['article_id'])
        self.assertFalse(result)

    def test_exists_public_article_ng_not_exists(self):
        result = DBUtil.exists_public_article(self.dynamodb, 'hogefugapiyo')
        self.assertFalse(result)

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
