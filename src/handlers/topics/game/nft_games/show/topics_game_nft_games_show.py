import os
import json
import nft_games_info
import settings
import copy
from jsonschema import validate
from decimal_encoder import DecimalEncoder
from es_util import ESUtil
from lambda_base import LambdaBase


class TopicsGameNftGamesShow(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'tag': settings.parameters['tag'],
            },
            'required': ['tag']
        }

    def validate_params(self):
        validate(self.params, self.get_schema())

    def exec_main_proc(self):
        # 該当タグに紐づくゲーム情報が存在しない場合は空を返却
        target_key = [k for k in nft_games_info.NFT_GAMES_INFO.keys() if
                      nft_games_info.NFT_GAMES_INFO[k].get('tag_name') == self.params['tag']]
        if len(target_key) != 1:
            return {
                'statusCode': 200,
                'body': '{}'
            }

        # 該当ゲームのタグ数をESより取得
        # タグ一覧を取得
        game_info = copy.deepcopy(nft_games_info.NFT_GAMES_INFO[target_key[0]])
        game_info['key'] = target_key[0]
        if game_info.get('tag_name') is not None:
            search_size = settings.parameters['tags']['maxItems']
            from_time = 86400 * settings.NFT_GAME_TAG_SEARCH_DAYS
            search_result = ESUtil.search_tags_count(self.elasticsearch, [game_info['tag_name']], search_size, from_time)
            # 集計結果より指定タグの件数を設定
            tag_count = [d['doc_count'] for d in search_result if d['key'] == game_info.get('tag_name')]
            game_info.update({
                'tag_count': tag_count[0] if len(tag_count) > 0 else 0
            })

        # BCデータを設定
        article_evaluated_manage_table = self.dynamodb.Table(os.environ['ARTICLE_EVALUATED_MANAGE_TABLE_NAME'])
        acquisition_info_table = self.dynamodb.Table(os.environ['ACQUISITION_INFO_TABLE_NAME'])
        article_evaluated_manage = article_evaluated_manage_table.get_item(Key={'type': 'nft_games'}).get('Item')
        if article_evaluated_manage is not None:
            acquisition_info = acquisition_info_table.get_item(
                Key={'key': article_evaluated_manage['last_update_key'], 'sort_key': game_info['key']}
            ).get('Item')
            if acquisition_info is not None:
                game_info.update({
                    'active_users_today': acquisition_info['active_users_today'],
                    'active_users_7days': acquisition_info['active_users_7days'],
                    'active_users_30days': acquisition_info['active_users_30days'],
                    'total_users': acquisition_info['total_users'],
                    'active_users_detail_30days': acquisition_info['active_users_detail_30days'],
                    'chains': acquisition_info['chains']
                })

        # 取得結果を返却
        return {
            'statusCode': 200,
            'body': json.dumps(game_info, cls=DecimalEncoder)
        }
