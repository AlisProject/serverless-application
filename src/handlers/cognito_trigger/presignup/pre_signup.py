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
        if re.match(r"^\-", self.event['userName']) or re.match(r".*\-$", self.event['userName']):
            raise ValidationError('not allowed hyphen at head or end')
        if re.match(r".*\-\-.*", self.event['userName']):
            raise ValidationError('double hyphen is not allowed')
        validate(params, self.get_schema())

    def exec_main_proc(self):
        return {'statusCode': 200}
