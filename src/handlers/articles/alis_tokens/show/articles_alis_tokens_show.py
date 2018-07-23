# -*- coding: utf-8 -*-
import os
import json
import settings
from db_util import DBUtil
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError
from decimal_encoder import DecimalEncoder


class ArticlesAlisTokensShow(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id']
            },
            'required': ['article_id']
        }

    def validate_params(self):
        # single
        params = self.event.get('pathParameters')

        if params is None:
            raise ValidationError('pathParameters is required')

        validate(params, self.get_schema())
        # relation
        DBUtil.validate_article_existence(
            self.dynamodb,
            params['article_id'],
            status='public'
        )

    def exec_main_proc(self):
        article_evaluated_manage_table = self.dynamodb.Table(os.environ['ARTICLE_EVALUATED_MANAGE_TABLE_NAME'])
        article_alis_token_table = self.dynamodb.Table(os.environ['ARTICLE_ALIS_TOKEN_TABLE_NAME'])
        article_evaluated_manage = article_evaluated_manage_table.get_item(Key={'type': 'alistoken'})

        if article_evaluated_manage.get('Item') is None:
            return {
                'statusCode': 200,
                'body': json.dumps({'article_id': self.params['article_id'], 'alis_token': 0})
            }

        responce = article_alis_token_table.get_item(
            Key={
                'evaluated_at': article_evaluated_manage['Item']['active_evaluated_at'],
                'article_id': self.params['article_id']
            }
        )

        if responce.get('Item') is None:
            return {
                'statusCode': 200,
                'body': json.dumps({'article_id': self.params['article_id'], 'alis_token': 0})
            }

        return {
            'statusCode': 200,
            'body': json.dumps(responce['Item'], cls=DecimalEncoder)
        }
