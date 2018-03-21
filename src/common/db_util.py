import os
from boto3.dynamodb.conditions import Key


class DBUtil:

    @staticmethod
    def exists_public_article(dynamodb, article_id):
        query_params = {
            'IndexName': 'article_id-status_key-index',
            'KeyConditionExpression': Key('status').eq('public') & Key('article_id').eq(article_id)
        }
        article_info_table = dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        return True if article_info_table.query(**query_params)['Count'] == 1 else False
