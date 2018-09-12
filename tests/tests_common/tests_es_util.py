import os
import time

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

    @staticmethod
    def create_tag_index(elasticsearch):
        tag_settings = {
            'settings': {
                'analysis': {
                    'normalizer': {
                        'lowercase_normalizer': {
                            'type': 'custom',
                            'char_filter': [],
                            'filter': ['lowercase']
                        }
                    },
                    'filter': {
                        'autocomplete_filter': {
                            'type': 'edge_ngram',
                            'min_gram': 1,
                            'max_gram': 20
                        }
                    },
                    'analyzer': {
                        'autocomplete': {
                            'type': 'custom',
                            'tokenizer': 'keyword',
                            'filter': [
                                'lowercase',
                                'autocomplete_filter'
                            ]
                        }
                    }
                }
            },
            'mappings': {
                'tag': {
                    'properties': {
                        'name': {
                            'type': 'keyword',
                            'normalizer': 'lowercase_normalizer'
                        },
                        'name_with_analyzer': {
                            'type': 'text',
                            'analyzer': 'autocomplete'
                        },
                        'created_at': {
                            'type': 'integer'
                        }
                    }
                }
            }
        }
        elasticsearch.indices.create(index='tags', body=tag_settings)
        elasticsearch.indices.refresh(index='tags')

    @staticmethod
    def create_tag_with_count(elasticsearch, tag_name, count):
        tag = {
            'name': tag_name,
            'name_with_analyzer': tag_name,
            'count': count,
            'created_at': int(time.time())
        }

        elasticsearch.index(
            index='tags',
            doc_type='tag',
            id=tag['name'],
            body=tag
        )

        elasticsearch.indices.refresh(index='tags')

    @staticmethod
    def get_all_tags(elasticsearch):
        res = elasticsearch.search(
            index='tags',
            doc_type='tag',
            body={}
        )

        tags = [item['_source'] for item in res['hits']['hits']]

        return tags
