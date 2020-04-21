# -*- coding: utf-8 -*-
import os
import settings
import time
import json
import hashlib
import logging
import traceback
from boto3.dynamodb.conditions import Key
from db_util import DBUtil
from user_util import UserUtil
from private_chain_util import PrivateChainUtil
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError
from time_util import TimeUtil
from decimal_encoder import DecimalEncoder
from decimal import Decimal
from botocore.exceptions import ClientError
from exceptions import SendTransactionError, ReceiptError


class MeArticlesPurchaseCreate(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id'],
                'purchase_signed_transaction': settings.parameters['raw_transaction'],
                'burn_signed_transaction': settings.parameters['raw_transaction']
            },
            'required': ['article_id', 'purchase_signed_transaction', 'burn_signed_transaction']
        }

    def validate_params(self):
        # 認証・ウォレット情報が登録済であること
        UserUtil.verified_phone_and_email(self.event)
        UserUtil.validate_private_eth_address(self.dynamodb,
                                              self.event['requestContext']['authorizer']['claims']['cognito:username'])

        # single
        validate(self.params, self.get_schema())
        # 署名が正しいこと
        PrivateChainUtil.validate_raw_transaction_signature(
            self.params['purchase_signed_transaction'],
            self.event['requestContext']['authorizer']['claims']['custom:private_eth_address']
        )
        PrivateChainUtil.validate_raw_transaction_signature(
            self.params['burn_signed_transaction'],
            self.event['requestContext']['authorizer']['claims']['custom:private_eth_address']
        )

        # relation
        DBUtil.validate_article_existence(
            self.dynamodb,
            self.params['article_id'],
            status='public',
            is_purchased=True
        )
        DBUtil.validate_not_purchased(
            self.dynamodb,
            self.params['article_id'],
            self.event['requestContext']['authorizer']['claims']['cognito:username']
        )

    def exec_main_proc(self):
        ################
        # get parameter
        ################
        # get article info
        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        article_info = article_info_table.get_item(Key={'article_id': self.params['article_id']}).get('Item')
        # purchase article
        paid_articles_table = self.dynamodb.Table(os.environ['PAID_ARTICLES_TABLE_NAME'])
        paid_status_table = self.dynamodb.Table(os.environ['PAID_STATUS_TABLE_NAME'])
        # eth_address
        article_user_eth_address = UserUtil.get_private_eth_address(self.cognito, article_info['user_id'])
        user_eth_address = self.event['requestContext']['authorizer']['claims']['custom:private_eth_address']
        # transaction_count
        transaction_count = PrivateChainUtil.get_transaction_count(user_eth_address)

        ################
        # validation
        ################
        # does not purchase same user's article
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']
        if article_info['user_id'] == user_id:
            raise ValidationError('Can not purchase own article')
        # validate raw_transaction
        # purchase
        purchase_data = PrivateChainUtil.get_data_from_raw_transaction(
            self.params['purchase_signed_transaction'],
            transaction_count
        )
        PrivateChainUtil.validate_erc20_transfer_data(purchase_data, article_user_eth_address)
        # burn
        transaction_count = PrivateChainUtil.increment_transaction_count(transaction_count)
        burn_data = PrivateChainUtil.get_data_from_raw_transaction(
            self.params['burn_signed_transaction'],
            transaction_count
        )
        PrivateChainUtil.validate_erc20_transfer_data(burn_data, '0x' + os.environ['BURN_ADDRESS'])

        # burn 量が正しいこと
        purchase_value = int(purchase_data[72:], 16)
        burn_value = int(burn_data[72:], 16)
        calc_burn_value = int(Decimal(purchase_value) / Decimal(9))
        if burn_value != calc_burn_value:
            raise ValidationError('burn_value is invalid.')

        # purchase_value が記事で指定されている金額に基づいた量が設定されていること
        DBUtil.validate_latest_price(
            self.dynamodb,
            self.params['article_id'],
            purchase_value
        )

        ################
        # purchase
        ################
        sort_key = TimeUtil.generate_sort_key()
        # 多重リクエストによる不必要なレコード生成を防ぐためにpaid_statusレコードを生成
        self.__create_paid_status(paid_status_table, user_id)
        # 購入のトランザクション処理
        purchase_transaction = PrivateChainUtil.send_raw_transaction(self.params['purchase_signed_transaction'])
        # 購入記事データを作成
        self.__create_paid_article(paid_articles_table, article_info, purchase_transaction, sort_key)
        # プライベートチェーンへのポーリングを行いトランザクションの承認状態を取得
        transaction_status = self.__polling_to_private_chain(purchase_transaction)
        # トランザクションの承認状態をpaid_articleとpaid_statusに格納
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
                burn_transaction = PrivateChainUtil.send_raw_transaction(self.params['burn_signed_transaction'])
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

    def __create_paid_article(self, paid_articles_table, article_info, purchase_transaction, sort_key):
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
            'purchase_transaction': purchase_transaction,
            'sort_key': sort_key,
            'price': article_info['price'],
            'history_created_at': history_created_at,
            'status': 'doing',
            'created_at': int(time.time())
        }

        # 購入時のtransactionの保存
        paid_articles_table.put_item(
            Item=paid_article
        )

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
    def __update_transaction_status(article_info, paid_articles_table, transaction_status, sort_key,
                                    paid_status_table, user_id):
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

    def __polling_to_private_chain(self, purchase_transaction):
        try:
            if PrivateChainUtil.is_transaction_completed(purchase_transaction):
                return 'done'
            return 'doing'
        except (SendTransactionError, ReceiptError) as e:
            logging.info(e)
            return 'fail'

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
            'status': 'doing',
            'created_at': int(time.time())
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
