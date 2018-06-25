import os
from db_util import DBUtil
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
                'sort_key': 1520150272000000
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
                'user_id': 'test_user',
                'text': 'hogefugapiyo',
                'created_at': 1520150272,
                'sort_key': 1520150272000000
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['COMMENT_TABLE_NAME'], cls.comment_items)

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

    def test_comment_existence_ok(self):
        result = DBUtil.comment_existence(
            self.dynamodb,
            self.comment_items[0]['comment_id']
        )
        self.assertTrue(result)

    def test_comment_existence_ng_not_exists_user_id(self):
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

    def test_validate_comment_existence_ng_not_exists_user_id(self):
        with self.assertRaises(RecordNotFoundError):
            DBUtil.validate_comment_existence(
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
