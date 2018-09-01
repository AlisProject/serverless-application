import re
import time

import settings
from jsonschema import ValidationError


class TagUtil:
    @classmethod
    def create_and_count(cls, elasticsearch, before_tag_names, after_tag_names):
        if before_tag_names is None:
            before_tag_names = []

        if after_tag_names is None:
            after_tag_names = []

        for tag_name in after_tag_names:
            if before_tag_names is None or tag_name not in before_tag_names:

                # 大文字小文字区別せずに存在チェックを行いDB(ES)にすでに存在する値を取得する
                tag = cls.__get_item_case_insensitive(elasticsearch, tag_name)

                if tag:
                    # タグが追加された場合カウントを+1する
                    cls.update_count(elasticsearch, tag['name'], 1)
                # タグがDB(ES)に存在しない場合は新規作成する
                else:
                    cls.create_tag(elasticsearch, tag_name)

        # タグが外された場合カウントを-1する
        for tag_name in before_tag_names:
            if tag_name not in after_tag_names:
                tag = cls.__get_item_case_insensitive(elasticsearch, tag_name)
                if tag:
                    cls.update_count(elasticsearch, tag['name'], -1)

    @classmethod
    def update_count(cls, elasticsearch, tag_name, num):
        update_script = {
            'script': {
                'source': 'ctx._source.count += params.count',
                'lang': 'painless',
                'params': {
                    'count': num
                }
            }
        }

        elasticsearch.update(index='tags', doc_type='tag', id=tag_name, body=update_script)

    @classmethod
    def create_tag(cls, elasticsearch, tag_name):
        tag = {
            'name': tag_name,
            'count': 1,
            'created_at': int(time.time())
        }

        elasticsearch.index(
            index='tags',
            doc_type='tag',
            id=tag['name'],
            body=tag
        )

        # デフォルトのrefresh_intervalだと、1sほど作成されたタグが検索対象にならないのでセグメントマージを強制的に行う
        elasticsearch.indices.refresh(index='tags')

    """
    与えられたタグ名をElasticSearchに問い合わせ(大文字小文字区別せず)
    すでに存在する場合はElasticSearchに存在する文字列に完全一致する形に変換し、タグ名の配列を返却する
    """
    @classmethod
    def get_tags_with_name_collation(cls, elasticsearch, tag_names):
        if not tag_names:
            return tag_names

        results = []

        for tag_name in tag_names:
            tag = cls.__get_item_case_insensitive(elasticsearch, tag_name)

            if tag:
                results.append(tag['name'])
            else:
                results.append(tag_name)

        return results

    @staticmethod
    def validate_format(tags):
        pattern = re.compile(settings.TAG_DENIED_SYMBOL_PATTERN)

        for tag in tags:
            result = pattern.search(tag)

            if result:
                raise ValidationError("tags don't support {str}".format(str=result.group()))

            for symbol in settings.TAG_ALLOWED_SYMBOLS:
                if tag[0] == symbol or tag[-1] == symbol:
                    raise ValidationError("tags don't support {str} with start and end of character".format(str=symbol))

    @classmethod
    def __get_item_case_insensitive(cls, elasticsearch, tag_name):
        body = {
            'query': {
                'bool': {
                    'must': [
                        {'match': {'name': tag_name}}
                    ]
                }
            }
        }

        res = elasticsearch.search(
            index='tags',
            doc_type='tag',
            body=body
        )

        tags = [item['_source'] for item in res['hits']['hits']]

        if not tags:
            return None

        return tags[0]
