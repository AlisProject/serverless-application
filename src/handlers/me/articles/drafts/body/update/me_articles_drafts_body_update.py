# -*- coding: utf-8 -*-
import os
import settings
from lambda_base import LambdaBase
from jsonschema import validate, FormatChecker
from db_util import DBUtil
from user_util import UserUtil
from text_sanitizer import TextSanitizer


class MeArticlesDraftsBodyUpdate(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id'],
                'body': settings.parameters['body']
            },
            'required': ['article_id', 'body']
        }

    def validate_params(self):
        UserUtil.verified_phone_and_email(self.event)
        validate(self.params, self.get_schema(), format_checker=FormatChecker())
        DBUtil.validate_article_existence(
            self.dynamodb,
            self.params['article_id'],
            user_id=self.event['requestContext']['authorizer']['claims']['cognito:username'],
            status='draft',
            version=2
        )

    def exec_main_proc(self):
        # 下書き記事を保存
        expression_attribute_values = {
            ':body': TextSanitizer.sanitize_article_body_v2(self.params.get('body'))
        }
        DBUtil.items_values_empty_to_none(expression_attribute_values)
        self.__update_article_content(expression_attribute_values)
        # 履歴を保存
        DBUtil.put_article_content_edit_history(
            dynamodb=self.dynamodb,
            user_id=self.event['requestContext']['authorizer']['claims']['cognito:username'],
            article_id=self.params.get('article_id'),
            sanitized_body=expression_attribute_values[':body']
        )

        return {
            'statusCode': 200
        }

    def __update_article_content(self, expression_attribute_values):
        article_content_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_TABLE_NAME'])

        article_content_table.update_item(
            Key={
                'article_id': self.params['article_id'],
            },
            UpdateExpression="set body=:body",
            ExpressionAttributeValues=expression_attribute_values
        )
