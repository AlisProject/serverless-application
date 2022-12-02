import json
import os
import nft_games_info
from freezegun import freeze_time
from tests_util import TestsUtil
from unittest import TestCase
from topics_game_nft_games_show import TopicsGameNftGamesShow
from elasticsearch import Elasticsearch


class TestNftGamesShow(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()
    elasticsearch = Elasticsearch(
        hosts=[{'host': 'localhost'}]
    )
    temp_games_info = None
    test_key = '2022-10-31#nft_games'

    @classmethod
    def setUpClass(cls):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)
        cls.temp_games_info = nft_games_info.NFT_GAMES_INFO

        evaluated_item = [{
            'type': 'nft_games',
            'last_update_key': cls.test_key
        }]
        TestsUtil.create_table(cls.dynamodb, os.environ['ARTICLE_EVALUATED_MANAGE_TABLE_NAME'], evaluated_item)
        acquisition_items = [{
            'key': cls.test_key,
            'sort_key': 'key1',
            'rank_value': 1,
            'active_users_today': 1,
            'active_users_7days': 7,
            'active_users_30days': 30,
            'total_users': 100,
            'active_users_detail_30days': {'2022-10-31': 1, '2022-10-30': 2},
            'chains': ['chain']
        }]
        TestsUtil.create_table(cls.dynamodb, os.environ['ACQUISITION_INFO_TABLE_NAME'], acquisition_items)

    def setUp(self):
        # 定数 NFT_GAMES_INFO にテスト用データを設定
        test_games_info = {}
        for i in range(1, 3):
            test_games_info[f'key{i}'] = {
                'name': f'name{i}',
                'tag_name': f't{i}',
                'description': f'desc{i}',
                'twitter': f'twitter{i}',
                'telegramUrl': f'tel{i}',
                'discord': f'disc{i}',
                'officialPageUrl': f'url{i}'
            }
        nft_games_info.NFT_GAMES_INFO = test_games_info
        # ESにテスト用データを設定
        es_items = [
            {
                'article_id': 'test1',
                'created_at': 1667347200,
                'title': 'abc1',
                'published_at': 1667347200,
                'sort_key': 1667347200000000,
                'body': 'huga test',
                'tags': ['t1', 't2', 't3']
            },
            {
                'article_id': 'test2',
                'created_at': 1667347220,
                'title': 'abc2',
                'published_at': 1667347200,
                'sort_key': 1667347220000000,
                'body': 'foo bar',
                'tags': ['t1', 't2']
            },
            {
                'article_id': 'test3',
                'created_at': 1667347230,
                'title': 'abc3',
                'published_at': 1667347200,
                'sort_key': 1667347230000000,
                'body': 'foo bar',
                'tags': ['t1']
            }
        ]
        for item in es_items:
            self.elasticsearch.index(
                index="articles",
                doc_type="article",
                id=item["article_id"],
                body=item
            )
        self.elasticsearch.indices.refresh(index="articles")

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)
        nft_games_info.NFT_GAMES_INFO = cls.temp_games_info

    def tearDown(self):
        self.elasticsearch.indices.delete(index="articles", ignore=[404])

    @freeze_time('2022-11-02 00:00:00')
    def test_main_ok(self):
        params = {
            'queryStringParameters': {
                'tag': 't1'
            }
        }
        response = TopicsGameNftGamesShow(params, {}, dynamodb=self.dynamodb, elasticsearch=self.elasticsearch).main()
        actual = json.loads(response['body'])
        self.assertEqual(response['statusCode'], 200)
        expected = {
            'active_users_30days': 30,
            'active_users_7days': 7,
            'active_users_today': 1,
            'active_users_detail_30days': {'2022-10-30': 2, '2022-10-31': 1},
            'chains': ['chain'],
            'description': 'desc1',
            'discord': 'disc1',
            'key': 'key1',
            'name': 'name1',
            'officialPageUrl': 'url1',
            'tag_count': 3,
            'tag_name': 't1',
            'telegramUrl': 'tel1',
            'total_users': 100,
            'twitter': 'twitter1'
        }
        self.assertEqual(200, response['statusCode'])
        self.assertEqual(expected, actual)

    @freeze_time('2022-11-02 00:00:00')
    def test_main_ok_not_exists_evaluated_at(self):
        article_evaluated_manage_table = self.dynamodb.Table(os.environ['ARTICLE_EVALUATED_MANAGE_TABLE_NAME'])
        article_evaluated_manage_table.delete_item(Key={'type': 'nft_games'})
        params = {
            'queryStringParameters': {
                'tag': 't1'
            }
        }
        response = TopicsGameNftGamesShow(params, {}, dynamodb=self.dynamodb, elasticsearch=self.elasticsearch).main()
        actual = json.loads(response['body'])
        self.assertEqual(response['statusCode'], 200)
        # DBに紐づくデータが存在しないため、紐づくデータが含まれない
        expected = {
            'description': 'desc1',
            'discord': 'disc1',
            'key': 'key1',
            'name': 'name1',
            'officialPageUrl': 'url1',
            'tag_count': 3,
            'tag_name': 't1',
            'telegramUrl': 'tel1',
            'twitter': 'twitter1'
        }
        self.assertEqual(200, response['statusCode'])
        self.assertEqual(expected, actual)

    @freeze_time('2022-11-02 00:00:00')
    def test_main_ok_not_exists_db(self):
        params = {
            'queryStringParameters': {
                'tag': 't2'
            }
        }
        response = TopicsGameNftGamesShow(params, {}, dynamodb=self.dynamodb, elasticsearch=self.elasticsearch).main()
        actual = json.loads(response['body'])
        self.assertEqual(response['statusCode'], 200)
        # DBに紐づくデータが存在しないため、紐づくデータが含まれない
        expected = {
            'description': 'desc2',
            'discord': 'disc2',
            'key': 'key2',
            'name': 'name2',
            'officialPageUrl': 'url2',
            'tag_count': 2,
            'tag_name': 't2',
            'telegramUrl': 'tel2',
            'twitter': 'twitter2'
        }
        self.assertEqual(200, response['statusCode'])
        self.assertEqual(expected, actual)

    @freeze_time('2022-11-02 00:00:00')
    def test_main_ok_not_exists_target_tag(self):
        params = {
            'queryStringParameters': {
                'tag': 't3'
            }
        }
        response = TopicsGameNftGamesShow(params, {}, dynamodb=self.dynamodb, elasticsearch=self.elasticsearch).main()
        actual = json.loads(response['body'])
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual({}, actual)

    def test_main_ng_no_params(self):
        params = {
            'queryStringParameters': {}
        }
        response = TopicsGameNftGamesShow(params, {}, dynamodb=self.dynamodb, elasticsearch=self.elasticsearch).main()
        self.assertEqual(response['statusCode'], 400)

    def test_invalid_key_params(self):
        params = {
            'queryStringParameters': {
                'tag': ''
            }
        }
        response = TopicsGameNftGamesShow(params, {}, dynamodb=self.dynamodb, elasticsearch=self.elasticsearch).main()
        self.assertEqual(response['statusCode'], 400)

        params = {
            'queryStringParameters': {
                'tag': 'a' * 26
            }
        }
        response = TopicsGameNftGamesShow(params, {}, dynamodb=self.dynamodb, elasticsearch=self.elasticsearch).main()
        self.assertEqual(response['statusCode'], 400)
