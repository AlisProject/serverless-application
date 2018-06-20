# -*- coding: utf-8 -*-
import os
import time
import settings
from db_util import DBUtil
from lambda_base import LambdaBase
from jsonschema import validate
from text_sanitizer import TextSanitizer


class MeInfoUpdate(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'user_display_name': settings.parameters['user_display_name'],
                'self_introduction': settings.parameters['self_introduction']
            },
            'required': ['user_display_name', 'self_introduction']
        }

    def validate_params(self):
        # single
        validate(self.params, self.get_schema())
        # relation
        DBUtil.validate_user_existence(
            self.dynamodb,
            self.event['requestContext']['authorizer']['claims']['cognito:username']
        )

    def exec_main_proc(self):
        users_table = self.dynamodb.Table(os.environ['USERS_TABLE_NAME'])

        expression_attribute_values = {
            ':user_display_name': TextSanitizer.sanitize_text(self.params['user_display_name']),
            ':self_introduction': TextSanitizer.sanitize_text(self.params['self_introduction']),
            ':sync_elasticsearch': 0,
            ':updated_at': int(time.time())
        }
        DBUtil.items_values_empty_to_none(expression_attribute_values)

        users_table.update_item(
            Key={
                'user_id': self.event['requestContext']['authorizer']['claims']['cognito:username'],
            },
            UpdateExpression=("set user_display_name=:user_display_name, self_introduction=:self_introduction, "
                              "sync_elasticsearch=:sync_elasticsearch, updated_at=:updated_at"),
            ExpressionAttributeValues=expression_attribute_values
        )

        return {
            'statusCode': 200
        }
