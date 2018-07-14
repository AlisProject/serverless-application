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
                'reason': settings.parameters['fraud_user']['reason'],
                'plagiarism_url': settings.parameters['fraud_user']['plagiarism_url'],
                'plagiarism_description': settings.parameters['fraud_user']['plagiarism_description'],
                'illegal_content': settings.parameters['fraud_user']['illegal_content']
            },
            'anyOf': [
                {
                    'properties': {
                        'reason': {
                            'enum': settings.FRAUD_REASONS
                        },
                    }

                }
            ],
            'required': ['article_id']
        }

    def validate_params(self):
        # single
        if self.event.get('pathParameters') is None:
            raise ValidationError('pathParameters is required')
        validate(self.params, self.get_schema())
        self.__validate_reason_dependencies(self.params)
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

    def __validate_reason_dependencies(self, params):
        reason = params.get('reason', '')
        if reason in settings.FRAUD_NEED_ORIGINAL_REASONS:
            self.__validate_dependencies(params, ['plagiarism_url', 'plagiarism_description'])

        if reason in settings.FRAUD_NEED_DETAIL_REASONS:
            self.__validate_dependencies(params, ['illegal_content'])

    def __validate_dependencies(self, params, required_items):
        for item in required_items:
            if not params[item]:
                raise ValidationError("%s is required" % item)

