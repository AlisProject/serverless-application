# -*- coding: utf-8 -*-
import os
import json
import settings
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError, FormatChecker
from text_sanitizer import TextSanitizer
from db_util import DBUtil
from user_util import UserUtil


class MeArticlesPublicUpdate(LambdaBase):
    def get_schema(self):
        params = json.loads(self.event.get('body'))
        if 'version' in params and params['version'] is 200:
            return {
                'type': 'object',
                'properties': {
                    'article_id': settings.parameters['article_id'],
                    'title': settings.parameters['title'],
                    'eye_catch_url': settings.parameters['eye_catch_url'],
                    'overview': settings.parameters['overview'],
                    'body': {
                        'type': 'array'
                    }
                }
            }
        else:
            return {
                'type': 'object',
                'properties': {
                    'article_id': settings.parameters['article_id'],
                    'title': settings.parameters['title'],
                    'body': settings.parameters['body'],
                    'eye_catch_url': settings.parameters['eye_catch_url'],
                    'overview': settings.parameters['overview']
                }
            }

    def validate_params(self):
        UserUtil.verified_phone_and_email(self.event)
        if not self.event.get('pathParameters'):
            raise ValidationError('pathParameters is required')

        if not self.event.get('body') or not json.loads(self.event.get('body')):
            raise ValidationError('Request parameter is required')

        params = json.loads(self.event.get('body'))

        validate(params, self.get_schema(), format_checker=FormatChecker())

        DBUtil.validate_article_existence(
            self.dynamodb,
            self.params['article_id'],
            user_id=self.event['requestContext']['authorizer']['claims']['cognito:username'],
            status='public'
        )

    def exec_main_proc(self):
        article_content_edit_table = self.dynamodb.Table(os.environ['ARTICLE_CONTENT_EDIT_TABLE_NAME'])
        params = json.loads(self.event.get('body'))
        update_expression = "set user_id = :user_id, title = :title, " \
                            "body=:body, overview=:overview, eye_catch_url=:eye_catch_url"
        if 'version' in params and params['version'] is 200:
            expression_attribute_values = {
                ':user_id': self.event['requestContext']['authorizer']['claims']['cognito:username'],
                ':title': TextSanitizer.sanitize_text(self.params.get('title')),
                ':body': TextSanitizer.sanitize_article_object(self.params.get('body')),
                ':overview': TextSanitizer.sanitize_text(self.params.get('overview')),
                ':eye_catch_url': self.params.get('eye_catch_url'),
                ':version': self.params.get('version'),
            }
            update_expression = update_expression + ', version=:version'
        else:
            expression_attribute_values = {
                ':user_id': self.event['requestContext']['authorizer']['claims']['cognito:username'],
                ':title': TextSanitizer.sanitize_text(self.params.get('title')),
                ':body': TextSanitizer.sanitize_article_body(self.params.get('body')),
                ':overview': TextSanitizer.sanitize_text(self.params.get('overview')),
                ':eye_catch_url': self.params.get('eye_catch_url')
            }
        DBUtil.items_values_empty_to_none(expression_attribute_values)

        article_content_edit_table.update_item(
            Key={
                'article_id': self.params['article_id'],
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )

        return {
            'statusCode': 200
        }
