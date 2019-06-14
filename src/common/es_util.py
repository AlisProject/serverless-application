# -*- coding: utf-8 -*-
import settings


class ESUtil:

    @staticmethod
    def search_tag(elasticsearch, word, limit, page):
        body = {
            'query': {
                'bool': {
                    'must': [
                        {
                            'match': {
                                'name_with_analyzer': {
                                    'query': word.lower(),
                                    'analyzer': 'keyword'
                                }
                            }
                        }
                    ]
                }
            },
            'sort': [
                {'count': 'desc'}
            ],
            'from': limit * (page - 1),
            'size': limit
        }

        response = elasticsearch.search(
            index='tags',
            body=body
        )

        tags = [item['_source'] for item in response['hits']['hits']]

        return tags

    @staticmethod
    def search_article(elasticsearch, limit, page, word=None, tag=None):
        body = {
            "query": {
                "bool": {
                    "must": [
                    ]
                }
            },
            "sort": [
                {"sort_key": "desc"}
            ],
            "from": limit*(page-1),
            "size": limit
        }

        # wordが渡ってきた場合は文字列検索をする
        if word:
            for s in word.split():
                query = {
                    "bool": {
                        "should": [
                            {
                                "match": {
                                    "title": s
                                }
                            },
                            {
                                "match": {
                                    "body": s
                                }
                            }
                        ]
                    }
                }
                body["query"]["bool"]["must"].append(query)

                # 文字列による検索の場合は検索スコアを第一ソートとする
                body['sort'].insert(0, {'_score': 'desc'})

        # tagが渡ってきたときはそのタグで一致検索を行う
        # TODO: 大文字小文字区別なしで検索を行えること
        if tag:
            body['query']['bool']['must'].append({'term': {'tags.keyword': tag}})

        res = elasticsearch.search(
                index="articles",
                body=body
        )
        return res

    @staticmethod
    def search_random_article(elasticsearch):
        query = {
            "function_score": {
                "query": {
                    "match_all": {}
                },
                "random_score": {},
            }
        }

        body = {
            "query": query,
            "size": 1
        }

        res = elasticsearch.search(
            index="articles",
            body=body
        )
        return res

    @staticmethod
    def search_user(elasticsearch, word, limit, page):
        body = {
            "query": {
                "wildcard": {
                    "search_name": f"*{word}*"
                }
            },
            "from": limit*(page-1),
            "size": limit
        }
        res = elasticsearch.search(
                index="users",
                body=body
        )
        return res

    @staticmethod
    def search_popular_articles(elasticsearch, params, limit, page):
        if not elasticsearch.indices.exists(index='article_scores'):
            return []

        body = {
            'query': {
                'bool': {
                    'must': [
                    ]
                }
            },
            'sort': [
                {'article_score': 'desc'}
            ],
            'from': limit * (page - 1),
            'size': limit
        }

        if params.get('topic'):
            body['query']['bool']['must'].append({'match': {'topic': params.get('topic')}})

        response = elasticsearch.search(
            index='article_scores',
            body=body
        )

        articles = [item['_source'] for item in response['hits']['hits']]

        return articles

    @staticmethod
    def search_tip_ranked_articles(elasticsearch, params, limit, page):
        if not elasticsearch.indices.exists(index=settings.ARTICLE_TIP_RANKING_INDEX_NAME):
            return []

        body = {
            'query': {
                'bool': {
                    'must': [
                    ]
                }
            },
            'sort': [
                {'sort_tip_value': 'desc'}
            ],
            'from': limit * (page - 1),
            'size': limit
        }

        if params.get('topic'):
            body['query']['bool']['must'].append({'match': {'topic': params.get('topic')}})

        response = elasticsearch.search(
            index=settings.ARTICLE_TIP_RANKING_INDEX_NAME,
            body=body
        )

        articles = [item['_source'] for item in response['hits']['hits']]

        return articles

    @staticmethod
    def search_recent_articles(elasticsearch, params, limit, page):
        body = {
            'query': {
                'bool': {
                    'must': []
                }
            },
            'sort': [
                {'sort_key': 'desc'}
            ],
            'from': limit * (page - 1),
            'size': limit
        }

        if params.get('topic'):
            body['query']['bool']['must'].append({'match': {'topic': params.get('topic')}})

        res = elasticsearch.search(
            index='articles',
            doc_type='article',
            body=body
        )
        articles = [item['_source'] for item in res['hits']['hits']]

        return articles
