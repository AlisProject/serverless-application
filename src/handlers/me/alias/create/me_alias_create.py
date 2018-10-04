# -*- coding: utf-8 -*-
# TODO: 大文字小文字の区別
import json
import os
import settings
import logging
from boto3.dynamodb.conditions import Key
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError
from botocore.exceptions import ClientError


class MeAliasCreate(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'alias_user_id': settings.parameters['user_id']
            }
        }

    def validate_params(self):
        params = json.loads(self.event.get('body'))
        if params['alias_user_id'] in settings.ng_user_name:
            raise ValidationError('This username is not allowed')
        validate(params, self.get_schema())

    def exec_main_proc(self):
        params = self.event
        body = json.loads(params.get('body'))
        users_table = self.dynamodb.Table(os.environ['USERS_TABLE_NAME'])
        user_id = params['requestContext']['authorizer']['claims']['cognito:username']
        exist_check_user = users_table.get_item(
            Key={
                'user_id': body['alias_user_id']
            }
        )

        exist_check_alias_user = users_table.query(
            IndexName="alias_user_id-index",
            KeyConditionExpression=Key('alias_user_id').eq(body['alias_user_id'])
        )

        user = users_table.get_item(Key={'user_id': user_id}).get('Item')
        if 'alias_user_id' in user:
            raise ValidationError('The alias id of this user has been added.')

        elif ('Item' not in exist_check_user) and (len(exist_check_alias_user['Items']) == 0):
            try:
                expression_attribute_values = {
                    ':alias_user_id': body['alias_user_id']
                }
                response = users_table.update_item(
                    Key={
                        'user_id': user_id
                    },
                    UpdateExpression="set alias_user_id=:alias_user_id",
                    ExpressionAttributeValues=expression_attribute_values
                )
                return {'statusCode': response['ResponseMetadata']['HTTPStatusCode']}
            except ClientError as e:
                logging.fatal(e)
                return {
                    'statusCode': 500,
                    'body': json.dumps({'message': 'Internal server error'})
                }

        else:
            raise ValidationError('This id is already in use.')
