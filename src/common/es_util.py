# -*- coding: utf-8 -*-


class ESUtil:

    @staticmethod
    def search_article(elasticsearch, word, limit, page):
        body = {
            "query": {
                "bool": {
                    "must": [
                    ]
                }
            },
            "sort": [
                "_score",
                {"published_at": "desc"}
            ],
            "from": limit*(page-1),
            "size": limit
        }
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
        res = elasticsearch.search(
                index="articles",
                body=body
        )
        return res

    @staticmethod
    def search_user(elasticsearch, word, limit, page):
        body = {
            "query": {
                "bool": {
                    "should": [
                        {"wildcard": {"user_id": f"*{word}*"}},
                        {"wildcard": {"user_display_name": f"*{word}*"}}
                    ]
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

        if params is not None and params:
            for name, value in params.items():
                query = {
                    'bool': {
                        'must': [
                            {
                                'match': {
                                    name: value
                                }
                            }
                        ]
                    }
                }
                body['query']['bool']['must'].append(query)

        res = elasticsearch.search(
            index='articles',
            doc_type='article',
            body=body
        )

        return res
