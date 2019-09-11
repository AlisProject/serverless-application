# -*- coding: utf-8 -*-
import settings
import os
import time
import csv
import hashlib
import boto3
from datetime import datetime, timedelta, timezone
from time_util import TimeUtil
from user_util import UserUtil
from web3 import Web3, HTTPProvider
from lambda_base import LambdaBase
from record_not_found_error import RecordNotFoundError

### TODO: getusercognitoidの変数をssm化（apigatewayからidentityidを取得できない場合）
class MeWalletTokenAllhistoriesCreate(LambdaBase):

    web3 = None
    address = None
    user_id = None
    eoa = None
    writer = None
    tmp_csv_file = None

    def get_schema(self):
        pass

    def validate_params(self):
        UserUtil.verified_phone_and_email(self.event)

    def exec_main_proc(self):
        self.web3 = Web3(HTTPProvider(os.environ['PRIVATE_CHAIN_OPERATION_URL']))
        self.address = self.web3.toChecksumAddress(os.environ['PRIVATE_CHAIN_ALIS_TOKEN_ADDRESS'])
        self.user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']
        self.eoa = self.__get_user_private_eth_address(self.user_id)

        self.tmp_csv_file = '/tmp/tmp_csv_file.csv'
        f = open(self.tmp_csv_file, 'a')
        self.writer = csv.writer(f)

        self.getTransferHistory(self.address, self.eoa)
        self.getMintHistory(self.address, self.eoa)

        f.close()
        # If file is empty, then error will be raised
        if sum(1 for i in open(self.tmp_csv_file, 'r')) == 0:
            raise RecordNotFoundError('Record Not Found')

        announce_url = self.extract_file_to_s3()

        notification_id = self.__notification(self.user_id, announce_url)
        os.remove(self.tmp_csv_file)

        return {
            'statusCode': 200
        }

    def padLeft(self, eoa):
        return '0x000000000000000000000000' + eoa[2:]

    def removeLeft(self, eoa):
        return '0x' + eoa[26:]

    def add_type(self, from_eoa, to_eoa):
        alis_bridge_contract_address = os.environ['PRIVATE_CHAIN_BRIDGE_ADDRESS']

        if from_eoa == self.eoa and to_eoa == alis_bridge_contract_address:
            return 'withdraw'
        elif from_eoa == self.eoa and to_eoa != '0x0000000000000000000000000000000000000000':
            return 'give'
        elif from_eoa == self.eoa and to_eoa == '0x0000000000000000000000000000000000000000':
            return 'burn'
        elif from_eoa == alis_bridge_contract_address and to_eoa == self.eoa:
            return 'deposit'
        elif from_eoa == '---' and to_eoa == self.eoa:
            return 'get by like'
        elif from_eoa != alis_bridge_contract_address and to_eoa == self.eoa:
            return 'get from an user'
        else:
            return 'unknown'

    def filter_transfer_data(self, transfer_result):
        for i in range(len(transfer_result)):
            self.writer.writerow([
                datetime.fromtimestamp(self.web3.eth.getBlock(transfer_result[i]['blockNumber'])['timestamp']),
                transfer_result[i]['transactionHash'].hex(),
                self.add_type(self.removeLeft(transfer_result[i]['topics'][1].hex()),self.removeLeft(transfer_result[i]['topics'][2].hex())),
                self.web3.fromWei(int(transfer_result[i]['data'], 16), 'ether')
            ])

    def getTransferHistory(self, address, eoa):
        fromfilter = self.web3.eth.filter({
            "address": address,
            "fromBlock": 1,
            "toBlock": 'latest',
            "topics": [self.web3.sha3(text="Transfer(address,address,uint256)").hex(),
                        self.padLeft(eoa)
            ],
            })

        tofilter = self.web3.eth.filter({
            "address": address,
            "fromBlock": 1,
            "toBlock": 'latest',
            "topics": [self.web3.sha3(text="Transfer(address,address,uint256)").hex(),
                        None,
                        self.padLeft(eoa)
            ],
        })

        transfer_result_from = fromfilter.get_all_entries()
        self.filter_transfer_data(transfer_result_from)
        transfer_result_to = tofilter.get_all_entries()
        self.filter_transfer_data(transfer_result_to)

    def filter_mint_data(self, mint_result):
        for i in range(len(mint_result)):
            self.writer.writerow([
                datetime.fromtimestamp(self.web3.eth.getBlock(mint_result[i]['blockNumber'])['timestamp']),
                mint_result[i]['transactionHash'].hex(),
                self.add_type('---', self.removeLeft(mint_result[i]['topics'][1].hex())),
                self.web3.fromWei(int(mint_result[i]['data'], 16), 'ether')
            ])

    def getMintHistory(self, address, eoa):
        to_filter = self.web3.eth.filter({
            "address": address,
            "fromBlock": 1,
            "toBlock": 'latest',
            "topics": [self.web3.sha3(text="Mint(address,uint256)").hex(),
                        self.padLeft(eoa)
            ],
        })

        mint_result = to_filter.get_all_entries()
        self.filter_mint_data(mint_result)

    def extract_file_to_s3(self):
        bucket = os.environ['ALL_TOKEN_HISTORY_CSV_DOWNLOAD_S3_BUCKET']
        JST = timezone(timedelta(hours=+9), 'JST')
        ### identityIdの項目はeventの中に存在するが、IAM認証でないと取得できないためlambda側でidtokenを使い取得する実装をした
        identityId = self.__get_user_cognito_identity_id()
        key = 'private/'+ identityId + '/' + self.user_id + '_' + datetime.now(JST).strftime('%Y-%m-%d-%H-%M-%S') + '.csv'
        with open(self.tmp_csv_file, 'rb') as f:
            csv_file = f.read()
            res = self.upload_file(bucket, key, csv_file)

        announce_url = 'https://'+bucket+'.s3-ap-northeast-1.amazonaws.com/'+key
        return announce_url

    def upload_file(self, bucket, key, bytes):
        s3Obj = self.s3.Object(bucket, key)
        res = s3Obj.put(Body = bytes)
        return res

    def __get_user_private_eth_address(self, user_id):
        # user_id に紐づく private_eth_address を取得
        user_info = UserUtil.get_cognito_user_info(self.cognito, user_id)
        private_eth_address = [a for a in user_info['UserAttributes'] if a.get('Name') == 'custom:private_eth_address']
        # private_eth_address が存在しないケースは想定していないため、取得出来ない場合は例外とする
        if len(private_eth_address) != 1:
            raise RecordNotFoundError('Record Not Found: private_eth_address')

        return private_eth_address[0]['Value']

    def __update_unread_notification_manager(self, user_id):
        unread_notification_manager_table = self.dynamodb.Table(os.environ['UNREAD_NOTIFICATION_MANAGER_TABLE_NAME'])

        unread_notification_manager_table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='set unread = :unread',
            ExpressionAttributeValues={':unread': True}
        )

    def __notification(self, user_id, announce_url):
        notification_table = self.dynamodb.Table(os.environ['NOTIFICATION_TABLE_NAME'])

        notification_id = self.__get_randomhash()

        notification_table.put_item(Item={
            'notification_id': notification_id,
            'user_id': user_id,
            'sort_key': TimeUtil.generate_sort_key(),
            'type': settings.CSVDOWNLOAD_NOTIFICATION_TYPE,
            'created_at': int(time.time()),
            'announce_body': '全トークン履歴のcsvのダウンロード準備が完了しました。本通知をクリックしてダウンロードしてください。',
            'announce_url': announce_url
        })

        self.__update_unread_notification_manager(user_id)

        return notification_id

    def __get_randomhash(self):
        return hashlib.sha256((str(time.time()) + str(os.urandom(16))).encode('utf-8')).hexdigest()

    def __get_user_cognito_identity_id(self):
        id_token = self.event['headers']['Authorization']
        identity_pool_id = os.environ['COGNITO_IDENTITY_POOL_ID']
        region = 'ap-northeast-1'
        cognito_user_pool_id = os.environ['COGNITO_USER_POOL_ID']

        logins = {'cognito-idp.' + region + '.amazonaws.com/' + cognito_user_pool_id : id_token}
        client = boto3.client('cognito-identity', region_name=region)
        cognito_identity_id = client.get_id(
            IdentityPoolId=identity_pool_id,
            Logins=logins
        )

        return cognito_identity_id['IdentityId']
