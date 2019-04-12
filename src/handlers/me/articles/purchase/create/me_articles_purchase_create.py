# -*- coding: utf-8 -*-
import os
import settings
import time
import json
import requests
import hashlib
import logging
import traceback
from boto3.dynamodb.conditions import Key
from db_util import DBUtil
from user_util import UserUtil
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError
from time_util import TimeUtil
from record_not_found_error import RecordNotFoundError
from exceptions import SendTransactionError
from aws_requests_auth.aws_auth import AWSRequestsAuth
from decimal_encoder import DecimalEncoder
from time import sleep
from decimal import Decimal
from botocore.exceptions import ClientError


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
        # single
        # check price type is integer or decimal
        try:
            self.params['price'] = int(self.params['price'])
        except ValueError:
            raise ValidationError('Price must be integer')

        # check price value is not decimal
        price = self.params['price'] / 10 ** 18
        if price.is_integer() is False:
            raise ValidationError('Decimal value is not allowed')
        validate(self.params, self.get_schema())

        # relation
        DBUtil.validate_article_existence(
            self.dynamodb,
            self.params['article_id'],
            status='public'
        )
        DBUtil.validate_latest_price(
            self.dynamodb,
            self.params['article_id'],
            self.params['price']
        )
        DBUtil.validate_not_purchased(
            self.dynamodb,
            self.params['article_id'],
            self.event['requestContext']['authorizer']['claims']['cognito:username']
        )

    def exec_main_proc(self):
        # get article info
        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        article_info = article_info_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')
        # does not purchase same user's article
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']
        if article_info['user_id'] == user_id:
            raise ValidationError('Can not purchase own article')

        # purchase article
        paid_status_table = self.dynamodb.Table(os.environ['PAID_STATUS_TABLE_NAME'])
        paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])
        article_user_eth_address = self.__get_user_private_eth_address(article_info['user_id'])
        user_eth_address = self.event['requestContext']['authorizer']['claims']['custom:private_eth_address']
        price = self.params['price']

        auth = AWSRequestsAuth(aws_access_key=os.environ['PRIVATE_CHAIN_AWS_ACCESS_KEY'],
                               aws_secret_access_key=os.environ['PRIVATE_CHAIN_AWS_SECRET_ACCESS_KEY'],
                               aws_host=os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'],
                               aws_region='ap-northeast-1',
                               aws_service='execute-api')
        headers = {'content-type': 'application/json'}

        sort_key = TimeUtil.generate_sort_key()

        # 購入記事データを作成
        self.__create_paid_status(paid_status_table, user_id)
        self.__create_paid_article(paid_articles_table, article_info, sort_key)
        # 購入のトランザクション処理
        purchase_transaction = self.__create_purchase_transaction(auth, headers, user_eth_address,
                                                                  article_user_eth_address, price)
        # 購入のトランザクション処理を記事購入データに格納
        self.__add_purchase_transaction_to_paid_article(purchase_transaction, paid_articles_table, article_info,
                                                        sort_key)

        # プライベートチェーンへのポーリングを行いトランザクションの承認状態を取得
        transaction_status = self.__polling_to_private_chain(purchase_transaction, auth, headers)
        # トランザクションの承認状態をpaid_artilcleとpaid_statusに格納
        self.__update_transaction_status(article_info, paid_articles_table, transaction_status, sort_key,
                                         paid_status_table, user_id)

        # 購入のトランザクションが成功した時のみバーンのトランザクションを発行する
        if transaction_status == 'done':
            try:
                # 購入に成功した場合、著者の未読通知フラグをTrueにする
                self.__update_unread_notification_manager(article_info['user_id'])
                # 著者へ通知を作成
                self.__notify_author(article_info, user_id)
                # バーンのトランザクション処理
                burn_transaction = self.__burn_transaction(price, user_eth_address, auth, headers)
                # バーンのトランザクションを購入テーブルに格納
                self.__add_burn_transaction_to_paid_article(burn_transaction, paid_articles_table,
                                                            article_info, sort_key)
            except Exception as err:
                logging.fatal(err)
                traceback.print_exc()
        # 記事購入者へは購入処理中の場合以外で通知を作成
        if transaction_status == 'done' or transaction_status == 'fail':
            self.__update_unread_notification_manager(user_id)
            self.__notify_purchaser(article_info, user_id, transaction_status)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': transaction_status
            })
        }

    @staticmethod
    def __create_purchase_transaction(auth, headers, user_eth_address, article_user_eth_address, price):
        purchase_price = format(int(Decimal(price) * Decimal(9) / Decimal(10)), '064x')
        purchase_payload = json.dumps(
            {
                'from_user_eth_address': user_eth_address,
                'to_user_eth_address': article_user_eth_address[2:],
                'tip_value': purchase_price
            }
        )
        # purchase article transaction
        response = requests.post('https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] +
                                 '/production/wallet/tip', auth=auth, headers=headers, data=purchase_payload)
        # validate status code
        if response.status_code != 200:
            raise SendTransactionError('status code not 200')

        # exists error
        if json.loads(response.text).get('error'):
            raise SendTransactionError(json.loads(response.text).get('error'))

        return json.loads(response.text).get('result').replace('"', '')

    def __create_paid_article(self, paid_articles_table, article_info, sort_key):
        article_history_table = self.dynamodb.Table(os.environ['ARTICLE_HISTORY_TABLE_NAME'])
        article_histories = article_history_table.query(
            KeyConditionExpression=Key('article_id').eq(self.params['article_id']),
            ScanIndexForward=False
        )['Items']
        history_created_at = None
        # 一番新しい記事historyデータを取得する
        for Item in json.loads(json.dumps(article_histories, cls=DecimalEncoder)):
            if Item.get('price') is not None and Item.get('price') == article_info['price']:
                history_created_at = Item.get('created_at')
                break

        # burnのtransactionが失敗した場合に購入transactionを追跡するためにburn_transaction以外を保存
        paid_article = {
            'article_id': self.params['article_id'],
            'user_id': self.event['requestContext']['authorizer']['claims']['cognito:username'],
            'article_user_id': article_info['user_id'],
            'article_title': article_info['title'],
            'sort_key': sort_key,
            'price': self.params['price'],
            'history_created_at': history_created_at,
            'status': 'doing',
            'created_at': int(time.time())
        }
        # 購入レコードの保存
        paid_articles_table.put_item(
            Item=paid_article
        )

    @staticmethod
    def __add_purchase_transaction_to_paid_article(purchase_transaction, paid_articles_table, article_info, sort_key):
        purchase_transaction = {
            ':purchase_transaction': purchase_transaction
        }
        paid_articles_table.update_item(
            Key={
                'article_id': article_info['article_id'],
                'sort_key': sort_key
            },
            UpdateExpression="set purchase_transaction = :purchase_transaction",
            ExpressionAttributeValues=purchase_transaction
        )

    @staticmethod
    def __burn_transaction(price, user_eth_address, auth, headers):
        burn_token = format(int(Decimal(price) / Decimal(10)), '064x')

        burn_payload = json.dumps(
            {
                'from_user_eth_address': user_eth_address,
                'to_user_eth_address': settings.ETH_ZERO_ADDRESS,
                'tip_value': burn_token
            }
        )

        # burn transaction
        response = requests.post('https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] +
                                 '/production/wallet/tip', auth=auth, headers=headers, data=burn_payload)

        # validate status code
        if response.status_code != 200:
            raise SendTransactionError('status code not 200')

        # exists error
        if json.loads(response.text).get('error'):
            raise SendTransactionError(json.loads(response.text).get('error'))

        return json.loads(response.text).get('result').replace('"', '')

    @staticmethod
    def __add_burn_transaction_to_paid_article(burn_transaction, paid_articles_table, article_info, sort_key):
        burn_transaction = {
            ':burn_transaction': burn_transaction
        }
        paid_articles_table.update_item(
            Key={
                'article_id': article_info['article_id'],
                'sort_key': sort_key
            },
            UpdateExpression="set burn_transaction = :burn_transaction",
            ExpressionAttributeValues=burn_transaction
        )

    @staticmethod
    def __update_transaction_status(article_info, paid_articles_table, transaction_status,
                                    sort_key, paid_status_table, user_id):
        paid_articles_table.update_item(
            Key={
                'article_id': article_info['article_id'],
                'sort_key': sort_key
            },
            UpdateExpression="set #attr = :transaction_status",
            ExpressionAttributeNames={'#attr': 'status'},
            ExpressionAttributeValues={':transaction_status': transaction_status}
        )

        # lock用のpaid_statusの:statusを更新
        paid_status_table.update_item(
            Key={
                'article_id': article_info['article_id'],
                'user_id': user_id
            },
            UpdateExpression="set #attr = :transaction_status",
            ExpressionAttributeNames={'#attr': 'status'},
            ExpressionAttributeValues={':transaction_status': transaction_status}
        )

    def __get_user_private_eth_address(self, user_id):
        # user_id に紐づく private_eth_address を取得
        user_info = UserUtil.get_cognito_user_info(self.cognito, user_id)
        private_eth_address = [a for a in user_info['UserAttributes'] if a.get('Name') == 'custom:private_eth_address']
        # private_eth_address が存在しないケースは想定していないため、取得出来ない場合は例外とする
        if len(private_eth_address) != 1:
            raise RecordNotFoundError('Record Not Found: private_eth_address')

        return private_eth_address[0]['Value']

    @staticmethod
    def __check_transaction_confirmation(purchase_transaction, auth, headers):
        receipt_payload = json.dumps(
            {
                'transaction_hash': purchase_transaction
            }
        )
        response = requests.post('https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] +
                                 '/production/transaction/receipt', auth=auth, headers=headers, data=receipt_payload)

        # validate status code
        if response.status_code != 200:
            raise SendTransactionError('status code not 200')

        # exists error
        if json.loads(response.text).get('error'):
            raise SendTransactionError(json.loads(response.text).get('error'))

        return response.text

    def __polling_to_private_chain(self, purchase_transaction, auth, headers):
        # 最大10回トランザクション詳細を問い合わせる(回数については問題がある場合検討)
        count = settings.POLLING_INITIAL_COUNT
        while count < settings.POLLING_MAX_COUNT:
            count += 1
            # 1秒待機
            sleep(1)
            # check whether transaction is completed
            transaction_info = self.__check_transaction_confirmation(purchase_transaction, auth, headers)
            result = json.loads(transaction_info).get('result')
            # exists error
            if json.loads(transaction_info).get('error'):
                return 'fail'
            # receiptがnullの場合countをインクリメントしてループ処理
            if result is None or len(result['logs']) == 0:
                continue
            # transactionが承認済みであればstatusをdoneにする
            if result['logs'][0].get('type') == 'mined':
                return 'done'
        return 'doing'

    def __update_unread_notification_manager(self, user_id):
        unread_notification_manager_table = self.dynamodb.Table(os.environ['UNREAD_NOTIFICATION_MANAGER_TABLE_NAME'])
        unread_notification_manager_table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='set unread = :unread',
            ExpressionAttributeValues={':unread': True}
        )

    def __notify_author(self, article_info, user_id):
        notification_table = self.dynamodb.Table(os.environ['NOTIFICATION_TABLE_NAME'])

        notification_table.put_item(Item={
            'notification_id': self.__get_randomhash(),
            'user_id': article_info['user_id'],
            'acted_user_id': user_id,
            'article_id': article_info['article_id'],
            'article_user_id': article_info['user_id'],
            'article_title': article_info['title'],
            'sort_key': TimeUtil.generate_sort_key(),
            'type': settings.ARTICLE_PURCHASED_TYPE,
            'price': int(article_info['price']),
            'created_at': int(time.time())
        })

    def __notify_purchaser(self, article_info, user_id, transaction_status):
        notification_table = self.dynamodb.Table(os.environ['NOTIFICATION_TABLE_NAME'])

        notification_table.put_item(Item={
            'notification_id': self.__get_randomhash(),
            'user_id': user_id,
            'acted_user_id': user_id,
            'article_id': article_info['article_id'],
            'article_user_id': article_info['user_id'],
            'article_title': article_info['title'],
            'sort_key': TimeUtil.generate_sort_key(),
            'type': settings.ARTICLE_PURCHASE_TYPE if transaction_status == 'done' else settings.ARTICLE_PURCHASE_ERROR_TYPE,
            'price': int(article_info['price']),
            'created_at': int(time.time())
        })

    @staticmethod
    def __get_randomhash():
        return hashlib.sha256((str(time.time()) + str(os.urandom(16))).encode('utf-8')).hexdigest()

    def __create_paid_status(self, paid_status_table, user_id):
        item = {
            'article_id': self.params['article_id'],
            'user_id': user_id,
            'status': 'doing'
        }
        try:
            paid_status_table.put_item(
                Item=item,
                ConditionExpression='#st <> :status1 and #st <> :status2',
                ExpressionAttributeValues={
                    ':status1': 'done',
                    ':status2': 'doing',
                },
                ExpressionAttributeNames={
                    '#st': 'status'
                }
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ValidationError('You have already purchased')
            else:
                raise e
