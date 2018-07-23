# -*- coding: utf-8 -*-
import os
import settings
import time

from db_util import DBUtil
from lambda_base import LambdaBase
from jsonschema import validate
from not_authorized_error import NotAuthorizedError


class MeCommentsDelete(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'comment_id': settings.parameters['comment']['comment_id']
            },
            'required': ['comment_id']
        }

    def validate_params(self):
        validate(self.params, self.get_schema())
        comment = DBUtil.get_validated_comment(self.dynamodb, self.params['comment_id'])
        DBUtil.validate_article_existence(self.dynamodb, comment['article_id'], status='public')

    def exec_main_proc(self):
        comment_table = self.dynamodb.Table(os.environ['COMMENT_TABLE_NAME'])
        comment = comment_table.get_item(
            Key={"comment_id": self.params['comment_id']}
        )['Item']

        if not self.__is_accessable_comment(comment):
            raise NotAuthorizedError('Forbidden')

        deleted_comment_table = self.dynamodb.Table(os.environ['DELETED_COMMENT_TABLE_NAME'])

        comment.update({"deleted_at": int(time.time())})
        deleted_comment_table.put_item(Item=comment)

        comment_table.delete_item(Key={"comment_id": self.params['comment_id']})

        return {'statusCode': 200}

    def __is_accessable_comment(self, comment):
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']

        article_info_table_name = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        article_info = article_info_table_name.get_item(Key={"article_id": comment['article_id']})['Item']

        if article_info['user_id'] == user_id or comment['user_id'] == user_id:
            return True

        return False
