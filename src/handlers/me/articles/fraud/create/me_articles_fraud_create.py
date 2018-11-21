# -*- coding: utf-8 -*-
import os
import settings
import time
import json
from db_util import DBUtil
from botocore.exceptions import ClientError
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError, FormatChecker

from text_sanitizer import TextSanitizer
from user_util import UserUtil


class MeArticlesFraudCreate(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id'],
                'reason': settings.parameters['fraud']['reason'],
                'origin_url': settings.parameters['fraud']['origin_url'],
                'free_text': settings.parameters['fraud']['free_text']
            },
            'required': ['article_id', 'reason']
        }

    def validate_params(self):
        UserUtil.verified_phone_and_email(self.event)

        # single
        if self.event.get('pathParameters') is None:
            raise ValidationError('pathParameters is required')
        validate(self.params, self.get_schema(), format_checker=FormatChecker())

        # 著作権侵害の場合はオリジナル記事のURLを必須とする
        if self.params['reason'] == 'copyright_violation':
            if not self.params['origin_url']:
                raise ValidationError('origin url is required')

        # relation
        DBUtil.validate_article_existence(
            self.dynamodb,
            self.event['pathParameters']['article_id'],
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
            'reason': self.params.get('reason'),
            'origin_url': self.params.get('origin_url'),
            'free_text': TextSanitizer.sanitize_text(self.params.get('free_text')),
            'created_at': int(time.time())
        }
        DBUtil.items_values_empty_to_none(article_fraud_user)

        article_fraud_user_table.put_item(
            Item=article_fraud_user,
            ConditionExpression='attribute_not_exists(article_id)'
        )
