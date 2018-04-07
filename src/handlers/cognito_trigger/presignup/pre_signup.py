# -*- coding: utf-8 -*-
import os
import boto3
import settings
import re
from jsonschema import validate, ValidationError
from lambda_base import LambdaBase


class PreSignUp(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'userName': settings.parameters['user_id']
            }
        }

    def validate_params(self):
        params = self.event
        if self.event['userName'] in settings.ng_user_name:
            raise ValidationError('This username is not allowed')
        validate(params, self.get_schema())

    def exec_main_proc(self):
        if os.environ['BETA_MODE_FLAG'] == "1":
            beta_table = self.dynamodb.Table(os.environ['BETA_USERS_TABLE_NAME'])
            item = beta_table.get_item(
                Key={
                    'email': self.event['request']['userAttributes']['email']
                }
            )
            if item.get('Item', False) and item['Item']['used'] is False:
                return self.event
            else:
                raise "This email address is not avalilable"
        else:
            return self.event
