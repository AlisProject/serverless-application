import json

from jsonschema import validate

import settings
from decimal_encoder import DecimalEncoder
from es_util import ESUtil
from lambda_base import LambdaBase


class SearchTagsCount(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'tags': settings.parameters['tags_count']
            },
            'required': ['tags']
        }

    def validate_params(self):
        validate(self.params, self.get_schema())

    def exec_main_proc(self):
        # 直近１週間分のタグを集計
        search_size = len(self.params['tags']) * settings.parameters['tags']['maxItems']
        from_time = 86400 * 7
        search_result = ESUtil.search_tags_count(self.elasticsearch, search_size, from_time)

        # 集計結果より指定タグの件数を取得
        temp = []
        for tag in self.params['tags']:
            tag_count = [d['doc_count'] for d in search_result if d['key'] == tag]
            temp.append({
                'tag': tag,
                'count': tag_count[0] if len(tag_count) > 0 else 0
            })
        result = sorted(temp, key=lambda x: x['count'], reverse=True)
        return {
            'statusCode': 200,
            'body': json.dumps(result, cls=DecimalEncoder)
        }
