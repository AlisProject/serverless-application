# -*- coding: utf-8 -*-
import os
import json
import requests
from aws_requests_auth.aws_auth import AWSRequestsAuth
from lambda_base import LambdaBase


class PostConfirmation(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        self.__wallet_initialization()

        users = self.dynamodb.Table(os.environ['USERS_TABLE_NAME'])
        user = {
            'user_id': self.event['userName'],
            'user_display_name': self.event['userName']
        }
        users.put_item(Item=user, ConditionExpression='attribute_not_exists(user_id)')
        if os.environ['BETA_MODE_FLAG'] == "1":
            beta_users = self.dynamodb.Table(os.environ['BETA_USERS_TABLE_NAME'])
            beta_user = {
                'email': self.event['request']['userAttributes']['email'],
                'used': True
            }
            beta_users.put_item(Item=beta_user)
        return True

    def __wallet_initialization(self):
        if 'custom:private_eth_address' in self.event['request']['userAttributes']:
            return True

        address = self.__create_new_account()
        self.cognito.admin_update_user_attributes(
            UserPoolId=self.event['userPoolId'],
            Username=self.event['userName'],
            UserAttributes=[
                {
                    'Name': 'custom:private_eth_address',
                    'Value': address
                },
            ]
        )

    @staticmethod
    def __create_new_account():
        auth = AWSRequestsAuth(aws_access_key=os.environ['PRIVATE_CHAIN_AWS_ACCESS_KEY'],
                               aws_secret_access_key=os.environ['PRIVATE_CHAIN_AWS_SECRET_ACCESS_KEY'],
                               aws_host=os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'],
                               aws_region='ap-northeast-1',
                               aws_service='execute-api')
        response = requests.post('https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] +
                                 '/production/accounts/new', auth=auth)
        return json.loads(response.text)['result']
