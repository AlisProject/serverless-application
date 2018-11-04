import json
import os
import time

from botocore.exceptions import ClientError
from jsonschema import validate, ValidationError

import settings
from db_util import DBUtil
from lambda_base import LambdaBase
from text_sanitizer import TextSanitizer
from user_util import UserUtil


class MeUsersFraudCreate(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'user_id': settings.parameters['user_id'],
                'reason': settings.parameters['fraud_user']['reason'],
                'free_text': settings.parameters['fraud_user']['free_text']
            },
            'required': ['user_id', 'reason']
        }

    def validate_params(self):
        UserUtil.verified_phone_and_email(self.event)

        validate(self.params, self.get_schema())

        self.__validate_reporting_myself()

        DBUtil.validate_user_existence(
            self.dynamodb,
            self.event['pathParameters']['user_id']
        )

    def exec_main_proc(self):
        try:
            article_user_fraud_table = self.dynamodb.Table(os.environ['USER_FRAUD_TABLE_NAME'])
            self.__create_user_fraud(article_user_fraud_table)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return {
                    'statusCode': 400,
                    'body': json.dumps({'message': 'Already exists'})
                }
            else:
                raise

        return {
            'statusCode': 200
        }

    def __create_user_fraud(self, article_user_fraud_table):
        user_fraud = {
            'target_user_id': self.event['pathParameters']['user_id'],
            'user_id': self.event['requestContext']['authorizer']['claims']['cognito:username'],
            'reason': self.params.get('reason'),
            'free_text': TextSanitizer.sanitize_text(self.params.get('free_text')),
            'created_at': int(time.time())
        }
        article_user_fraud_table.put_item(
            Item=user_fraud,
            ConditionExpression='attribute_not_exists(user_id)'
        )
        pass

    def __validate_reporting_myself(self):
        login_user = self.event['requestContext']['authorizer']['claims']['cognito:username']
        target_user = self.event['pathParameters']['user_id']

        if login_user == target_user:
            raise ValidationError('Can not report myself')
