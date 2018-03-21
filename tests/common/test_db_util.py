import boto3
import os
from db_util import DBUtil
from tests_util import TestsUtil
from unittest import TestCase


class TestTimeUtil(TestCase):
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
                'sort_key': 1520150272000000
            },
            {
                'article_id': 'testid000002',
                'status': 'draft',
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
