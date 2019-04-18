import os

import settings
from boto3.dynamodb.conditions import Key
from jsonschema import ValidationError
from record_not_found_error import RecordNotFoundError
from not_authorized_error import NotAuthorizedError


class DBUtil:

    @staticmethod
    def exists_article(dynamodb, article_id, user_id=None, status=None):
        article_info_table = dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        article_info = article_info_table.get_item(Key={'article_id': article_id}).get('Item')

        if article_info is None:
            return False
        if user_id is not None and article_info['user_id'] != user_id:
            return False
        if status is not None and article_info['status'] != status:
            return False
        return True

    @classmethod
    def validate_article_existence(cls, dynamodb, article_id, user_id=None, status=None, version=None,
                                   is_purchased=None):
        article_info_table = dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        article_info = article_info_table.get_item(Key={'article_id': article_id}).get('Item')

        if article_info is None:
            raise RecordNotFoundError('Record Not Found')
        if user_id is not None and article_info['user_id'] != user_id:
            raise NotAuthorizedError('Forbidden')
        if status is not None and article_info['status'] != status:
            raise RecordNotFoundError('Record Not Found')
        if version is not None and not cls.__validate_version(article_info, version):
            raise RecordNotFoundError('Record Not Found')
        if is_purchased is not None and 'price' not in article_info:
            raise RecordNotFoundError('Record Not Found')

        return True

    @classmethod
    def __validate_version(cls, article_info, version):
        # version が 1 の場合は設定されていないことを確認
        if version == 1:
            if article_info.get('version') is None:
                return True
        # version 2 以降の場合は直接値を比較する
        elif article_info.get('version') == version:
            return True

        return False

    @staticmethod
    def validate_user_existence(dynamodb, user_id):
        users_table = dynamodb.Table(os.environ['USERS_TABLE_NAME'])
        user = users_table.get_item(Key={'user_id': user_id}).get('Item')

        if user is None:
            raise RecordNotFoundError('Record Not Found')
        return True

    @staticmethod
    def comment_existence(dynamodb, comment_id):
        table = dynamodb.Table(os.environ['COMMENT_TABLE_NAME'])
        comment = table.get_item(Key={'comment_id': comment_id}).get('Item')

        if comment is None:
            return False
        return True

    @staticmethod
    def validate_comment_existence(dynamodb, comment_id):
        table = dynamodb.Table(os.environ['COMMENT_TABLE_NAME'])
        comment = table.get_item(Key={'comment_id': comment_id}).get('Item')

        if comment is None:
            raise RecordNotFoundError('Record Not Found')
        return True

    @staticmethod
    def validate_parent_comment_existence(dynamodb, comment_id):
        table = dynamodb.Table(os.environ['COMMENT_TABLE_NAME'])
        comment = table.get_item(Key={'comment_id': comment_id}).get('Item')

        if comment is None or comment.get('parent_id'):
            raise RecordNotFoundError('Record Not Found')
        return True

    @staticmethod
    def get_validated_comment(dynamodb, comment_id):
        table = dynamodb.Table(os.environ['COMMENT_TABLE_NAME'])
        comment = table.get_item(Key={'comment_id': comment_id}).get('Item')

        if comment is None:
            raise RecordNotFoundError('Record Not Found')
        return comment

    @staticmethod
    def items_values_empty_to_none(values):
        for k, v in values.items():
            if v == '':
                values[k] = None

    @staticmethod
    def query_all_items(dynamodb_table, query_params):

        response = dynamodb_table.query(**query_params)
        items = response['Items']

        while 'LastEvaluatedKey' in response:
            query_params.update({'ExclusiveStartKey': response['LastEvaluatedKey']})
            response = dynamodb_table.query(**query_params)
            items.extend(response['Items'])

        return items

    @staticmethod
    def validate_topic(dynamodb, topic_name):
        topic_table = dynamodb.Table(os.environ['TOPIC_TABLE_NAME'])

        query_params = {
            'IndexName': 'index_hash_key-order-index',
            'KeyConditionExpression': Key('index_hash_key').eq(settings.TOPIC_INDEX_HASH_KEY)
        }

        topics = topic_table.query(**query_params)['Items']

        if topic_name not in [topic['name'] for topic in topics]:
            raise ValidationError('Bad Request: Invalid topic')
        return True

    @staticmethod
    def validate_user_existence_in_thread(dynamodb, replyed_user_id, parent_comment_id):

        comment_table = dynamodb.Table(os.environ['COMMENT_TABLE_NAME'])

        query_params = {
            'IndexName': 'parent_id-sort_key-index',
            'KeyConditionExpression': Key('parent_id').eq(parent_comment_id)
        }

        thread_comments = comment_table.query(**query_params)['Items']
        thread_user_ids = [comment['user_id'] for comment in thread_comments]
        parent_comment = comment_table.get_item(Key={'comment_id': parent_comment_id})['Item']

        if replyed_user_id not in thread_user_ids + [parent_comment['user_id']]:
            raise ValidationError("Bad Request: {replyed_user_id} doesn't exist in thread"
                                  .format(replyed_user_id=replyed_user_id))

        return True
