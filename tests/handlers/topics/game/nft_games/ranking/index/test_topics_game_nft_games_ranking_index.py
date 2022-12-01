import json
import os
import nft_games_info
from freezegun import freeze_time
from tests_util import TestsUtil
from unittest import TestCase
from topics_game_nft_games_ranking_index import TopicsGameNftGamesRankingIndex
from elasticsearch import Elasticsearch


class TestNftGamesRankingIndex(TestCase):
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
        acquisition_items = []
        for i in range(1, 7):
            if i == 5:
                continue
            acquisition_items.append({
                'key': cls.test_key,
                'sort_key': 'key' + str(i),
                'rank_value': i,
                'active_users_today': i,
                'active_users_7days': i * 7,
                'active_users_30days': i * 30,
                'total_users': i * 100,
                'active_users_detail_30days': {'test'},
                'chains': ['chain' + str(i)]
            })
        TestsUtil.create_table(cls.dynamodb, os.environ['ACQUISITION_INFO_TABLE_NAME'], acquisition_items)

    def setUp(self):
        # 定数 NFT_GAMES_INFO にテスト用データを設定
        test_games_info = {}
        for i in range(1, 7):
            test_games_info[f'key{i}'] = {
                'name': f'name{i}',
                'tag_name': f't{i}',
                'description': f'desc{i}',
                'twitter': f'twitter{i}',
                'telegramUrl': f'tel{i}',
                'discord': f'disc{i}',
                'officialPageUrl': f'url{i}'
            }
            # tag_name が存在しない場合
            if i == 6:
                del test_games_info[f'key{i}']['tag_name']
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
            },
            {
                'article_id': 'test4',
                'created_at': 1667347240,
                'title': 'abc4',
                'published_at': 1667347200,
                'sort_key': 1667347200000000,
                'body': 'foo bar',
                'tags': ['t4', 'test']
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
        response = TopicsGameNftGamesRankingIndex({}, {}, dynamodb=self.dynamodb, elasticsearch=self.elasticsearch).main()
        actual = json.loads(response['body'])
        self.assertEqual(response['statusCode'], 200)
        # key5: DBに紐づくデータが存在しないため、紐づくデータが含まれない
        # key6: tag_name が存在しないため対象外
        expected = [
            {"key": "key1", "name": "name1", "tag_count": 3, "tag_name": "t1", "active_users_today": 1,
             "active_users_7days": 7, "active_users_30days": 30, "total_users": 100, "chains": ["chain1"]},
            {"key": "key2", "name": "name2", "tag_count": 2, "tag_name": "t2", "active_users_today": 2,
             "active_users_7days": 14, "active_users_30days": 60, "total_users": 200, "chains": ["chain2"]},
            {"key": "key3", "name": "name3", "tag_count": 1, "tag_name": "t3", "active_users_today": 3,
             "active_users_7days": 21, "active_users_30days": 90, "total_users": 300, "chains": ["chain3"]},
            {"key": "key4", "name": "name4", "tag_count": 1, "tag_name": "t4", "active_users_today": 4,
             "active_users_7days": 28, "active_users_30days": 120, "total_users": 400, "chains": ["chain4"]},
            {"key": "key5", "name": "name5", "tag_count": 0, "tag_name": "t5"}
        ]
        self.assertEqual(200, response['statusCode'])
        self.assertEqual(expected, actual)

    @freeze_time('2022-11-02 00:00:00')
    def test_main_ok_not_exists_evaluated_at(self):
        article_evaluated_manage_table = self.dynamodb.Table(os.environ['ARTICLE_EVALUATED_MANAGE_TABLE_NAME'])
        article_evaluated_manage_table.delete_item(Key={'type': 'nft_games'})
        response = TopicsGameNftGamesRankingIndex({}, {}, dynamodb=self.dynamodb, elasticsearch=self.elasticsearch).main()
        actual = json.loads(response['body'])
        self.assertEqual(response['statusCode'], 200)
        # key5: DBに紐づくデータが存在しないため、紐づくデータが含まれない
        # key6: tag_name が存在しないため対象外
        expected = [
            {'key': 'key1', 'name': 'name1', 'tag_count': 3, 'tag_name': 't1'},
            {'key': 'key2', 'name': 'name2', 'tag_count': 2, 'tag_name': 't2'},
            {'key': 'key3', 'name': 'name3', 'tag_count': 1, 'tag_name': 't3'},
            {'key': 'key4', 'name': 'name4', 'tag_count': 1, 'tag_name': 't4'},
            {'key': 'key5', 'name': 'name5', 'tag_count': 0, 'tag_name': 't5'}
        ]
        self.assertEqual(200, response['statusCode'])
        self.assertEqual(expected, actual)
