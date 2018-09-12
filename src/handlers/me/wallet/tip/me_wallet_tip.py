# -*- coding: utf-8 -*-
import os
import settings
import json
import requests
import time
from time_util import TimeUtil
from user_util import UserUtil
from db_util import DBUtil
from aws_requests_auth.aws_auth import AWSRequestsAuth
from jsonschema import validate
from lambda_base import LambdaBase
from jsonschema import ValidationError
from record_not_found_error import RecordNotFoundError
from exceptions import SendTransactionError


class MeWalletTip(LambdaBase):

    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id'],
                'tip_value': settings.parameters['tip_value'],
            },
            'required': ['article_id', 'tip_value']
        }

    def validate_params(self):
        # single
        # フロント（js）の都合上桁数が多い場合は指数表記で値が渡る事があるため、int 型に整形
        self.params['tip_value'] = int(self.params['tip_value'])
        validate(self.params, self.get_schema())
        # relation
        DBUtil.validate_article_existence(
            self.dynamodb,
            self.params['article_id'],
            status='public'
        )

    def exec_main_proc(self):
        # get article info
        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        article_info = article_info_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')
        # validation
        # does not tip same user
        if article_info['user_id'] == self.event['requestContext']['authorizer']['claims']['cognito:username']:
            raise ValidationError('Can not tip to myself')

        # send tip
        from_user_eth_address = self.event['requestContext']['authorizer']['claims']['custom:private_eth_address']
        to_user_eth_address = self.__get_user_private_eth_address(article_info['user_id'])
        tip_value = self.params['tip_value']
        transaction_hash = self.__send_tip(from_user_eth_address, to_user_eth_address, tip_value)

        # create tip info
        self.__create_tip_info(transaction_hash, article_info)

        return {
            'statusCode': 200
        }

    @staticmethod
    def __send_tip(from_user_eth_address, to_user_eth_address, tip_value):
        headers = {'content-type': 'application/json'}
        payload = json.dumps(
            {
                'from_user_eth_address': from_user_eth_address,
                'to_user_eth_address': to_user_eth_address[2:],
                'tip_value': format(tip_value, '064x')
            }
        )
        auth = AWSRequestsAuth(aws_access_key=os.environ['PRIVATE_CHAIN_AWS_ACCESS_KEY'],
                               aws_secret_access_key=os.environ['PRIVATE_CHAIN_AWS_SECRET_ACCESS_KEY'],
                               aws_host=os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'],
                               aws_region='ap-northeast-1',
                               aws_service='execute-api')
        response = requests.post('https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] +
                                 '/production/wallet/tip', auth=auth, headers=headers, data=payload)

        # exists error
        if json.loads(response.text).get('error'):
            raise SendTransactionError(json.loads(response.text).get('error'))

        # return transaction hash
        return json.dumps(json.loads(response.text).get('result')).replace('"', '')

    def __create_tip_info(self, transaction_hash, article_info):
        tip_table = self.dynamodb.Table(os.environ['TIP_TABLE_NAME'])

        sort_key = TimeUtil.generate_sort_key()
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']

        tip_info = {
            'user_id': user_id,
            'to_user_id': article_info['user_id'],
            'tip_value': self.params['tip_value'],
            'article_id': self.params['article_id'],
            'article_title': article_info['title'],
            'transaction': transaction_hash,
            'uncompleted': 1,
            'sort_key': sort_key,
            'created_at': int(time.time())
        }

        tip_table.put_item(
            Item=tip_info,
            ConditionExpression='attribute_not_exists(user_id)'
        )

    def __get_user_private_eth_address(self, user_id):
        # user_id に紐づく private_eth_address を取得
        user_info = UserUtil.get_cognito_user_info(self.cognito, user_id)
        private_eth_address = [a for a in user_info['UserAttributes'] if a.get('Name') == 'custom:private_eth_address']
        # private_eth_address が存在しないケースは想定していないため、取得出来ない場合は例外とする
        if len(private_eth_address) != 1:
            raise RecordNotFoundError('Record Not Found: private_eth_address')

        return private_eth_address[0]['Value']
