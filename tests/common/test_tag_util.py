from decimal import Decimal
from unittest import TestCase

from elasticsearch import Elasticsearch
from jsonschema import ValidationError
from tests_es_util import TestsEsUtil

from tag_util import TagUtil
from tests_util import TestsUtil


class TestTagUtil(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()
    elasticsearch = Elasticsearch(
        hosts=[{'host': 'localhost'}]
    )

    def setUp(self):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(self.dynamodb)
        TestsEsUtil.create_tag_index(self.elasticsearch)

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)
        self.elasticsearch.indices.delete(index="tags", ignore=[404])

    def test_create_and_count_ok(self):
        TagUtil.create_tag(self.elasticsearch, 'A')
        TagUtil.update_count(self.elasticsearch, 'A', 1)
        TagUtil.create_tag(self.elasticsearch, 'B')

        # count: 0 のTagを作成する
        TagUtil.create_tag(self.elasticsearch, 'F')
        TagUtil.update_count(self.elasticsearch, 'F', -1)
        self.elasticsearch.indices.refresh(index="tags")

        before_tag_names = ['A', 'B', 'C', 'F']
        after_tag_names = ['A', 'D', 'E']

        TagUtil.create_and_count(self.elasticsearch, before_tag_names, after_tag_names)

        self.elasticsearch.indices.refresh(index="tags")

        tags = TestsEsUtil.get_all_tags(self.elasticsearch)

        expected = [
            {
                'name': 'A',
                'name_with_analyzer': 'A',
                'count': Decimal('2'),
            },
            {
                'name': 'B',
                'name_with_analyzer': 'B',
                'count': Decimal('0'),
            },
            {
                'name': 'D',
                'name_with_analyzer': 'D',
                'count': Decimal('1'),
            },
            {
                'name': 'E',
                'name_with_analyzer': 'E',
                'count': Decimal('1'),
            },
            {
                'name': 'F',
                'name_with_analyzer': 'F',
                'count': Decimal('0'),
            },
        ]

        for tag in tags:
            del tag['created_at']

        tags = sorted(tags, key=lambda t: t['name'])

        self.assertEqual(tags, expected)

    def test_create_and_count_with_null_before_tag_names(self):
        TagUtil.create_tag(self.elasticsearch, 'A')
        TagUtil.create_tag(self.elasticsearch, 'B')
        self.elasticsearch.indices.refresh(index="tags")

        before_tag_names = None
        after_tag_names = ['a', 'D', 'E']

        TagUtil.create_and_count(self.elasticsearch, before_tag_names, after_tag_names)
        self.elasticsearch.indices.refresh(index="tags")

        tags = TestsEsUtil.get_all_tags(self.elasticsearch)

        expected = [
            {
                'name': 'A',
                'name_with_analyzer': 'A',
                'count': Decimal('2'),
            },
            {
                'name': 'B',
                'name_with_analyzer': 'B',
                'count': Decimal('1'),
            },
            {
                'name': 'D',
                'name_with_analyzer': 'D',
                'count': Decimal('1'),
            },
            {
                'name': 'E',
                'name_with_analyzer': 'E',
                'count': Decimal('1'),
            },
        ]

        for tag in tags:
            del tag['created_at']

        tags = sorted(tags, key=lambda t: t['name'])

        self.assertEqual(tags, expected)

    def test_create_and_count_with_null_after_tag_names(self):
        TagUtil.create_tag(self.elasticsearch, 'A')
        TagUtil.create_tag(self.elasticsearch, 'B')
        TagUtil.create_tag(self.elasticsearch, 'E')
        self.elasticsearch.indices.refresh(index="tags")

        before_tag_names = ['A', 'b', 'C']
        after_tag_names = None

        TagUtil.create_and_count(self.elasticsearch, before_tag_names, after_tag_names)
        self.elasticsearch.indices.refresh(index="tags")

        tags = TestsEsUtil.get_all_tags(self.elasticsearch)

        expected = [
            {
                'name': 'A',
                'name_with_analyzer': 'A',
                'count': Decimal('0'),
            },
            {
                'name': 'B',
                'name_with_analyzer': 'B',
                'count': Decimal('0'),
            },
            {
                'name': 'E',
                'name_with_analyzer': 'E',
                'count': Decimal('1'),
            },
        ]

        for tag in tags:
            del tag['created_at']

        tags = sorted(tags, key=lambda t: t['name'])

        self.assertEqual(tags, expected)

    def test_validate_format(self):
        def expected_raise_error(args):
            with self.assertRaises(ValidationError):
                TagUtil.validate_format(args)

        def expected_raise_no_error(args):
            try:
                TagUtil.validate_format(args)
            except ValidationError:
                self.fail('expected no error is raised')

        expected_raise_no_error(['ABCDE', 'b', 'あいうえおぁぃぅぇぉﾊﾝｶｸ'])
        expected_raise_no_error(['チャーハン', '＆＄％！”＃', '𪚲🍣𪚲'])
        expected_raise_no_error(['aa-aa', 'Ruby on Rails', 'C C C C C'])
        expected_raise_error(['XSS', 'CSRF', '<script>'])
        expected_raise_error(['ALIS', 'INVALID '])
        expected_raise_error(['ALIS', ' INVALID'])
        expected_raise_error(['ALIS', '-INVALID'])
        expected_raise_error(['ALIS', 'INVALID-'])
        expected_raise_error(['ALIS', 'INVA--LID'])
        expected_raise_error(['ALIS', 'INVA  LID'])

        # ハイフン以外の半角記号
        targets = '!"#$%&\'()*+,./:;<=>?@[\\]^_`{|}~'

        for target in targets:
            expected_raise_error(['ALIS', 'INV{target}ALID'.format(target=target)])

    def test_get_tags_with_name_collation(self):
        TagUtil.create_tag(self.elasticsearch, "aaa aaa")
        TagUtil.create_tag(self.elasticsearch, "aaa")
        TagUtil.create_tag(self.elasticsearch, "aaa ccc")
        TagUtil.create_tag(self.elasticsearch, "BbB")
        TagUtil.create_tag(self.elasticsearch, "CCC")

        self.elasticsearch.indices.refresh(index="tags")

        tag_names = ['AAA', 'BBB', 'CCC', 'DDD']
        result = TagUtil.get_tags_with_name_collation(self.elasticsearch, tag_names)

        self.assertEquals(result, ['aaa', 'BbB', 'CCC', 'DDD'])

    def test_get_tags_with_name_collation_with_none(self):
        TagUtil.create_tag(self.elasticsearch, "aaa")
        TagUtil.create_tag(self.elasticsearch, "BbB")
        TagUtil.create_tag(self.elasticsearch, "CCC")

        self.elasticsearch.indices.refresh(index="tags")

        tag_names = None
        result = TagUtil.get_tags_with_name_collation(self.elasticsearch, tag_names)

        self.assertIsNone(result)
