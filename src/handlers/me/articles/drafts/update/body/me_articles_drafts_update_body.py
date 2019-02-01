# -*- coding: utf-8 -*-
import os
import settings
from lambda_base import LambdaBase
from text_sanitizer import TextSanitizer
from db_util import DBUtil


class MeArticlesDraftsUpdateBody(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id'],
                'body': settings.parameters['body']
            }
        }

    def validate_params(self):
        pass

    def exec_main_proc(self):
        DBUtil.validate_article_existence(
            self.dynamodb,
            self.params['article_id'],
            user_id=self.event['requestContext']['authorizer']['claims']['cognito:username'],
            status='draft'
        )

        self.__update_article_content()

        return {
            'statusCode': 200
        }

    def __update_article_content(self):
        article_content_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_TABLE_NAME'])

        expression_attribute_values = {
            # ':body': TextSanitizer.sanitize_article_body(self.params.get('body'))
            ':body': self.params.get('body')
        }

        DBUtil.items_values_empty_to_none(expression_attribute_values)

        article_content_table.update_item(
            Key={
                'article_id': self.params['article_id'],
            },
            UpdateExpression="set body=:body",
            ExpressionAttributeValues=expression_attribute_values
        )
