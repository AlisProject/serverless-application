import os
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

    @staticmethod
    def validate_article_existence(dynamodb, article_id, user_id=None, status=None):
        article_info_table = dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        article_info = article_info_table.get_item(Key={'article_id': article_id}).get('Item')

        if article_info is None:
            raise RecordNotFoundError('Record Not Found')
        if user_id is not None and article_info['user_id'] != user_id:
            raise NotAuthorizedError('Forbidden')
        if status is not None and article_info['status'] != status:
            raise RecordNotFoundError('Record Not Found')
        return True

    @staticmethod
    def validate_user_existence(dynamodb, user_id):
        users_table = dynamodb.Table(os.environ['USERS_TABLE_NAME'])
        user = users_table.get_item(Key={'user_id': user_id}).get('Item')

        if user is None:
            raise RecordNotFoundError('Record Not Found')
        return True

    @staticmethod
    def items_values_empty_to_none(values):
        for k, v in values.items():
            if v == '':
                values[k] = None
