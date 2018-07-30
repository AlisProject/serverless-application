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
