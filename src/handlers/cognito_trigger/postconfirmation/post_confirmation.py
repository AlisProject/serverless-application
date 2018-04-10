# -*- coding: utf-8 -*-
import os
import urllib.request
import json
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
        empty_data = json.dumps({}).encode('utf-8')
        headers = {'Content-Type': 'application/json'}
        url = os.environ['PRIVATE_CHAIN_API'] + '/accounts/new'
        request = urllib.request.Request(url, data=empty_data, method='POST', headers=headers)

        with urllib.request.urlopen(request) as response:
            response_data = response.read().decode('utf-8')

        return json.loads(response_data)['result']
