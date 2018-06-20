# -*- coding: utf-8 -*-


class ESUtil:

    @staticmethod
    def post_article(elasticsearch, article_info, article_content):
        id = article_info['article_id']
        body = article_info
        body.update(article_content)
        elasticsearch.index(
            index="articles",
            doc_type="article",
            id=id,
            body=body
        )

    @staticmethod
    def delete_article(elasticsearch, article_id):
        elasticsearch.delete(
            index="articles",
            doc_type="article",
            id=article_id,
            ignore=[404]
        )

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
                {
                    "published_at": "desc"
                }
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
                    "must": [
                    ]
                }
            },
            "from": limit*(page-1),
            "size": limit
        }
        for s in word.split():
            query = {
                "bool": {
                    "should": [
                        {
                            "match": {
                                "user_id": s
                            }
                        },
                        {
                            "match": {
                                "user_display_name": s
                            }
                        },
                        {
                            "match": {
                                "self_introduction": s
                            }
                        }
                    ]
                }
            }
            body["query"]["bool"]["must"].append(query)
        res = elasticsearch.search(
                index="users",
                body=body
        )
        return res

    @staticmethod
    def post_user(elasticsearch, user):
        id = user['user_id']
        elasticsearch.index(
            index="users",
            doc_type="user",
            id=id,
            body=user
        )
