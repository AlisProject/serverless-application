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
        return self.event
