import json

from jsonschema import validate

import settings
from decimal_encoder import DecimalEncoder
from es_util import ESUtil
from lambda_base import LambdaBase
from parameter_util import ParameterUtil


class SearchTagsCount(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'tags': settings.parameters['tags_count'],
                'search_days': settings.parameters['tags_count_search_days']
            },
            'required': ['tags']
        }

    def validate_params(self):
        ParameterUtil.cast_parameter_to_int(self.params, self.get_schema())
        self.params['tags'] = self.event['multiValueQueryStringParameters'].get('tags')
        validate(self.params, self.get_schema())

    def exec_main_proc(self):
        # 直近１週間分のタグを集計
        search_size = len(self.params['tags']) * settings.parameters['tags']['maxItems']
        search_days = self.params.get('search_days') if self.params.get('search_days') else 7
        from_time = 86400 * search_days
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
