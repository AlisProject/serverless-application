from unittest import TestCase

from elasticsearch import Elasticsearch
from tests_es_util import TestsEsUtil

from es_util import ESUtil


class TestDBUtil(TestCase):
    elasticsearch = Elasticsearch(
        hosts=[{'host': 'localhost'}]
    )

    def setUp(self):
        TestsEsUtil.create_tag_index(self.elasticsearch)

    def tearDown(self):
        self.elasticsearch.indices.delete(index="tags", ignore=[404])

    def test_search_tag(self):
        TestsEsUtil.create_tag_with_count(self.elasticsearch, 'ALIS', 5)
        TestsEsUtil.create_tag_with_count(self.elasticsearch, 'apple orange', 2)
        TestsEsUtil.create_tag_with_count(self.elasticsearch, 'beautiful Apple', 3)
        TestsEsUtil.create_tag_with_count(self.elasticsearch, '漢字 カタカナ', 1)
        TestsEsUtil.create_tag_with_count(self.elasticsearch, 'Application', 4)

        self.elasticsearch.indices.refresh(index="tags")

        self.__assert_search_tags('A', ['ALIS', 'Application', 'apple orange'])
        self.__assert_search_tags('漢', ['漢字 カタカナ'])
        self.__assert_search_tags('app', ['Application', 'apple orange'])
        self.__assert_search_tags('カタ', [])
        self.__assert_search_tags('apple ora', ['apple orange'])
        self.__assert_search_tags('ALIS on', [])

    def test_search_tag_with_limit(self):
        # 0~110のループを回す
        for x in range(0, 111):
            TestsEsUtil.create_tag_with_count(self.elasticsearch, 'A' + str(x), x)

        result = ESUtil.search_tag(self.elasticsearch, 'A')
        self.assertEquals(len(result), 100)

        result = ESUtil.search_tag(self.elasticsearch, 'A', limit=10)
        self.assertEquals(len(result), 10)

        result = ESUtil.search_tag(self.elasticsearch, 'A', limit=2, page=2)
        self.assertEquals(len(result), 2)
        self.assertEquals([tag['name'] for tag in result], ['A108', 'A107'])

    def __assert_search_tags(self, word, expected):
        result = ESUtil.search_tag(self.elasticsearch, word)
        tags = [tag['name'] for tag in result]
        self.assertEquals(tags, expected)
