# -*- coding: utf-8 -*-
import os
import settings
import time
import json
import requests
from boto3.dynamodb.conditions import Key
from db_util import DBUtil
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError
from time_util import TimeUtil
from user_util import UserUtil
from record_not_found_error import RecordNotFoundError
from exceptions import SendTransactionError
from aws_requests_auth.aws_auth import AWSRequestsAuth
from decimal_encoder import DecimalEncoder


class MeArticlesPurchaseCreate(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id'],
                'price': settings.parameters['price']
            },
            'required': ['article_id', 'price']
        }

    def validate_params(self):
        UserUtil.verified_phone_and_email(self.event)

        # check price type is integer or decimal
        try:
            self.params['price'] = int(self.params['price'])
        except ValueError:
            raise ValidationError('Price must be integer')

        # check price value is not decimal
        price = self.params['price'] / 10 ** 18
        if price.is_integer() is False:
            raise ValidationError('Decimal value is not allowed')

        # single
        validate(self.params, self.get_schema())
        # relation
        DBUtil.validate_article_existence(
            self.dynamodb,
            self.params['article_id'],
            status='public'
        )
        # validate latest price
        DBUtil.validate_latest_price(
            self.dynamodb,
            self.params['article_id'],
            self.params['price']
        )

    def exec_main_proc(self):
        # get article info
        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        article_info = article_info_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')
        # does not purchase same user's article
        if article_info['user_id'] == self.event['requestContext']['authorizer']['claims']['cognito:username']:
            raise ValidationError('Can not purchase own article')

        # purchase article
        article_user_eth_address = self.__get_user_private_eth_address(article_info['user_id'])
        user_eth_address = self.event['requestContext']['authorizer']['claims']['custom:private_eth_address']
        price = self.params['price']
        transactions = self.__purchase_article(user_eth_address, article_user_eth_address, price)

        # create article_purchased_table
        self.__create_paid_articles(transactions, article_info)

        return {
            'statusCode': 200
        }

    @staticmethod
    def __purchase_article(user_eth_address, article_user_eth_address, price):
        headers = {'content-type': 'application/json'}
        purchase_price = format(int(price * 0.9), '064x')
        burn_token = format(int(price * 0.1), '064x')
        purchase_payload = json.dumps(
            {
                'from_user_eth_address': user_eth_address,
                'to_user_eth_address': article_user_eth_address[2:],
                'tip_value': purchase_price
            }
        )
        burn_payload = json.dumps(
            {
                'from_user_eth_address': user_eth_address,
                'to_user_eth_address': '0000000000000000000000000000000000000000',
                'tip_value': burn_token
            }
        )
        auth = AWSRequestsAuth(aws_access_key=os.environ['PRIVATE_CHAIN_AWS_ACCESS_KEY'],
                               aws_secret_access_key=os.environ['PRIVATE_CHAIN_AWS_SECRET_ACCESS_KEY'],
                               aws_host=os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'],
                               aws_region='ap-northeast-1',
                               aws_service='execute-api')
        # purchase article transaction
        response = requests.post('https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] +
                                 '/production/wallet/tip', auth=auth, headers=headers, data=purchase_payload)

        # exists error
        if json.loads(response.text).get('error'):
            raise SendTransactionError(json.loads(response.text).get('error'))
        # burn transaction
        burn_response = requests.post('https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] +
                                      '/production/wallet/tip', auth=auth, headers=headers, data=burn_payload)

        # exists error
        if json.loads(burn_response.text).get('error'):
            raise SendTransactionError(json.loads(burn_response.text).get('error'))

        return json.dumps({
            'purchase_transaction_hash': json.loads(response.text).get('result').replace('"', ''),
            'burn_transaction_hash': json.loads(burn_response.text).get('result').replace('"', '')
        })

    def __create_paid_articles(self, transactions, article_info):
        paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])
        article_history_table = self.dynamodb.Table(os.environ['ARTICLE_HISTORY_TABLE_NAME'])
        article_histories = article_history_table.query(
            KeyConditionExpression=Key('article_id').eq(self.params['article_id']),
            ScanIndexForward=False
        )['Items']
        history_created_at = ''
        # 降順でarticle_infoの価格と同じ一番新しい記事historyデータを取得する
        for Item in json.loads(json.dumps(article_histories, cls=DecimalEncoder)):
            if Item.get('price') is not None and Item.get('price') == article_info['price']:
                history_created_at = Item.get('created_at')
                break

        paid_article = {
            'article_id': self.params['article_id'],
            'user_id': self.event['requestContext']['authorizer']['claims']['cognito:username'],
            'article_user_id': article_info['user_id'],
            'created_at': int(time.time()),
            'history_created_at': history_created_at,
            'status': 'doing',
            'purchase_transaction': json.loads(transactions).get('purchase_transaction_hash'),
            'burn_transaction': json.loads(transactions).get('burn_transaction_hash'),
            'sort_key': TimeUtil.generate_sort_key(),
            'price': self.params['price']
        }
        paid_articles_table.put_item(
            Item=paid_article,
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
