import re
import time
import settings
from jsonschema import ValidationError
from web3_util import Web3Util


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
                if tag and tag['count'] > 0:
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

    """
    ここで作成されたtagが検索対象になるまで(__get_item_case_insensitiveの条件として引っかかってくるまで)1sほどかかる
    これはESのセグメントマージという仕様によるものでどうしても回避したい場合は `elasticsearch.indices.refresh(index='tags')` をcreate後に行う必要がある
    しかし、ESのデフォルト挙動を無理やり変えることになり、返ってパフォーマンス低下が起きる可能性もあるので特に何もしていない
    """
    @classmethod
    def create_tag(cls, elasticsearch, tag_name):
        tag = {
            'name': tag_name,
            'name_with_analyzer': tag_name,
            'count': 1,
            'created_at': int(time.time())
        }

        elasticsearch.index(
            index='tags',
            doc_type='tag',
            id=tag['name'],
            body=tag
        )

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
    def validate_tags(tags, user_id=None):
        pattern = re.compile(settings.TAG_DENIED_SYMBOL_PATTERN)

        for tag in tags:
            result = pattern.search(tag)

            if result:
                raise ValidationError("tags don't support {str}".format(str=result.group()))

            for symbol in settings.TAG_ALLOWED_SYMBOLS:
                if tag[0] == symbol or tag[-1] == symbol:
                    raise ValidationError("tags don't support {str} with start and end of character".format(str=symbol))

        # 対象バッジ取得者限定タグを利用していた場合、該当バッジを保持しているかを確認
        if settings.VIP_TAG_NAME in tags:
            user_types = Web3Util.get_badge_types(user_id)
            if len(set(settings.VIP_TAG_BADGE_TYPES) & set(user_types)) <= 0:
                raise ValidationError(f"Tag name {settings.VIP_TAG_NAME} is not available")

    @classmethod
    def __get_item_case_insensitive(cls, elasticsearch, tag_name):
        body = {
            'query': {
                'bool': {
                    'must': [
                        {'term': {'name': tag_name}}
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
