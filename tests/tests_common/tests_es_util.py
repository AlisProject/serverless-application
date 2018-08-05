import os
from boto3.dynamodb.conditions import Key


class TestsEsUtil:
    @classmethod
    def delete_alias(cls, elastic_search, alias_name):
        if elastic_search.indices.exists_alias(alias_name):
            indices = elastic_search.indices.get_alias(alias_name)

            for index in indices:
                elastic_search.indices.delete_alias(index, alias_name)
                elastic_search.indices.delete(index)

    @staticmethod
    def create_articles_index(elasticsearch):
        TestsEsUtil.remove_articles_index(elasticsearch)

        article_settings = {
            'mappings': {
                'article': {
                    'properties': {
                        'sort_key': {
                            'type': 'long'
                        }
                    }
                }
            }
        }
        elasticsearch.indices.create(index='articles', body=article_settings)

    @staticmethod
    def remove_articles_index(elasticsearch):
        elasticsearch.indices.delete(index='articles', ignore=[404])

    @staticmethod
    def sync_public_articles_from_dynamodb(dynamodb, elasticsearch):
        table = dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        query_params = {
            'IndexName': 'status-sort_key-index',
            'KeyConditionExpression': Key('status').eq('public')
        }
        articles = table.query(**query_params)
        for article in articles['Items']:
            elasticsearch.index(
                index='articles',
                doc_type='article',
                id=article['article_id'],
                body=article
            )
        elasticsearch.indices.refresh(index='articles')
