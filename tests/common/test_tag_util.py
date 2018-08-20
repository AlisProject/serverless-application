import os
from decimal import Decimal
from unittest import TestCase

from tag_util import TagUtil
from tests_util import TestsUtil


class TestDBUtil(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    def setUp(self):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(self.dynamodb)

        # create article_info_table
        self.tag_table_items = [
            {
                'name': 'A',
                'count': 2,
                'created_at': 1520150272
            },
            {
                'name': 'B',
                'count': 3,
                'created_at': 1520150272
            },
            {
                'name': 'E',
                'count': 4,
                'created_at': 1520150272
            }
        ]
        TestsUtil.create_table(self.dynamodb, os.environ['TAG_TABLE_NAME'], self.tag_table_items)

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def test_main_ok(self):
        before_tag_names = ['A', 'B', 'C']
        after_tag_names = ['A', 'D', 'E']

        TagUtil.create_and_count(self.dynamodb, before_tag_names, after_tag_names)

        tag_table = self.dynamodb.Table(os.environ['TAG_TABLE_NAME'])
        tags = tag_table.scan()['Items']

        expected = [
            {
                'name': 'A',
                'count': Decimal('2'),
            },
            {
                'name': 'B',
                'count': Decimal('2'),
            },
            {
                'name': 'D',
                'count': Decimal('1'),
            },
            {
                'name': 'E',
                'count': Decimal('5'),
            },
        ]

        for tag in tags:
            del tag['created_at']

        tags = sorted(tags, key=lambda t: t['name'])

        self.assertEqual(tags, expected)

    def test_main_with_null_before_tag_names(self):
        before_tag_names = None
        after_tag_names = ['A', 'D', 'E']

        TagUtil.create_and_count(self.dynamodb, before_tag_names, after_tag_names)

        tag_table = self.dynamodb.Table(os.environ['TAG_TABLE_NAME'])
        tags = tag_table.scan()['Items']

        expected = [
            {
                'name': 'A',
                'count': Decimal('3'),
            },
            {
                'name': 'B',
                'count': Decimal('3'),
            },
            {
                'name': 'D',
                'count': Decimal('1'),
            },
            {
                'name': 'E',
                'count': Decimal('5'),
            },
        ]

        for tag in tags:
            del tag['created_at']

        tags = sorted(tags, key=lambda t: t['name'])

        self.assertEqual(tags, expected)

    def test_main_with_null_after_tag_names(self):
        before_tag_names = ['A', 'B', 'C']
        after_tag_names = None

        TagUtil.create_and_count(self.dynamodb, before_tag_names, after_tag_names)

        tag_table = self.dynamodb.Table(os.environ['TAG_TABLE_NAME'])
        tags = tag_table.scan()['Items']

        expected = [
            {
                'name': 'A',
                'count': Decimal('1'),
            },
            {
                'name': 'B',
                'count': Decimal('2'),
            },
            {
                'name': 'E',
                'count': Decimal('4'),
            },
        ]

        for tag in tags:
            del tag['created_at']

        tags = sorted(tags, key=lambda t: t['name'])

        self.assertEqual(tags, expected)
