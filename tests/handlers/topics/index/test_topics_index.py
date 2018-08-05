import json
import os
from unittest import TestCase

import settings

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
            {'name': 'crypto', 'display_name': '暗号通貨', 'order': 1, 'index_hash_key': settings.TOPIC_INDEX_HASH_KEY},
            {'name': 'fashion', 'fashion': 'ファッション', 'order': 2, 'index_hash_key': settings.TOPIC_INDEX_HASH_KEY},
            {'name': 'food', 'fashion': '食', 'order': 3, 'index_hash_key': settings.TOPIC_INDEX_HASH_KEY}
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['TOPIC_TABLE_NAME'], cls.topic_items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def test_main(self):
        response = TopicsIndex({}, {}, dynamodb=self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), self.topic_items)
