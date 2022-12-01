import os
import json
import nft_games_info
import settings
from boto3.dynamodb.conditions import Key
from decimal_encoder import DecimalEncoder
from es_util import ESUtil
from db_util import DBUtil
from lambda_base import LambdaBase


class TopicsGameNftGamesRankingIndex(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        # 該当ゲームのタグ数をESより取得
        # タグ一覧を取得
        tags = [i.get('tag_name') for i in nft_games_info.NFT_GAMES_INFO.values() if i.get('tag_name') is not None]
        search_size = len(tags) * settings.parameters['tags']['maxItems']
        from_time = 86400 * settings.NFT_GAME_TAG_SEARCH_DAYS
        search_result = ESUtil.search_tags_count(self.elasticsearch, tags, search_size, from_time)
        # 集計結果より指定タグの件数を設定
        temp = {}
        for k, v in nft_games_info.NFT_GAMES_INFO.items():
            if v.get('tag_name') is None:
                continue
            temp[k] = {'key': k, 'name': v['name'], 'tag_count': 0}
            tag_count = [d['doc_count'] for d in search_result if d['key'] == v.get('tag_name')]
            temp[k].update({
                'tag_name': v.get('tag_name'),
                'tag_count': tag_count[0] if len(tag_count) > 0 else 0
            })

        # BCデータを設定
        article_evaluated_manage_table = self.dynamodb.Table(os.environ['ARTICLE_EVALUATED_MANAGE_TABLE_NAME'])
        acquisition_info_table = self.dynamodb.Table(os.environ['ACQUISITION_INFO_TABLE_NAME'])
        article_evaluated_manage = article_evaluated_manage_table.get_item(Key={'type': 'nft_games'}).get('Item')
        if article_evaluated_manage is not None:
            query_params = {
                'KeyConditionExpression': Key('key').eq(article_evaluated_manage['last_update_key'])
            }
            acquisition_info = DBUtil.query_all_items(acquisition_info_table, query_params)
            for bc_info in acquisition_info:
                if temp.get(bc_info['sort_key']) is not None:
                    temp[bc_info['sort_key']].update({
                        'active_users_today': bc_info['active_users_today'],
                        'active_users_7days': bc_info['active_users_7days'],
                        'active_users_30days': bc_info['active_users_30days'],
                        'total_users': bc_info['total_users'],
                        'chains': bc_info['chains']
                    })

        # 記事数順で返却
        result = sorted(list(temp.values()), key=lambda x: x.get('tag_count'), reverse=True)
        return {
            'statusCode': 200,
            'body': json.dumps(result, cls=DecimalEncoder)
        }
