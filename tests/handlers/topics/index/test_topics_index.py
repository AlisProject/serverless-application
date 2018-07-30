import json
import os
from unittest import TestCase
from topics_index import TopicsIndex
from tests_util import TestsUtil


class TestTopicsIndex(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

        # create users_table
        cls.topic_items = [
            {'name': 'crypto', 'order': 1, 'index_hash_key': 'index_hash_key'},
            {'name': 'fashion', 'order': 2, 'index_hash_key': 'index_hash_key'},
            {'name': 'food', 'order': 3, 'index_hash_key': 'index_hash_key'}
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['TOPIC_TABLE_NAME'], cls.topic_items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def test_main(self):
        response = TopicsIndex({}, {}, dynamodb=self.dynamodb).main()

        expected = [topic['name'] for topic in self.topic_items]

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), expected)
