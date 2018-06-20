# -*- coding: utf-8 -*-


class ESUtil:

    @staticmethod
    def post_article(elasticsearch, article_info, article_content):
        id = article_info['Item']['article_id']
        body = article_info['Item']
        body.update(article_content['Item'])
        elasticsearch.index(
            index="articles",
            doc_type="article",
            id=id,
            body=body
        )

    @staticmethod
    def update_article(elasticsearch, article_content_edit):
        id = article_content_edit['article_id']
        elasticsearch.update(
            index="articles",
            doc_type="article",
            id=id,
            body={
                "doc": article_content_edit
            },
            ignore=[404]
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
    def search_article(elasticsearch, search_word):
        body = {
            "query": {
                "bool": {
                    "must": [
                    ]
                }
            }
        }
        for s in search_word.split():
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
