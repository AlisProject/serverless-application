# -*- coding: utf-8 -*-
import os
import settings
import time
import json
from db_util import DBUtil
from botocore.exceptions import ClientError
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError


class MeArticlesFraudCreate(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id'],
                'reason': {
                    'type': 'string',
                    'enum': settings.FRAUD_REASONS
                }
            },
            'required': ['article_id']
        }

    def validate_params(self):
        if not self.event.get('body'):
            raise ValidationError('Request parameter is required')

        validate(self.params, self.get_schema())
        # relation
        DBUtil.validate_article_existence(
            self.dynamodb,
            self.params['article_id'],
            status='public'
        )

    def exec_main_proc(self):
        try:
            article_fraud_user_table = self.dynamodb.Table(os.environ['ARTICLE_FRAUD_USER_TABLE_NAME'])
            self.__create_article_fraud_user(article_fraud_user_table)
        except ClientError as e:
            print(e)
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

    def __create_article_fraud_user(self, article_fraud_user_table):
        article_fraud_user = {
            'article_id': self.event['pathParameters']['article_id'],
            'user_id': self.event['requestContext']['authorizer']['claims']['cognito:username'],
            'created_at': int(time.time())
        }
        article_fraud_user_table.put_item(
            Item=article_fraud_user,
            ConditionExpression='attribute_not_exists(article_id)'
        )

    def __validate_plagiarism(self):
        # TODO:


